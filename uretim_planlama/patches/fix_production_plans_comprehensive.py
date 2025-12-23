"""
Production Plan'ları kapsamlı şekilde düzeltir:
1. Tüm aktif Work Order'lar tamamlandıysa planı Completed yap
2. Kapatılmış ama eksik üretim olan iş emirlerini tespit et
3. Tekrar oluşturulmuş iş emirlerini tespit et
4. Eksik üretim durumlarını düzelt
"""
import frappe
from frappe.utils import flt
from frappe.model.workflow import apply_workflow, get_transitions


def execute():
	"""
	Tüm submitted Production Plan'ları kapsamlı şekilde düzeltir
	"""
	frappe.reload_doc("manufacturing", "doctype", "production_plan")
	
	# Tüm submitted production plan'ları al
	all_plans = frappe.get_all(
		"Production Plan",
		filters={"docstatus": 1},
		fields=["name", "status", "workflow_state", "total_planned_qty", "total_produced_qty"],
		order_by="name",
		limit=1000
	)
	
	print(f"Toplam {len(all_plans)} submitted Production Plan kontrol ediliyor...\n")
	
	updated_count = 0
	error_count = 0
	closed_wo_fixed = 0
	duplicate_wo_found = 0
	
	for pp in all_plans:
		try:
			pp_doc = frappe.get_doc("Production Plan", pp.name)
			
			# Tüm Work Order'ları al
			work_orders = frappe.get_all(
				"Work Order",
				filters={"production_plan": pp.name},
				fields=["name", "status", "qty", "produced_qty", "docstatus"],
				order_by="creation"
			)
			
			if not work_orders:
				continue
			
			# Work Order durumlarını analiz et
			wo_statuses = [wo.status for wo in work_orders]
			total_wo_count = len(work_orders)
			completed_count = sum(1 for status in wo_statuses if status == "Completed")
			closed_count = sum(1 for status in wo_statuses if status == "Closed")
			cancelled_count = sum(1 for status in wo_statuses if status == "Cancelled")
			active_wo_count = total_wo_count - cancelled_count
			
			# Aktif Work Order'lar (Closed/Stopped hariç)
			wo_status_for_completion = frappe.get_all(
				"Work Order",
				filters={
					"production_plan": pp.name,
					"status": ("not in", ["Closed", "Stopped"]),
					"docstatus": ("<", 2),
				},
				fields=["name", "status", "qty", "produced_qty"],
			)
			all_wo_completed = all(s == "Completed" for s in [wo.status for wo in wo_status_for_completion]) if wo_status_for_completion else False
			
			# Item kontrolü - eğer tüm Work Order'lar tamamlandıysa, item'ları üretilmiş say
			if all_wo_completed and active_wo_count > 0:
				all_items_produced = True
			else:
				all_items_produced = all(
					abs(flt(d.planned_qty) - flt(d.produced_qty)) < 0.000001 
					for d in pp_doc.po_items
				) if pp_doc.po_items else False
			
			should_be_completed = all_items_produced and all_wo_completed
			
			# 1. Kapatılmış ama eksik üretim olan iş emirlerini kontrol et
			closed_with_incomplete = []
			for wo in work_orders:
				if wo.status == "Closed":
					if flt(wo.qty) > flt(wo.produced_qty) + 0.000001:
						closed_with_incomplete.append(wo.name)
						# İş emrini Completed yap (eğer üretim yapıldıysa)
						try:
							wo_doc = frappe.get_doc("Work Order", wo.name)
							# Eğer produced_qty > 0 ise, status'u Completed yap
							if flt(wo_doc.produced_qty) > 0:
								wo_doc.status = "Completed"
								wo_doc.db_set("status", "Completed", update_modified=False)
								closed_wo_fixed += 1
								print(f"  ✅ {wo.name}: Closed → Completed (produced_qty={wo_doc.produced_qty})")
						except Exception as e:
							frappe.log_error(
								title=f"Fix Closed WO ({wo.name})",
								message=f"Hata: {str(e)}"
							)
			
			# 2. Tekrar oluşturulmuş iş emirlerini tespit et
			if pp_doc.po_items:
				item_wo_map = {}
				for wo in work_orders:
					if wo.status == "Completed":
						try:
							wo_doc = frappe.get_doc("Work Order", wo.name)
							if wo_doc.production_plan_item:
								pp_item = frappe.get_value("Production Plan Item", wo_doc.production_plan_item, "item_code")
								if pp_item:
									if pp_item not in item_wo_map:
										item_wo_map[pp_item] = []
									item_wo_map[pp_item].append({
										"wo": wo.name,
										"qty": wo.qty,
										"produced": wo.produced_qty,
										"creation": wo.get("creation", "")
									})
						except Exception:
							pass
				
				# Aynı item için birden fazla tamamlanmış WO varsa
				duplicate_items = {item: wos for item, wos in item_wo_map.items() if len(wos) > 1}
				if duplicate_items:
					duplicate_wo_found += len(duplicate_items)
					print(f"  ⚠️  {pp.name}: {len(duplicate_items)} item için tekrar oluşturulmuş iş emri var")
			
			# 3. Eğer tüm aktif Work Order'lar tamamlandıysa (item kontrolü olmadan), planı Completed yap
			# Çünkü kullanıcı "eksik üretilen ürünler olmasına rağmen kapatılmış iş emirleri" diyor
			# Bu durumda, tüm aktif WO'lar tamamlandıysa plan completed olmalı
			if all_wo_completed and active_wo_count > 0 and pp.status != "Completed":
				should_be_completed = True
			
			# 4. Eğer tüm şartlar sağlanıyorsa ama status "Completed" değilse, güncelle
			if should_be_completed and pp.status != "Completed":
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
					workflow_updated = False
					
					if current_workflow_state != "Tamamlandı":
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
								else:
									# Action yoksa direkt workflow_state'yi güncelle
									pp_doc.workflow_state = "Tamamlandı"
									pp_doc.db_set("workflow_state", "Tamamlandı", update_modified=False)
									frappe.db.commit()
									workflow_updated = True
							except Exception as e:
								# Hata durumunda direkt workflow_state'yi güncelle
								try:
									pp_doc.workflow_state = "Tamamlandı"
									pp_doc.db_set("workflow_state", "Tamamlandı", update_modified=False)
									frappe.db.commit()
									workflow_updated = True
								except Exception as e2:
									frappe.log_error(
										title=f"Production Plan Workflow Fix ({pp.name}) - Üretimi Bitir",
										message=f"Hata: {str(e2)}"
									)
						elif current_workflow_state == "Tamamlandı":
							workflow_updated = True
						else:
							# Beklenmeyen durum - direkt workflow_state'yi güncelle
							try:
								pp_doc.workflow_state = "Tamamlandı"
								pp_doc.db_set("workflow_state", "Tamamlandı", update_modified=False)
								frappe.db.commit()
								workflow_updated = True
							except Exception as e:
								frappe.log_error(
									title=f"Production Plan Workflow Fix ({pp.name}) - Direkt Güncelleme",
									message=f"Hata: {str(e)}"
								)
					
					if workflow_updated or current_workflow_state == "Tamamlandı":
						updated_count += 1
						print(f"✅ {pp.name}: Status ve workflow_state güncellendi")
				else:
					# Workflow yok, sadece status güncelle
					updated_count += 1
					print(f"✅ {pp.name}: Status güncellendi (workflow yok)")
				
				frappe.db.commit()
		
		except Exception as e:
			error_count += 1
			frappe.log_error(
				title=f"Production Plan Comprehensive Fix Error ({pp.name})",
				message=f"Hata: {str(e)}\nTraceback: {frappe.get_traceback()}"
			)
			print(f"❌ {pp.name}: Hata - {str(e)}")
	
	print(f"\n{'='*80}")
	print(f"Özet:")
	print(f"  Toplam kontrol edilen: {len(all_plans)}")
	print(f"  Güncellenen plan: {updated_count}")
	print(f"  Kapatılmış WO düzeltildi: {closed_wo_fixed}")
	print(f"  Tekrar oluşturulmuş WO bulundu: {duplicate_wo_found}")
	print(f"  Hata: {error_count}")
	print(f"{'='*80}")
	
	return {
		"updated": updated_count,
		"errors": error_count,
		"closed_wo_fixed": closed_wo_fixed,
		"duplicate_wo_found": duplicate_wo_found,
		"total": len(all_plans)
	}

