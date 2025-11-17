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
	
	# after_commit kullanarak asenkron hale getir
	# Böylece Job Card submit işlemi tamamlandıktan sonra çalışır
	production_plan_name = doc.production_plan  # Closure için değeri sakla
	
	def update_production_plan():
		try:
			# Production Plan'ı yükle
			production_plan = frappe.get_doc("Production Plan", production_plan_name)
			
			# Sadece submitted Production Plan'lar için işlem yap
			if production_plan.docstatus != 1:
				return
			
			# set_status metodunu çağır (update_bin=False, close=None)
			# Bu metod override edilmiş CustomProductionPlan.set_status() metodunu çağıracak
			# ve Work Order durumlarını kontrol ederek workflow_state'yi güncelleyecek
			production_plan.set_status(close=None, update_bin=False)
			
		except Exception as e:
			# Hata durumunda log kaydet ama işlemi durdurma
			frappe.log_error(
				title=f"Work Order Production Plan Status Update Error ({doc.name})",
				message=str(e)
			)
	
	# after_commit ile asenkron çalıştır
	frappe.db.after_commit.add(update_production_plan)

