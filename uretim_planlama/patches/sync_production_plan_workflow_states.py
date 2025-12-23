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

	if not active_workflow:
		frappe.logger().error("Production Plan için aktif workflow bulunamadı")
		return

	workflow_name = active_workflow[0].name
	frappe.logger().info(f"Production Plan Workflow Sync başlatılıyor - Workflow: {workflow_name}")

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
	skipped_count = 0

	frappe.logger().info(f"Toplam {total_count} Production Plan kontrol ediliyor...")

	for pp in production_plans:
		try:
			pp_doc = frappe.get_doc("Production Plan", pp.name)
			current_workflow_state = pp_doc.workflow_state or ""
			current_status = pp_doc.status or ""

			# Bağlı Work Order'ları kontrol et
			work_orders = frappe.get_all(
				"Work Order",
				filters={"production_plan": pp.name, "docstatus": ["<", 2]},
				fields=["name", "status"],
			)

			if not work_orders:
				skipped_count += 1
				frappe.logger().debug(f"Production Plan {pp.name}: Work Order bulunamadı, atlanıyor")
				continue

			# Work Order durumlarını analiz et
			wo_statuses = [wo.status for wo in work_orders]
			total_wo_count = len(work_orders)
			completed_count = sum(1 for status in wo_statuses if status == "Completed")
			in_process_count = sum(1 for status in wo_statuses if status in ["In Process", "In Progress"])
			cancelled_count = sum(1 for status in wo_statuses if status == "Cancelled")
			active_wo_count = total_wo_count - cancelled_count

			# Durum 1: Tüm aktif Work Order'lar tamamlandı → "Tamamlandı"
			if active_wo_count > 0 and completed_count == active_wo_count:
				# Status kontrolünü esnek yap - Completed veya In Process olabilir
				if current_status in ["Completed", "In Process"]:
					if current_workflow_state != "Tamamlandı":
						# Önce "Devam Ediyor" durumuna geç (eğer değilse)
						if current_workflow_state == "Üretime Hazır":
							try:
								apply_workflow(pp_doc, "Üretimi Başlat")
								frappe.db.commit()
								pp_doc.reload()
								current_workflow_state = pp_doc.workflow_state or ""
								frappe.logger().info(
									f"Production Plan {pp.name}: 'Üretime Hazır' → 'Devam Ediyor' geçişi yapıldı"
								)
							except Exception as e:
								frappe.log_error(
									title=f"Production Plan Workflow Sync ({pp.name}) - Üretimi Başlat",
									message=f"Hata: {str(e)}\nTraceback: {frappe.get_traceback()}"
								)
								error_count += 1
								continue

						# Sonra "Tamamlandı" durumuna geç
						pp_doc.reload()
						if pp_doc.workflow_state == "Devam Ediyor":
							try:
								apply_workflow(pp_doc, "Üretimi Bitir")
								frappe.db.commit()
								updated_count += 1
								frappe.logger().info(
									f"Production Plan {pp.name}: workflow_state 'Tamamlandı' olarak güncellendi "
									f"(Tüm {active_wo_count} aktif Work Order tamamlandı)"
								)
							except Exception as e:
								frappe.log_error(
									title=f"Production Plan Workflow Sync ({pp.name}) - Üretimi Bitir",
									message=f"Hata: {str(e)}\nTraceback: {frappe.get_traceback()}"
								)
								error_count += 1
						elif pp_doc.workflow_state == "Tamamlandı":
							# Zaten tamamlandı
							updated_count += 1

			# Durum 2: En az bir Work Order "In Process" veya bazıları tamamlandı ama hepsi değil → "Devam Ediyor"
			elif (in_process_count > 0 or (completed_count > 0 and completed_count < active_wo_count)):
				# Status kontrolünü esnek yap
				if current_status in ["In Process", "Completed", "Not Started"]:
					if current_workflow_state == "Üretime Hazır":
						try:
							apply_workflow(pp_doc, "Üretimi Başlat")
							frappe.db.commit()
							updated_count += 1
							frappe.logger().info(
								f"Production Plan {pp.name}: workflow_state 'Devam Ediyor' olarak güncellendi "
								f"(Work Order durumu: {in_process_count} devam ediyor, {completed_count}/{active_wo_count} tamamlandı)"
							)
						except Exception as e:
							frappe.log_error(
								title=f"Production Plan Workflow Sync ({pp.name}) - Üretimi Başlat",
								message=f"Hata: {str(e)}\nTraceback: {frappe.get_traceback()}"
							)
							error_count += 1

		except Exception as e:
			error_count += 1
			frappe.log_error(
				title=f"Production Plan Workflow Sync Error ({pp.name})",
				message=f"Hata: {str(e)}\nTraceback: {frappe.get_traceback()}"
			)

	frappe.logger().info(
		f"Production Plan Workflow Sync tamamlandı: "
		f"{updated_count} güncellendi, {skipped_count} atlandı, {error_count} hata"
	)

	frappe.db.commit()
