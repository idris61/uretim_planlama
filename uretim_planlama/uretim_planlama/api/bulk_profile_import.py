# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
Bulk Profile Stock Import Handler

Bu modül Profile Stock Ledger import işlemleri için özel handler sağlar.
Import sırasında Profile Entry kayıtları da otomatik oluşturulur.

Kullanım:
    bench --site sitename execute uretim_planlama.api.bulk_profile_import.process_bulk_import --args "{'file_path': '/path/to/file.csv'}"
"""

import frappe
from frappe import _
from frappe.utils import flt, today
import csv
import io


def process_bulk_import(file_path, create_profile_entries=True, submit_entries=True):
    """
    Profile Stock Ledger bulk import işlemi yapar ve Profile Entry kayıtları oluşturur.
    
    Args:
        file_path (str): CSV dosya yolu
        create_profile_entries (bool): Profile Entry kayıtları oluşturulsun mu?
        submit_entries (bool): Profile Entry kayıtları submit edilsin mi?
    """
    print(f"{'='*60}")
    print(f"BULK PROFILE STOCK IMPORT")
    print(f"{'='*60}")
    print(f"Dosya: {file_path}")
    print(f"Profile Entry Oluştur: {'Evet' if create_profile_entries else 'Hayır'}")
    print(f"Profile Entry Submit: {'Evet' if submit_entries else 'Hayır'}")
    print()
    
    try:
        # CSV dosyasını oku
        import_data = _read_csv_file(file_path)
        print(f"📊 {len(import_data)} satır veri okundu")
        
        # Verileri grupla (aynı gün için bir Profile Entry)
        grouped_data = _group_by_date(import_data)
        print(f"📅 {len(grouped_data)} farklı tarih grubu bulundu")
        
        # Profile Stock Ledger kayıtlarını oluştur
        stock_records = _create_stock_records(import_data)
        print(f"📦 {len(stock_records)} Profile Stock Ledger kaydı oluşturuldu")
        
        # Profile Entry kayıtlarını oluştur (isteğe bağlı)
        if create_profile_entries:
            entry_records = _create_profile_entries(grouped_data, submit_entries)
            print(f"📝 {len(entry_records)} Profile Entry kaydı oluşturuldu")
        else:
            entry_records = []
        
        # Sonuç raporu
        _print_import_summary(import_data, stock_records, entry_records)
        
        return {
            "status": "success",
            "stock_records": len(stock_records),
            "entry_records": len(entry_records),
            "total_rows": len(import_data)
        }
        
    except Exception as e:
        frappe.log_error(f"Bulk import hatası: {str(e)}", "Bulk Profile Import Error")
        print(f"❌ Hata: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


def _read_csv_file(file_path):
    """CSV dosyasını okur ve veriyi döner"""
    import_data = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        # CSV header'ını oku
        reader = csv.DictReader(file)
        
        for row_idx, row in enumerate(reader, 1):
            try:
                # Gerekli alanları kontrol et
                required_fields = ['item_code', 'length', 'qty']
                missing_fields = [field for field in required_fields if not row.get(field)]
                
                if missing_fields:
                    print(f"⚠️ Satır {row_idx}: Eksik alanlar - {missing_fields}")
                    continue
                
                # Veriyi temizle ve dönüştür
                clean_data = {
                    'item_code': row['item_code'].strip(),
                    'length': flt(row['length']),
                    'qty': flt(row['qty']),
                    'is_scrap_piece': row.get('is_scrap_piece', '0').strip() in ['1', 'true', 'yes'],
                    'date': row.get('date', today()),
                    'supplier': row.get('supplier', '').strip() or None,
                    'remarks': row.get('remarks', '').strip() or None
                }
                
                import_data.append(clean_data)
                
            except Exception as e:
                print(f"❌ Satır {row_idx} okuma hatası: {str(e)}")
                continue
    
    return import_data


def _group_by_date(import_data):
    """Verileri tarihe göre gruplar"""
    grouped = {}
    
    for data in import_data:
        date_key = data['date']
        if date_key not in grouped:
            grouped[date_key] = {
                'date': date_key,
                'supplier': data.get('supplier'),
                'remarks': data.get('remarks'),
                'items': []
            }
        
        grouped[date_key]['items'].append({
            'item_code': data['item_code'],
            'length': data['length'],
            'qty': data['qty']
        })
    
    return grouped


def _create_stock_records(import_data):
    """Profile Stock Ledger kayıtlarını oluşturur"""
    created_records = []
    
    for data in import_data:
        try:
            # Profile Stock Ledger kaydı oluştur
            stock_doc = frappe.get_doc({
                "doctype": "Profile Stock Ledger",
                "item_code": data['item_code'],
                "length": data['length'],
                "qty": data['qty'],
                "is_scrap_piece": data['is_scrap_piece']
            })
            
            # Import flag'ini set et
            stock_doc.flags.in_import = True
            stock_doc.flags.ignore_validate = True
            
            stock_doc.insert()
            created_records.append(stock_doc.name)
            
        except Exception as e:
            print(f"❌ Profile Stock Ledger oluşturma hatası: {str(e)}")
            frappe.log_error(f"Stock record creation error: {str(e)}", "Profile Stock Import Error")
    
    return created_records


def _create_profile_entries(grouped_data, submit_entries=True):
    """Profile Entry kayıtlarını oluşturur"""
    created_entries = []
    
    for date_key, group_data in grouped_data.items():
        try:
            # Profile Entry oluştur
            entry_doc = frappe.get_doc({
                "doctype": "Profile Entry",
                "date": group_data['date'],
                "supplier": group_data.get('supplier'),
                "remarks": group_data.get('remarks') or f"Bulk import - {len(group_data['items'])} ürün",
                "items": []
            })
            
            # Items ekle
            for item in group_data['items']:
                entry_doc.append("items", {
                    "item_code": item['item_code'],
                    "length": item['length'],
                    "received_quantity": item['qty'],
                    "reference_type": "Manual Entry"
                })
            
            # Validation'ları bypass et
            entry_doc.flags.ignore_validate = True
            entry_doc.flags.ignore_permissions = True
            entry_doc.flags.bypass_group_check = True
            
            entry_doc.insert()
            
            # Submit et (isteğe bağlı)
            if submit_entries:
                entry_doc.flags.ignore_validate = True
                entry_doc.submit()
            
            created_entries.append(entry_doc.name)
            
        except Exception as e:
            print(f"❌ Profile Entry oluşturma hatası: {str(e)}")
            frappe.log_error(f"Entry creation error: {str(e)}", "Profile Entry Import Error")
    
    return created_entries


def _print_import_summary(import_data, stock_records, entry_records):
    """Import özetini yazdırır"""
    print(f"{'='*60}")
    print(f"IMPORT ÖZETİ")
    print(f"{'='*60}")
    print(f"📊 Toplam satır: {len(import_data)}")
    print(f"📦 Profile Stock Ledger: {len(stock_records)} kayıt")
    print(f"📝 Profile Entry: {len(entry_records)} kayıt")
    
    # Ürün bazında özet
    profile_summary = {}
    for data in import_data:
        key = f"{data['item_code']} - {data['length']}m"
        if key not in profile_summary:
            profile_summary[key] = 0
        profile_summary[key] += data['qty']
    
    print(f"\n📋 ÜRÜN BAZINDA ÖZET:")
    for profile, total_qty in sorted(profile_summary.items()):
        print(f"   {profile}: {total_qty} adet")
    
    print(f"{'='*60}")


def create_import_template():
    """Import için örnek CSV template oluşturur"""
    template_path = "/tmp/profile_stock_import_template.csv"
    
    sample_data = [
        {
            'item_code': '101073427',
            'length': 6.5,
            'qty': 100,
            'is_scrap_piece': 0,
            'date': '2025-01-15',
            'supplier': 'Tedarikçi A',
            'remarks': 'Açıklama'
        },
        {
            'item_code': '102003427',
            'length': 6.5,
            'qty': 50,
            'is_scrap_piece': 0,
            'date': '2025-01-15',
            'supplier': 'Tedarikçi A',
            'remarks': 'Açıklama'
        }
    ]
    
    with open(template_path, 'w', newline='', encoding='utf-8') as file:
        if sample_data:
            writer = csv.DictWriter(file, fieldnames=sample_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_data)
    
    print(f"✅ Template oluşturuldu: {template_path}")
    return template_path


if __name__ == "__main__":
    # Script olarak çalıştırıldığında template oluştur
    create_import_template()
