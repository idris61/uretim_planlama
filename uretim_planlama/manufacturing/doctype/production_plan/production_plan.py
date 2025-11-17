import frappe
from frappe.model.workflow import apply_workflow

# ozerpanjobcard app'i varsa onun class'ını, yoksa ERPNext'in class'ını kullan
try:
    from ozerpanjobcard.manufacturing.doctype.production_plan.production_plan import CustomProductionPlan as BaseProductionPlan
except ImportError:
    from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan as BaseProductionPlan


class CustomProductionPlan(BaseProductionPlan):
    """
    Production Plan'ın status değişikliklerini workflow_state ile senkronize eder.
    Hook kullanmadan, class override ile çalışır.
    """
    
    def set_status(self, close=None, update_bin=False):
        """
        set_status() metodunu override edip, status değişikliklerini 
        workflow_state ile senkronize ediyoruz.
        """
        # Önce orijinal metodu çalıştır
        super().set_status(close=close, update_bin=update_bin)
        
        # Eğer workflow yoksa veya submitted değilse çık
        if self.docstatus != 1:
            return
        
        # Status'a göre workflow_state'yi güncelle
        try:
            current_workflow_state = self.workflow_state or ""
            
            # Status "In Process" olduğunda ve workflow_state "Üretime Hazır" ise
            # "Devam Ediyor" durumuna geç
            if self.status == "In Process" and current_workflow_state == "Üretime Hazır":
                # Bağlı Job Card'lardan biri "Work In Progress" mi kontrol et
                work_orders = frappe.get_all(
                    "Work Order",
                    filters={"production_plan": self.name},
                    pluck="name"
                )
                
                if work_orders:
                    has_work_in_progress = frappe.db.exists(
                        "Job Card",
                        {
                            "work_order": ["in", work_orders],
                            "status": "Work In Progress",
                            "docstatus": ["<", 2]
                        }
                    )
                    
                    if has_work_in_progress:
                        try:
                            apply_workflow(self, "Üretimi Başlat")
                            frappe.logger().info(
                                f"Production Plan {self.name} workflow_state 'Devam Ediyor' olarak güncellendi "
                                f"(status: In Process, Job Card çalışıyor)"
                            )
                        except Exception as e:
                            # Workflow action bulunamazsa sessiz geç
                            frappe.log_error(
                                title=f"Production Plan Workflow Update ({self.name})",
                                message=str(e)
                            )
            
            # Status "Completed" olduğunda ve workflow_state "Devam Ediyor" ise
            # "Tamamlandı" durumuna geç
            elif self.status == "Completed" and current_workflow_state == "Devam Ediyor":
                try:
                    apply_workflow(self, "Üretimi Bitir")
                    frappe.logger().info(
                        f"Production Plan {self.name} workflow_state 'Tamamlandı' olarak güncellendi "
                        f"(status: Completed)"
                    )
                except Exception as e:
                    # Workflow action bulunamazsa sessiz geç
                    frappe.log_error(
                        title=f"Production Plan Workflow Update ({self.name})",
                        message=str(e)
                    )
                    
        except Exception as e:
            # Hata durumunda orijinal fonksiyon çalışmaya devam etsin
            frappe.log_error(
                title=f"Production Plan set_status Override Error ({self.name})",
                message=str(e)
            )

