# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
Profile Stock Ledger Duplicate Consolidation Script

Bu script mevcut duplicate kayıtları bulur ve birleştirir.
Aynı profile_type, length, is_scrap_piece kombinasyonu için
birden fazla kayıt varsa, bunları tek kayıtta birleştirir.

Kullanım:
    bench --site sitename execute uretim_planlama.api.consolidate_profile_stock.consolidate_duplicates
"""

import frappe
from frappe import _
from frappe.utils import flt


def consolidate_duplicates(dry_run=True):
    """
    Profile Stock Ledger duplicate kayıtlarını birleştirir.
    
    Args:
        dry_run (bool): True ise sadece rapor verir, değişiklik yapmaz
    """
    print(f"{'='*60}")
    print(f"PROFILE STOCK LEDGER DUPLICATE CONSOLIDATION")
    print(f"{'='*60}")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print()
    
    # Duplicate kayıtları bul
    duplicates = _find_duplicate_records()
    
    if not duplicates:
        print("✅ Hiç duplicate kayıt bulunamadı!")
        return
    
    print(f"🔍 {len(duplicates)} adet duplicate grup bulundu:")
    print()
    
    total_consolidated = 0
    total_deleted = 0
    
    for group in duplicates:
        item_code = group['item_code']
        length = group['length']
        is_scrap = group['is_scrap_piece']
        records = group['records']
        total_qty = sum(flt(r['qty']) for r in records)
        
        print(f"📦 {item_code} - {length}m - Scrap: {is_scrap}")
        print(f"   Kayıt sayısı: {len(records)}")
        print(f"   Toplam miktar: {total_qty}")
        
        for record in records:
            print(f"     - {record['name']}: {record['qty']} adet")
        
        if not dry_run:
            try:
                # Birleştirme işlemi
                _consolidate_group(records, item_code, length, is_scrap)
                total_consolidated += len(records) - 1  # Ana kayıt hariç
                total_deleted += len(records) - 1
                print(f"   ✅ Birleştirildi!")
            except Exception as e:
                print(f"   ❌ Hata: {str(e)}")
                frappe.log_error(f"Consolidation error: {str(e)}", "Profile Stock Consolidation Error")
        else:
            print(f"   📋 DRY RUN - Birleştirilecek")
        
        print()
    
    print(f"{'='*60}")
    print(f"ÖZET:")
    print(f"   Toplam duplicate grup: {len(duplicates)}")
    
    if dry_run:
        print(f"   DRY RUN - Hiçbir değişiklik yapılmadı")
        print(f"   Gerçek çalıştırmak için: dry_run=False kullanın")
    else:
        print(f"   Birleştirilen kayıt: {total_consolidated}")
        print(f"   Silinen kayıt: {total_deleted}")
    
    print(f"{'='*60}")


def _find_duplicate_records():
    """Duplicate kayıtları bulur"""
    
    # SQL ile duplicate grupları bul
    query = """
        SELECT 
            item_code,
            length,
            is_scrap_piece,
            COUNT(*) as record_count,
            SUM(qty) as total_qty
        FROM `tabProfile Stock Ledger`
        GROUP BY item_code, length, is_scrap_piece
        HAVING COUNT(*) > 1
        ORDER BY record_count DESC, total_qty DESC
    """
    
    duplicate_groups = frappe.db.sql(query, as_dict=True)
    
    # Her grup için detaylı kayıtları al
    result = []
    for group in duplicate_groups:
        records = frappe.get_all(
            "Profile Stock Ledger",
            filters={
                "item_code": group.item_code,
                "length": group.length,
                "is_scrap_piece": group.is_scrap_piece
            },
            fields=["name", "qty", "creation", "modified"],
            order_by="creation desc"
        )
        
        result.append({
            "item_code": group.item_code,
            "length": group.length,
            "is_scrap_piece": group.is_scrap_piece,
            "records": records
        })
    
    return result


def _consolidate_group(records, item_code, length, is_scrap_piece):
    """Bir duplicate grubu birleştirir"""
    
    # Toplam miktarı hesapla
    total_qty = sum(flt(record['qty']) for record in records)
    
    # En son oluşturulan kaydı ana kayıt olarak seç
    main_record = records[0]  # creation desc ile sıralandı
    main_doc = frappe.get_doc("Profile Stock Ledger", main_record['name'])
    
    # Ana kaydı güncelle
    main_doc.qty = total_qty
    main_doc.save()
    
    # Diğer kayıtları sil
    for record in records[1:]:
        frappe.delete_doc("Profile Stock Ledger", record['name'])
    
    # Log kaydı
    frappe.logger().info(
        f"Profile Stock Ledger consolidation: {item_code} {length}m "
        f"(scrap: {is_scrap_piece}) -> {len(records)} kayıt birleştirildi, "
        f"toplam qty: {total_qty}"
    )


def get_consolidation_report():
    """Consolidation raporu oluşturur"""
    duplicates = _find_duplicate_records()
    
    if not duplicates:
        return {
            "status": "clean",
            "message": "Hiç duplicate kayıt bulunamadı",
            "duplicate_count": 0
        }
    
    total_records = sum(len(group['records']) for group in duplicates)
    total_consolidated = sum(len(group['records']) - 1 for group in duplicates)
    
    return {
        "status": "duplicates_found",
        "message": f"{len(duplicates)} duplicate grup, {total_records} kayıt bulundu",
        "duplicate_count": len(duplicates),
        "total_records": total_records,
        "will_consolidate": total_consolidated,
        "groups": duplicates
    }


if __name__ == "__main__":
    # Script olarak çalıştırıldığında
    import sys
    
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1].lower() == "execute":
        dry_run = False
    
    consolidate_duplicates(dry_run=dry_run)
