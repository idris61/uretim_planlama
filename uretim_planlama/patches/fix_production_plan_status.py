"""
Production Plan'ların status ve workflow_state'lerini düzeltir
Tüm Work Order'lar ve Material Request'ler tamamlandığında status'u "Completed" yapar
"""
import frappe
from frappe.utils import flt
from frappe.model.workflow import apply_workflow, get_transitions


def execute():
	"""
	Tüm submitted Production Plan'ları kontrol edip status ve workflow_state'lerini düzeltir
	"""
	frappe.reload_doc("manufacturing", "doctype", "production_plan")
	
	# Tüm submitted production plan'ları al
	all_plans = frappe.get_all(
		"Production Plan",
		filters={"docstatus": 1},
		fields=["name", "status", "workflow_state", "total_planned_qty", "total_produced_qty"],
		limit=1000
	)
	
	print(f"Toplam {len(all_plans)} submitted Production Plan kontrol ediliyor...")
	
	updated_count = 0
	error_count = 0
	problematic_plans = []
	
	for pp in all_plans:
		try:
			pp_doc = frappe.get_doc("Production Plan", pp.name)
			
			# Work Order'ları kontrol et
			work_orders = frappe.get_all(
				"Work Order",
				filters={"production_plan": pp.name, "docstatus": ["<", 2]},
				fields=["name", "status", "qty", "produced_qty"]
			)
			
			if not work_orders:
				continue
			
			# Work Order durumlarını analiz et
			wo_statuses = [wo.status for wo in work_orders]
			total_wo_count = len(work_orders)
			completed_count = sum(1 for status in wo_statuses if status == "Completed")
			cancelled_count = sum(1 for status in wo_statuses if status == "Cancelled")
			active_wo_count = total_wo_count - cancelled_count
			
			# 2. Tüm aktif Work Order'lar tamamlandı mı? (Closed/Stopped hariç)
			wo_status_for_completion = frappe.get_all(
				"Work Order",
				filters={
					"production_plan": pp.name,
					"status": ("not in", ["Closed", "Stopped"]),
					"docstatus": ("<", 2),
				},
				fields="status",
				pluck="status",
			)
			all_wo_completed = all(s == "Completed" for s in wo_status_for_completion) if wo_status_for_completion else False
			
			# all_items_completed() mantığını kontrol et
			# 1. Tüm item'lar üretilmiş mi?
			# Eğer tüm Work Order'lar tamamlandıysa, item'ları da üretilmiş say
			# (Work Order'lar tamamlandıysa, üretim yapılmış demektir)
			if all_wo_completed and active_wo_count > 0:
				# Tüm Work Order'lar tamamlandıysa, item'ları üretilmiş say
				all_items_produced = True
			else:
				# Normal kontrol - plan item'larındaki produced_qty'yi kontrol et
				all_items_produced = all(
					abs(flt(d.planned_qty) - flt(d.produced_qty)) < 0.000001 
					for d in pp_doc.po_items
				) if pp_doc.po_items else False
			
			# Material Request'leri kontrol et (opsiyonel - eğer varsa tamamlanmış olmalı)
			mr_items = frappe.get_all(
				"Production Plan Material Request",
				filters={"parent": pp.name},
				fields=["material_request"]
			)
			
			all_mr_completed = True
			if mr_items:
				for mr_item in mr_items:
					if mr_item.material_request:
						try:
							mr_doc = frappe.get_doc("Material Request", mr_item.material_request)
							# Material Request tamamlanmış veya iptal edilmiş olmalı
							if mr_doc.status not in ["Completed", "Cancelled", "Stopped"]:
								all_mr_completed = False
								break
						except frappe.DoesNotExistError:
							# Material Request silinmişse, tamamlanmış say
							pass
			
			# Durum kontrolü: Eğer tüm şartlar sağlanıyorsa "Completed" olmalı
			# Material Request kontrolü opsiyonel - sadece Work Order ve item kontrolü yeterli
			should_be_completed = all_items_produced and all_wo_completed
			
			if should_be_completed and pp.status != "Completed":
				problematic_plans.append({
					"name": pp.name,
					"current_status": pp.status,
					"workflow_state": pp.workflow_state,
					"all_items_produced": all_items_produced,
					"all_wo_completed": all_wo_completed,
					"all_mr_completed": all_mr_completed,
					"wo_statuses": wo_status_for_completion
				})
				
				# Status'u "Completed" yap
				pp_doc.status = "Completed"
				pp_doc.db_set("status", "Completed", update_modified=False)
				
				# Workflow state'i güncelle
				current_workflow_state = pp_doc.workflow_state or ""
				
				# Workflow aktif mi kontrol et
				active_workflow = frappe.get_all(
					"Workflow",
					filters={"document_type": "Production Plan", "is_active": 1},
					fields=["name"],
					limit=1
				)
				
				if active_workflow and active_workflow[0].name == "Production Plan – Gerçek Durum":
					# Workflow state'i "Tamamlandı" yap
					if current_workflow_state != "Tamamlandı":
						workflow_updated = False
						
						# Önce "Devam Ediyor" durumuna geç (eğer değilse)
						if current_workflow_state == "Üretime Hazır":
							try:
								pp_doc.reload()
								available_actions = [t.action for t in get_transitions(pp_doc)]
								if "Üretimi Başlat" in available_actions:
									apply_workflow(pp_doc, "Üretimi Başlat")
									frappe.db.commit()
									pp_doc.reload()
									current_workflow_state = pp_doc.workflow_state or ""
									frappe.db.commit()
							except Exception as e:
								frappe.log_error(
									title=f"Production Plan Workflow Fix ({pp.name}) - Üretimi Başlat",
									message=f"Hata: {str(e)}"
								)
						
						# Sonra "Tamamlandı" durumuna geç
						pp_doc.reload()
						current_workflow_state = pp_doc.workflow_state or ""
						
						if current_workflow_state == "Devam Ediyor":
							try:
								available_actions = [t.action for t in get_transitions(pp_doc)]
								if "Üretimi Bitir" in available_actions:
									apply_workflow(pp_doc, "Üretimi Bitir")
									frappe.db.commit()
									workflow_updated = True
									print(f"✅ {pp.name}: Status ve workflow_state güncellendi (workflow action)")
								else:
									# Action yoksa direkt workflow_state'yi güncelle
									pp_doc.workflow_state = "Tamamlandı"
									pp_doc.db_set("workflow_state", "Tamamlandı", update_modified=False)
									frappe.db.commit()
									workflow_updated = True
									print(f"✅ {pp.name}: Status ve workflow_state (direkt) güncellendi")
							except Exception as e:
								# Hata durumunda direkt workflow_state'yi güncelle
								try:
									pp_doc.workflow_state = "Tamamlandı"
									pp_doc.db_set("workflow_state", "Tamamlandı", update_modified=False)
									frappe.db.commit()
									workflow_updated = True
									print(f"✅ {pp.name}: Status ve workflow_state (fallback) güncellendi")
								except Exception as e2:
									frappe.log_error(
										title=f"Production Plan Workflow Fix ({pp.name}) - Üretimi Bitir",
										message=f"Hata: {str(e2)}"
									)
									error_count += 1
						elif current_workflow_state == "Tamamlandı":
							# Zaten tamamlandı
							workflow_updated = True
							print(f"✅ {pp.name}: Status güncellendi (workflow_state zaten Tamamlandı)")
						else:
							# Beklenmeyen durum - direkt workflow_state'yi güncelle
							try:
								pp_doc.workflow_state = "Tamamlandı"
								pp_doc.db_set("workflow_state", "Tamamlandı", update_modified=False)
								frappe.db.commit()
								workflow_updated = True
								print(f"✅ {pp.name}: Status ve workflow_state (beklenmeyen durum) güncellendi")
							except Exception as e:
								frappe.log_error(
									title=f"Production Plan Workflow Fix ({pp.name}) - Direkt Güncelleme",
									message=f"Hata: {str(e)}"
								)
								error_count += 1
						
						if workflow_updated:
							updated_count += 1
					else:
						# Workflow state zaten "Tamamlandı"
						updated_count += 1
						print(f"✅ {pp.name}: Status güncellendi (workflow_state zaten Tamamlandı)")
				else:
					# Workflow yok, sadece status güncelle
					updated_count += 1
					print(f"✅ {pp.name}: Status güncellendi (workflow yok)")
				
				frappe.db.commit()
		
		except Exception as e:
			error_count += 1
			frappe.log_error(
				title=f"Production Plan Status Fix Error ({pp.name})",
				message=f"Hata: {str(e)}\nTraceback: {frappe.get_traceback()}"
			)
			print(f"❌ {pp.name}: Hata - {str(e)}")
	
	print(f"\n{'='*80}")
	print(f"Özet:")
	print(f"  Toplam kontrol edilen: {len(all_plans)}")
	print(f"  Güncellenen: {updated_count}")
	print(f"  Hata: {error_count}")
	print(f"  Sorunlu plan sayısı: {len(problematic_plans)}")
	print(f"{'='*80}")
	
	if problematic_plans:
		print(f"\nSorunlu planlar:")
		for pp in problematic_plans:
			print(f"  - {pp['name']}: Status={pp['current_status']}, Workflow={pp['workflow_state']}")
			print(f"    WO statuses: {pp['wo_statuses']}")
	
	return {
		"updated": updated_count,
		"errors": error_count,
		"total": len(all_plans)
	}

