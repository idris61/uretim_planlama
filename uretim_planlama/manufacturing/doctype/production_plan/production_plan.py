import frappe
from frappe.model.workflow import apply_workflow, get_transitions

# ozerpanjobcard app'i varsa onun class'ını, yoksa ERPNext'in class'ını kullan
try:
    from ozerpanjobcard.manufacturing.doctype.production_plan.production_plan import CustomProductionPlan as BaseProductionPlan
except ImportError:
    from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan as BaseProductionPlan


class CustomProductionPlan(BaseProductionPlan):
    """
    Production Plan'ın status değişikliklerini workflow_state ile senkronize eder.
    Work Order durumlarını kontrol ederek otomatik workflow geçişleri yapar.
    """
    
    def set_status(self, close=None, update_bin=False):
        """
        set_status() metodunu override edip, status değişikliklerini 
        workflow_state ile senkronize ediyoruz.
        Work Order durumlarını kontrol ederek otomatik geçişler yapıyoruz.
        """
        # Önce orijinal metodu çalıştır
        super().set_status(close=close, update_bin=update_bin)
        
        # Eğer workflow yoksa veya submitted değilse çık
        if self.docstatus != 1:
            return
        
        # Workflow aktif mi kontrol et
        active_workflow = frappe.get_all(
            "Workflow",
            filters={"document_type": "Production Plan", "is_active": 1},
            fields=["name"],
            limit=1
        )
        if not active_workflow or active_workflow[0].name != "Production Plan – Gerçek Durum":
            return
        
        # Status'a göre workflow_state'yi güncelle
        try:
            current_workflow_state = self.workflow_state or ""
            
            # Bağlı Work Order'ları kontrol et
            work_orders = frappe.get_all(
                "Work Order",
                filters={"production_plan": self.name, "docstatus": ["<", 2]},
                fields=["name", "status", "qty", "produced_qty"],
            )
            
            if not work_orders:
                # Work Order yoksa işlem yapma
                return
            
            # Work Order durumlarını analiz et (birden fazla work order olabilir)
            wo_statuses = [wo.status for wo in work_orders]
            total_wo_count = len(work_orders)
            completed_count = sum(1 for status in wo_statuses if status == "Completed")
            in_process_count = sum(1 for status in wo_statuses if status in ["In Process", "In Progress"])
            cancelled_count = sum(1 for status in wo_statuses if status == "Cancelled")
            active_wo_count = total_wo_count - cancelled_count  # İptal edilenler hariç
            
            # Mevcut durum için geçerli action'ları kontrol et
            # Eğer workflow_state yoksa veya geçersizse, işlem yapma
            if not current_workflow_state:
                return
            
            try:
                available_actions = [t.action for t in get_transitions(self)]
            except Exception:
                # get_transitions hata verirse (örneğin workflow_state geçersizse) işlem yapma
                return
            
            # Durum 1: TÜM aktif Work Order'lar tamamlandı → "Tamamlandı"
            # (İptal edilen work order'lar sayılmaz)
            if active_wo_count > 0 and completed_count == active_wo_count and self.status == "Completed":
                if current_workflow_state not in ["Tamamlandı"]:
                    # Önce "Devam Ediyor" durumuna geç (eğer değilse)
                    if current_workflow_state == "Üretime Hazır":
                        if "Üretimi Başlat" in available_actions:
                            try:
                                apply_workflow(self, "Üretimi Başlat")
                                frappe.db.commit()
                                # Doc'u yeniden yükle
                                self.reload()
                                # workflow_state'yi veritabanından kontrol et
                                updated_state = frappe.db.get_value("Production Plan", self.name, "workflow_state")
                                if updated_state != "Devam Ediyor":
                                    return  # Geçiş başarısız oldu
                                # Available actions'ı güncelle
                                try:
                                    available_actions = [t.action for t in get_transitions(self)]
                                except Exception:
                                    return
                            except Exception as e:
                                frappe.log_error(
                                    title=f"Production Plan Workflow Update ({self.name}) - Üretimi Başlat",
                                    message=f"Hata: {str(e)}, Mevcut durum: {current_workflow_state}, Mevcut action'lar: {available_actions}"
                                )
                                return  # Hata varsa devam etme
                        else:
                            # Action mevcut değil, işlem yapma
                            return
                    
                    # Sonra "Tamamlandı" durumuna geç
                    # workflow_state'yi veritabanından kontrol et
                    current_state = frappe.db.get_value("Production Plan", self.name, "workflow_state")
                    if current_state == "Devam Ediyor":
                        # Doc'u yeniden yükle
                        self.reload()
                        # Available actions'ı tekrar kontrol et
                        try:
                            available_actions = [t.action for t in get_transitions(self)]
                        except Exception:
                            return
                        
                        if "Üretimi Bitir" in available_actions:
                            try:
                                apply_workflow(self, "Üretimi Bitir")
                                frappe.db.commit()
                                frappe.logger().info(
                                    f"Production Plan {self.name} workflow_state 'Tamamlandı' olarak güncellendi "
                                    f"(Tüm {active_wo_count} aktif Work Order tamamlandı)"
                                )
                            except Exception as e:
                                frappe.log_error(
                                    title=f"Production Plan Workflow Update ({self.name}) - Üretimi Bitir",
                                    message=f"Hata: {str(e)}, Mevcut durum: {current_state}, Mevcut action'lar: {available_actions}"
                                )
                        else:
                            # Action mevcut değil, log kaydet
                            frappe.log_error(
                                title=f"Production Plan Workflow Update ({self.name}) - Üretimi Bitir Action Bulunamadı",
                                message=f"Mevcut durum: {current_state}, Mevcut action'lar: {available_actions}"
                            )
            
            # Durum 2: En az bir Work Order "In Process" veya bazıları tamamlandı ama hepsi değil → "Devam Ediyor"
            # (Bazı work order'lar tamamlandı, bazıları devam ediyor veya henüz başlamadı)
            elif (in_process_count > 0 or (completed_count > 0 and completed_count < active_wo_count)) and self.status == "In Process":
                if current_workflow_state == "Üretime Hazır":
                    if "Üretimi Başlat" in available_actions:
                        try:
                            apply_workflow(self, "Üretimi Başlat")
                            frappe.db.commit()
                            frappe.logger().info(
                                f"Production Plan {self.name} workflow_state 'Devam Ediyor' olarak güncellendi "
                                f"(Work Order durumu: {in_process_count} devam ediyor, {completed_count}/{active_wo_count} tamamlandı)"
                            )
                        except Exception as e:
                            frappe.log_error(
                                title=f"Production Plan Workflow Update ({self.name}) - Üretimi Başlat",
                                message=f"Hata: {str(e)}, Mevcut durum: {current_workflow_state}, Mevcut action'lar: {available_actions}"
                            )
                    else:
                        # Action mevcut değil, log kaydet
                        frappe.log_error(
                            title=f"Production Plan Workflow Update ({self.name}) - Üretimi Başlat Action Bulunamadı",
                            message=f"Mevcut durum: {current_workflow_state}, Mevcut action'lar: {available_actions}"
                        )
                    
        except Exception as e:
            # Hata durumunda orijinal fonksiyon çalışmaya devam etsin
            frappe.log_error(
                title=f"Production Plan set_status Override Error ({self.name})",
                message=str(e)
            )

