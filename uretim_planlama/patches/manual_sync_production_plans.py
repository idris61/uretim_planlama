"""
Manuel olarak çalıştırılabilir Production Plan workflow_state sync script'i
Kullanım: bench --site ozerpan.com console
>>> exec(open('apps/uretim_planlama/uretim_planlama/patches/manual_sync_production_plans.py').read())
"""
import frappe
from frappe.model.workflow import apply_workflow

# Site bağlantısı kontrolü
if not frappe.db:
    frappe.init(site='ozerpan.com')
    frappe.connect()

# Workflow aktif mi kontrol et
active_workflow = frappe.get_all(
    "Workflow",
    filters={"document_type": "Production Plan", "is_active": 1},
    fields=["name"],
    limit=1
)
if not active_workflow or active_workflow[0].name != "Production Plan – Gerçek Durum":
    print("❌ Production Plan – Gerçek Durum workflow'u aktif değil")
    exit()

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

print(f"\n📊 Toplam {total_count} Production Plan kontrol ediliyor...\n")

for idx, pp in enumerate(production_plans, 1):
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
            skipped_count += 1
            continue
        
        # Work Order durumlarını analiz et
        wo_statuses = [wo.status for wo in work_orders]
        total_wo_count = len(work_orders)
        completed_count = sum(1 for status in wo_statuses if status == "Completed")
        in_process_count = sum(1 for status in wo_statuses if status in ["In Process", "In Progress"])
        cancelled_count = sum(1 for status in wo_statuses if status == "Cancelled")
        active_wo_count = total_wo_count - cancelled_count
        
        updated = False
        
        # Durum 1: Tüm aktif Work Order'lar tamamlandı → "Tamamlandı"
        if active_wo_count > 0 and completed_count == active_wo_count and pp_doc.status == "Completed":
            if current_workflow_state not in ["Tamamlandı"]:
                # Önce "Devam Ediyor" durumuna geç (eğer değilse)
                if current_workflow_state == "Üretime Hazır":
                    try:
                        apply_workflow(pp_doc, "Üretimi Başlat")
                        frappe.db.commit()
                        pp_doc.reload()
                        print(f"  [{idx}/{total_count}] {pp.name}: Üretime Hazır → Devam Ediyor")
                    except Exception as e:
                        print(f"  ⚠️  [{idx}/{total_count}] {pp.name}: Üretimi Başlat hatası - {str(e)}")
                
                # Sonra "Tamamlandı" durumuna geç
                if pp_doc.workflow_state == "Devam Ediyor":
                    try:
                        apply_workflow(pp_doc, "Üretimi Bitir")
                        frappe.db.commit()
                        updated_count += 1
                        updated = True
                        print(f"  ✅ [{idx}/{total_count}] {pp.name}: Devam Ediyor → Tamamlandı ({completed_count}/{active_wo_count} WO tamamlandı)")
                    except Exception as e:
                        print(f"  ⚠️  [{idx}/{total_count}] {pp.name}: Üretimi Bitir hatası - {str(e)}")
        
        # Durum 2: En az bir Work Order "In Process" → "Devam Ediyor"
        elif (in_process_count > 0 or (completed_count > 0 and completed_count < active_wo_count)) and pp_doc.status == "In Process":
            if current_workflow_state == "Üretime Hazır":
                try:
                    apply_workflow(pp_doc, "Üretimi Başlat")
                    frappe.db.commit()
                    updated_count += 1
                    updated = True
                    print(f"  ✅ [{idx}/{total_count}] {pp.name}: Üretime Hazır → Devam Ediyor ({in_process_count} devam ediyor, {completed_count}/{active_wo_count} tamamlandı)")
                except Exception as e:
                    print(f"  ⚠️  [{idx}/{total_count}] {pp.name}: Üretimi Başlat hatası - {str(e)}")
        
        if not updated and idx % 50 == 0:
            print(f"  📍 [{idx}/{total_count}] İşleniyor...")
    
    except Exception as e:
        error_count += 1
        print(f"  ❌ [{idx}/{total_count}] {pp.name}: Hata - {str(e)}")
        frappe.log_error(
            title=f"Production Plan Workflow Sync Error ({pp.name})",
            message=str(e)
        )

print(f"\n{'='*60}")
print(f"✅ Güncelleme tamamlandı!")
print(f"   📊 Toplam: {total_count} Production Plan")
print(f"   ✅ Güncellenen: {updated_count}")
print(f"   ⏭️  Atlanan (WO yok): {skipped_count}")
print(f"   ❌ Hata: {error_count}")
print(f"{'='*60}\n")

frappe.db.commit()

