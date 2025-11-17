"""
Work Order durumu değiştiğinde Production Plan'ın set_status metodunu tetikler
Böylece workflow_state otomatik güncellenir
"""
import frappe


def on_update_after_submit(doc, method=None):
	"""
	Work Order durumu değiştiğinde (status, produced_qty vb.)
	Production Plan'ın set_status metodunu çağırarak workflow_state'yi günceller
	"""
	if not doc.production_plan:
		return
	
	try:
		# Production Plan'ı yükle
		production_plan = frappe.get_doc("Production Plan", doc.production_plan)
		
		# Sadece submitted Production Plan'lar için işlem yap
		if production_plan.docstatus != 1:
			return
		
		# set_status metodunu çağır (update_bin=False, close=None)
		# Bu metod override edilmiş CustomProductionPlan.set_status() metodunu çağıracak
		# ve Work Order durumlarını kontrol ederek workflow_state'yi güncelleyecek
		production_plan.set_status(close=None, update_bin=False)
		production_plan.save(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		# Hata durumunda log kaydet ama işlemi durdurma
		frappe.log_error(
			title=f"Work Order Production Plan Status Update Error ({doc.name})",
			message=str(e)
		)

