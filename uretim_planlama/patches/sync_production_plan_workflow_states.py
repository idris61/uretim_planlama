"""
Geçmiş Production Plan'ların workflow_state'lerini Work Order durumlarına göre günceller
"""
import frappe
from frappe.model.workflow import apply_workflow


def execute():
	"""
	Tüm submitted Production Plan'ları kontrol edip workflow_state'lerini günceller
	"""
	frappe.reload_doc("manufacturing", "doctype", "production_plan")
	
	# Workflow aktif mi kontrol et
	active_workflow = frappe.get_all(
		"Workflow",
		filters={"document_type": "Production Plan", "is_active": 1},
		fields=["name"],
		limit=1
	)
	if not active_workflow or active_workflow[0].name != "Production Plan – Gerçek Durum":
		frappe.log_error(
			title="Production Plan Workflow Sync",
			message="Production Plan – Gerçek Durum workflow'u aktif değil"
		)
		return
	
	# Tüm submitted Production Plan'ları al
	production_plans = frappe.get_all(
		"Production Plan",
		filters={"docstatus": 1},
		fields=["name", "status", "workflow_state"],
		order_by="creation asc"
	)
	
	total_count = len(production_plans)
	updated_count = 0
	error_count = 0
	
	frappe.msgprint(f"Toplam {total_count} Production Plan kontrol ediliyor...")
	
	for pp in production_plans:
		try:
			pp_doc = frappe.get_doc("Production Plan", pp.name)
			current_workflow_state = pp_doc.workflow_state or ""
			
			# Bağlı Work Order'ları kontrol et
			work_orders = frappe.get_all(
				"Work Order",
				filters={"production_plan": pp.name, "docstatus": ["<", 2]},
				fields=["name", "status"],
			)
			
			if not work_orders:
				# Work Order yoksa atla
				continue
			
			# Work Order durumlarını analiz et
			wo_statuses = [wo.status for wo in work_orders]
			total_wo_count = len(work_orders)
			completed_count = sum(1 for status in wo_statuses if status == "Completed")
			in_process_count = sum(1 for status in wo_statuses if status in ["In Process", "In Progress"])
			cancelled_count = sum(1 for status in wo_statuses if status == "Cancelled")
			active_wo_count = total_wo_count - cancelled_count
			
			# Durum 1: Tüm aktif Work Order'lar tamamlandı → "Tamamlandı"
			if active_wo_count > 0 and completed_count == active_wo_count and pp_doc.status == "Completed":
				if current_workflow_state not in ["Tamamlandı"]:
					# Önce "Devam Ediyor" durumuna geç (eğer değilse)
					if current_workflow_state == "Üretime Hazır":
						try:
							apply_workflow(pp_doc, "Üretimi Başlat")
							frappe.db.commit()
							# Doc'u yeniden yükle
							pp_doc = frappe.get_doc("Production Plan", pp.name)
						except Exception as e:
							frappe.log_error(
								title=f"Production Plan Workflow Sync ({pp.name}) - Üretimi Başlat",
								message=str(e)
						 )
							continue  # Hata varsa bir sonraki plana geç
					
					# Sonra "Tamamlandı" durumuna geç
					# Doc'u tekrar yükle çünkü workflow_state değişmiş olabilir
					pp_doc = frappe.get_doc("Production Plan", pp.name)
					if pp_doc.workflow_state == "Devam Ediyor":
						try:
							apply_workflow(pp_doc, "Üretimi Bitir")
							frappe.db.commit()
							updated_count += 1
							frappe.logger().info(
								f"Production Plan {pp.name} workflow_state 'Tamamlandı' olarak güncellendi "
								f"(Tüm {active_wo_count} aktif Work Order tamamlandı)"
							)
						except Exception as e:
							frappe.log_error(
								title=f"Production Plan Workflow Sync ({pp.name}) - Üretimi Bitir",
								message=str(e)
							)
					elif pp_doc.workflow_state == "Tamamlandı":
						# Zaten tamamlandı, işlem yapma
						updated_count += 1
			
			# Durum 2: En az bir Work Order "In Process" veya bazıları tamamlandı ama hepsi değil → "Devam Ediyor"
			elif (in_process_count > 0 or (completed_count > 0 and completed_count < active_wo_count)) and pp_doc.status == "In Process":
				if current_workflow_state == "Üretime Hazır":
					try:
						apply_workflow(pp_doc, "Üretimi Başlat")
						frappe.db.commit()
						updated_count += 1
						frappe.logger().info(
							f"Production Plan {pp.name} workflow_state 'Devam Ediyor' olarak güncellendi "
							f"(Work Order durumu: {in_process_count} devam ediyor, {completed_count}/{active_wo_count} tamamlandı)"
						)
					except Exception as e:
						frappe.log_error(
							title=f"Production Plan Workflow Sync ({pp.name}) - Üretimi Başlat",
							message=str(e)
						)
		
		except Exception as e:
			error_count += 1
			frappe.log_error(
				title=f"Production Plan Workflow Sync Error ({pp.name})",
				message=str(e)
			)
	
	frappe.msgprint(
		f"Güncelleme tamamlandı: {updated_count} Production Plan güncellendi, "
		f"{error_count} hata oluştu"
	)
	
	frappe.db.commit()

