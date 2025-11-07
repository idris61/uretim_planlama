"""
Patch: Normalize all existing rezerv quantities to fix float precision issues
Version: 1.0.0
Date: 2025-11-05

Bu patch mevcut tüm rezerv kayıtlarındaki miktarları flt() ile normalize eder.
Geçmişte float hassasiyet sorunlarından kaynaklanan küsürat problemlerini temizler.
"""

import frappe
from frappe.utils import flt


def execute():
    """
    Tüm mevcut Rezerved Raw Materials ve Long Term Reserve Usage kayıtlarındaki
    miktarları normalize eder (6 ondalık basamak).
    """
    frappe.db.auto_commit_on_many_writes = True
    
    try:
        # 1. Rezerved Raw Materials kayıtlarını normalize et
        print("\n" + "="*80)
        print("REZERV KAYITLARI NORMALİZASYONU BAŞLIYOR")
        print("="*80)
        
        normalize_reserved_raw_materials()
        normalize_long_term_reserve_usage()
        cleanup_zero_records()
        
        frappe.db.commit()
        
        print("\n" + "="*80)
        print("✓ TAMAMLANDI - Tüm rezerv kayıtları normalize edildi")
        print("="*80 + "\n")
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error("Rezerv Normalize Patch Hatası", frappe.get_traceback())
        print(f"\n✗ HATA: {str(e)}")
        raise


def normalize_reserved_raw_materials():
    """Rezerved Raw Materials kayıtlarını normalize eder"""
    print("\n1. Rezerved Raw Materials kayıtları kontrol ediliyor...")
    
    # Tüm kayıtları al
    records = frappe.db.sql("""
        SELECT name, quantity
        FROM `tabRezerved Raw Materials`
    """, as_dict=True)
    
    print(f"   Toplam {len(records)} kayıt bulundu")
    
    updated_count = 0
    deleted_count = 0
    
    for record in records:
        try:
            original_qty = record.quantity or 0
            normalized_qty = flt(original_qty, 6)
            
            # Sıfıra çok yakın değerleri sil
            if normalized_qty <= flt(0.000001, 6):
                frappe.db.sql("""
                    DELETE FROM `tabRezerved Raw Materials`
                    WHERE name = %s
                """, (record.name,))
                deleted_count += 1
                print(f"   ✓ Silindi: {record.name} (miktar: {original_qty} → sıfır)")
                continue
            
            # Eğer değer değiştiyse güncelle
            if original_qty != normalized_qty:
                frappe.db.sql("""
                    UPDATE `tabRezerved Raw Materials`
                    SET quantity = %s
                    WHERE name = %s
                """, (normalized_qty, record.name))
                updated_count += 1
                print(f"   ✓ Güncellendi: {record.name}")
                print(f"     Öncesi: {original_qty:.15f}")
                print(f"     Sonrası: {normalized_qty:.6f}")
        
        except Exception as e:
            print(f"   ✗ Hata ({record.name}): {str(e)}")
            continue
    
    print(f"\n   Özet:")
    print(f"   - Güncellenen: {updated_count} kayıt")
    print(f"   - Silinen (sıfır): {deleted_count} kayıt")
    print(f"   - Değişmeyen: {len(records) - updated_count - deleted_count} kayıt")


def normalize_long_term_reserve_usage():
    """Long Term Reserve Usage kayıtlarını normalize eder"""
    print("\n2. Long Term Reserve Usage kayıtları kontrol ediliyor...")
    
    # Tüm kayıtları al
    records = frappe.db.sql("""
        SELECT name, used_qty
        FROM `tabLong Term Reserve Usage`
    """, as_dict=True)
    
    print(f"   Toplam {len(records)} kayıt bulundu")
    
    updated_count = 0
    deleted_count = 0
    
    for record in records:
        try:
            original_qty = record.used_qty or 0
            normalized_qty = flt(original_qty, 6)
            
            # Sıfıra çok yakın değerleri sil
            if normalized_qty <= flt(0.000001, 6):
                frappe.db.sql("""
                    DELETE FROM `tabLong Term Reserve Usage`
                    WHERE name = %s
                """, (record.name,))
                deleted_count += 1
                print(f"   ✓ Silindi: {record.name} (miktar: {original_qty} → sıfır)")
                continue
            
            # Eğer değer değiştiyse güncelle
            if original_qty != normalized_qty:
                frappe.db.sql("""
                    UPDATE `tabLong Term Reserve Usage`
                    SET used_qty = %s
                    WHERE name = %s
                """, (normalized_qty, record.name))
                updated_count += 1
                print(f"   ✓ Güncellendi: {record.name}")
                print(f"     Öncesi: {original_qty:.15f}")
                print(f"     Sonrası: {normalized_qty:.6f}")
        
        except Exception as e:
            print(f"   ✗ Hata ({record.name}): {str(e)}")
            continue
    
    print(f"\n   Özet:")
    print(f"   - Güncellenen: {updated_count} kayıt")
    print(f"   - Silinen (sıfır): {deleted_count} kayıt")
    print(f"   - Değişmeyen: {len(records) - updated_count - deleted_count} kayıt")


def cleanup_zero_records():
    """Negatif veya sıfıra yakın kayıtları temizler"""
    print("\n3. Negatif/Sıfır kayıtlar temizleniyor...")
    
    # Negatif Rezerved Raw Materials kayıtları
    negative_reserves = frappe.db.sql("""
        SELECT name, quantity
        FROM `tabRezerved Raw Materials`
        WHERE quantity < 0.000001
    """, as_dict=True)
    
    for record in negative_reserves:
        frappe.db.sql("""
            DELETE FROM `tabRezerved Raw Materials`
            WHERE name = %s
        """, (record.name,))
        print(f"   ✓ Temizlendi (Rezerv): {record.name} (miktar: {record.quantity})")
    
    # Negatif Long Term Reserve Usage kayıtları
    negative_usage = frappe.db.sql("""
        SELECT name, used_qty
        FROM `tabLong Term Reserve Usage`
        WHERE used_qty < 0.000001
    """, as_dict=True)
    
    for record in negative_usage:
        frappe.db.sql("""
            DELETE FROM `tabLong Term Reserve Usage`
            WHERE name = %s
        """, (record.name,))
        print(f"   ✓ Temizlendi (Usage): {record.name} (miktar: {record.used_qty})")
    
    print(f"\n   Özet:")
    print(f"   - Temizlenen rezerv: {len(negative_reserves)} kayıt")
    print(f"   - Temizlenen usage: {len(negative_usage)} kayıt")


if __name__ == "__main__":
    # Manuel çalıştırma için
    execute()


