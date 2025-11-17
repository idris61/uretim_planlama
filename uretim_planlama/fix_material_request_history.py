#!/usr/bin/env python3
"""
Material Request Geçmiş Verileri Düzeltme
==========================================

Eski hatalı kod ile oluşturulmuş Material Request'lerin
ordered_qty ve received_qty değerlerini Purchase Order ve 
Purchase Receipt belgelerine göre düzeltir.

Kullanım:
bench --site [site_name] execute uretim_planlama.uretim_planlama.fix_material_request_history.fix_all_material_requests

veya

bench --site [site_name] console
>>> from uretim_planlama.uretim_planlama.fix_material_request_history import fix_material_request
>>> fix_material_request("MAT-MR-2025-00001")
"""

import frappe


@frappe.whitelist()
def fix_material_request(mr_name, dry_run=True):
    """
    Tek bir Material Request'i düzelt
    
    Args:
        mr_name: Material Request adı
        dry_run: True ise sadece rapor göster, değişiklik yapma
    """
    print("=" * 100)
    print(f"Material Request Düzeltme: {mr_name}")
    print(f"Mod: {'DRY RUN (Değişiklik yapılmayacak)' if dry_run else 'CANLI (Değişiklikler uygulanacak)'}")
    print("=" * 100)
    
    # MR'yi kontrol et
    if not frappe.db.exists("Material Request", mr_name):
        print(f"❌ {mr_name} bulunamadı!")
        return
    
    mr_doc = frappe.get_doc("Material Request", mr_name)
    
    if mr_doc.docstatus != 1:
        print(f"⚠️  {mr_name} submit edilmemiş (docstatus={mr_doc.docstatus})")
        return
    
    print(f"\n📋 Mevcut Durum:")
    print(f"  Status: {mr_doc.status}")
    print(f"  per_ordered: {mr_doc.per_ordered:.2f}%")
    print(f"  per_received: {mr_doc.per_received:.2f}%")
    print(f"  Toplam Item: {len(mr_doc.items)}")
    
    # Purchase Order'lardan gerçek ordered_qty'yi hesapla
    print(f"\n🔍 Purchase Order'ları tarıyorum...")
    
    po_items = frappe.db.sql("""
        SELECT poi.item_code, SUM(poi.stock_qty) as total_ordered
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
        WHERE po.docstatus = 1
        AND (poi.custom_material_request_references LIKE %(mr_pattern)s
            OR poi.material_request = %(mr_name)s)
        GROUP BY poi.item_code
    """, {"mr_name": mr_name, "mr_pattern": f"%{mr_name}%"}, as_dict=1)
    
    real_ordered = {item.item_code: item.total_ordered for item in po_items}
    print(f"  Bulunan PO item'ları: {len(real_ordered)}")
    
    # Purchase Receipt'lerden gerçek received_qty'yi hesapla
    print(f"\n🔍 Purchase Receipt'leri tarıyorum...")
    
    pr_items = frappe.db.sql("""
        SELECT pri.item_code, SUM(pri.stock_qty) as total_received
        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE pr.docstatus = 1
        AND (pri.custom_material_request_references LIKE %(mr_pattern)s
            OR pri.material_request = %(mr_name)s)
        GROUP BY pri.item_code
    """, {"mr_name": mr_name, "mr_pattern": f"%{mr_name}%"}, as_dict=1)
    
    real_received = {item.item_code: item.total_received for item in pr_items}
    print(f"  Bulunan PR item'ları: {len(real_received)}")
    
    # Stock Entry'lerden transferred_qty hesapla (Material Transfer tipinde)
    if mr_doc.material_request_type == "Material Transfer":
        print(f"\n🔍 Stock Entry'leri tarıyorum...")
        
        se_items = frappe.db.sql("""
            SELECT sed.item_code, SUM(sed.qty) as total_transferred
            FROM `tabStock Entry Detail` sed
            INNER JOIN `tabStock Entry` se ON se.name = sed.parent
            WHERE se.docstatus = 1
            AND se.stock_entry_type = 'Material Transfer'
            AND (sed.custom_material_request_references LIKE %(mr_pattern)s
                OR sed.material_request = %(mr_name)s)
            GROUP BY sed.item_code
        """, {"mr_name": mr_name, "mr_pattern": f"%{mr_name}%"}, as_dict=1)
        
        real_ordered = {item.item_code: item.total_transferred for item in se_items}
        print(f"  Bulunan SE item'ları: {len(real_ordered)}")
    
    # Düzeltmeleri uygula
    print(f"\n🔧 Düzeltmeler:")
    
    updated_count = 0
    reset_count = 0
    
    for item in mr_doc.items:
        item_code = item.item_code
        current_ordered = item.ordered_qty
        current_received = item.received_qty
        
        # Gerçek değerler
        correct_ordered = real_ordered.get(item_code, 0)
        correct_received = real_received.get(item_code, 0)
        
        # Düzeltme gerekiyor mu?
        if current_ordered != correct_ordered or current_received != correct_received:
            if correct_ordered > 0 or correct_received > 0:
                print(f"  ✏️  {item_code}:")
                print(f"      ordered: {current_ordered:,.0f} → {correct_ordered:,.0f}")
                print(f"      received: {current_received:,.0f} → {correct_received:,.0f}")
                updated_count += 1
            else:
                reset_count += 1
            
            if not dry_run:
                frappe.db.sql("""
                    UPDATE `tabMaterial Request Item`
                    SET ordered_qty = %(ordered)s, 
                        received_qty = %(received)s
                    WHERE name = %(name)s
                """, {
                    "ordered": correct_ordered,
                    "received": correct_received,
                    "name": item.name
                })
    
    if reset_count > 0:
        print(f"  🔄 {reset_count} item sıfırlanacak (gerçekte sipariş/alış yok)")
    
    if updated_count == 0 and reset_count == 0:
        print(f"  ✅ Düzeltme gerekmiyor, tüm değerler doğru!")
        return
    
    # per_ordered ve per_received'ı yeniden hesapla
    if not dry_run:
        print(f"\n🔧 per_ordered ve per_received hesaplanıyor...")
        
        frappe.db.sql("""
            UPDATE `tabMaterial Request` mr
            SET per_ordered = (
                SELECT 
                    CASE 
                        WHEN SUM(stock_qty) > 0 
                        THEN (SUM(ordered_qty) / SUM(stock_qty)) * 100
                        ELSE 0
                    END
                FROM `tabMaterial Request Item`
                WHERE parent = mr.name
            ),
            per_received = (
                SELECT 
                    CASE 
                        WHEN SUM(stock_qty) > 0 
                        THEN (SUM(received_qty) / SUM(stock_qty)) * 100
                        ELSE 0
                    END
                FROM `tabMaterial Request Item`
                WHERE parent = mr.name
            )
            WHERE name = %(mr_name)s
        """, {"mr_name": mr_name})
        
        # Reload ve status güncelle
        mr_doc.reload()
        
        # ERPNext'in standart set_status metodunu kullan
        try:
            mr_doc.set_status(update=True)
        except:
            pass
        
        frappe.db.commit()
    
    # Sonuç raporu
    mr_doc.reload()
    
    print(f"\n📊 {'Yeni' if not dry_run else 'Olacak'} Durum:")
    print(f"  Status: {mr_doc.status}")
    print(f"  per_ordered: {mr_doc.per_ordered:.2f}%")
    print(f"  per_received: {mr_doc.per_received:.2f}%")
    
    print(f"\n✅ Özet:")
    print(f"  Güncellenen: {updated_count} item")
    print(f"  Sıfırlanan: {reset_count} item")
    
    if dry_run:
        print(f"\n⚠️  DRY RUN modu - Değişiklikler uygulanmadı!")
        print(f"   Uygulamak için: fix_material_request('{mr_name}', dry_run=False)")
    else:
        print(f"\n✅ Değişiklikler başarıyla uygulandı!")
    
    print("=" * 100)
    
    return {
        "mr_name": mr_name,
        "updated": updated_count,
        "reset": reset_count,
        "status": mr_doc.status,
        "per_ordered": mr_doc.per_ordered,
        "per_received": mr_doc.per_received
    }


@frappe.whitelist()
def fix_all_material_requests(from_date=None, to_date=None, dry_run=True):
    """
    Belirli tarih aralığındaki tüm Material Request'leri düzelt
    
    Args:
        from_date: Başlangıç tarihi (YYYY-MM-DD)
        to_date: Bitiş tarihi (YYYY-MM-DD)
        dry_run: True ise sadece rapor göster
    """
    print("=" * 100)
    print("TOPLU MATERIAL REQUEST DÜZELTMESİ")
    print("=" * 100)
    
    # Tarih filtresi
    filters = {"docstatus": 1}
    
    if from_date:
        filters["transaction_date"] = [">=", from_date]
    if to_date:
        if "transaction_date" in filters:
            filters["transaction_date"] = ["between", [from_date, to_date]]
        else:
            filters["transaction_date"] = ["<=", to_date]
    
    # Material Request'leri çek
    mr_list = frappe.get_all(
        "Material Request",
        filters=filters,
        fields=["name", "transaction_date", "status"],
        order_by="transaction_date desc"
    )
    
    print(f"\n📋 Bulunan Material Request: {len(mr_list)}")
    
    if not mr_list:
        print("⚠️  Düzeltilecek kayıt bulunamadı!")
        return
    
    # Her birini düzelt
    results = []
    
    for idx, mr in enumerate(mr_list, 1):
        print(f"\n[{idx}/{len(mr_list)}] İşleniyor: {mr.name} ({mr.transaction_date})")
        print("-" * 100)
        
        result = fix_material_request(mr.name, dry_run=dry_run)
        if result:
            results.append(result)
    
    # Özet rapor
    print("\n" + "=" * 100)
    print("TOPLU DÜZELTME ÖZETİ")
    print("=" * 100)
    
    total_updated = sum(r["updated"] for r in results)
    total_reset = sum(r["reset"] for r in results)
    
    print(f"\nİşlenen MR: {len(results)}")
    print(f"Güncellenen toplam item: {total_updated}")
    print(f"Sıfırlanan toplam item: {total_reset}")
    
    if dry_run:
        print(f"\n⚠️  DRY RUN modu - Hiçbir değişiklik uygulanmadı!")
        print(f"\nUygulamak için:")
        print(f"  Python: fix_all_material_requests(dry_run=False)")
    else:
        print(f"\n✅ Tüm düzeltmeler başarıyla uygulandı!")
    
    print("=" * 100)
    
    return results


if __name__ == "__main__":
    # Manuel test için
    import sys
    
    if len(sys.argv) > 1:
        mr_name = sys.argv[1]
        dry_run = sys.argv[2].lower() != "false" if len(sys.argv) > 2 else True
        
        frappe.init(site='ozerpan.com')
        frappe.connect()
        
        fix_material_request(mr_name, dry_run=dry_run)
        
        frappe.destroy()





