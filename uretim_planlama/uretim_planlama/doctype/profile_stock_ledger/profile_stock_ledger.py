# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProfileStockLedger(Document):
	def validate(self):
		# Boy (m) ve Miktar girildiyse, Toplam Boy (m) otomatik hesapla
		if self.length and self.qty:
			self.total_length = float(self.length) * int(self.qty)
		else:
			self.total_length = 0

def update_profile_stock(profile_type, length, qty, action, is_scrap_piece=0):
    """
    Profil stoklarını günceller. action: 'in' (giriş) veya 'out' (çıkış)
    """
    filters = {"profile_type": profile_type, "length": length, "is_scrap_piece": is_scrap_piece}
    stock = frappe.get_all("Profile Stock Ledger", filters=filters, fields=["name", "qty", "total_length"])
    if stock:
        doc = frappe.get_doc("Profile Stock Ledger", stock[0].name)
        if action == "in":
            doc.qty += qty
        elif action == "out":
            doc.qty -= qty
            if doc.qty < 0:
                frappe.throw(f"Yetersiz stok: {profile_type} {length}m profilden çıkış yapılamaz.")
        doc.total_length = doc.qty * doc.length
        if doc.qty == 0:
            doc.delete()
        else:
            doc.save()
    else:
        if action == "in":
            doc = frappe.new_doc("Profile Stock Ledger")
            doc.profile_type = profile_type
            doc.length = length
            doc.qty = qty
            doc.is_scrap_piece = is_scrap_piece
            doc.total_length = qty * length
            doc.insert()
        else:
            frappe.throw(f"Stokta olmayan profilden çıkış yapılamaz: {profile_type} {length}m")

def get_profile_stock(profile_type=None):
    """
    Profil stoklarını (boy ve adet bazında) listeler.
    """
    filters = {}
    if profile_type:
        filters["profile_type"] = profile_type
    return frappe.get_all(
        "Profile Stock Ledger",
        filters=filters,
        fields=["profile_type", "length", "qty", "total_length"],
        order_by="profile_type, length"
    )

def get_length_options(doctype):
    """
    Belirtilen doctype'ta length alanının options'ını alır
    """
    try:
        meta = frappe.get_meta(doctype)
        length_field = meta.get_field("length")
        if length_field and length_field.fieldtype == "Select":
            return [opt.strip() for opt in length_field.options.split('\n') if opt.strip()]
        return []
    except:
        return []

def reconcile_profile_stock_with_entries(counts, posting_date=None):
    """
    Sayım sonrası fiili stok ile sistemdeki stok arasındaki farkı Profile Stock Ledger'da günceller.
    counts: [
        {"profile_type": "Profil-1", "length": 5, "qty": 8},
        {"profile_type": "Profil-1", "length": 6, "qty": 4},
        ...
    ]
    posting_date: Düzeltme belgeleri için kullanılacak tarih (opsiyonel)
    """
    errors = []
    success_count = 0
    
    for count in counts:
        try:
            # Mevcut stok kaydını bul
            filters = {
                "profile_type": count["profile_type"],
                "length": count["length"],
                "is_scrap_piece": 0
            }
            
            existing_stock = frappe.get_all("Profile Stock Ledger", filters=filters, fields=["name", "qty"])
            
            if existing_stock:
                # Mevcut kaydı güncelle
                stock_doc = frappe.get_doc("Profile Stock Ledger", existing_stock[0].name)
                stock_doc.qty = count["qty"]
                stock_doc.total_length = count["qty"] * count["length"]
                stock_doc.save()
                success_count += 1
            else:
                # Yeni kayıt oluştur
                new_stock = frappe.get_doc({
                    "doctype": "Profile Stock Ledger",
                    "profile_type": count["profile_type"],
                    "length": count["length"],
                    "qty": count["qty"],
                    "total_length": count["qty"] * count["length"],
                    "is_scrap_piece": 0
                })
                new_stock.insert()
                success_count += 1
                
        except Exception as e:
            error_msg = f"Profil: {count['profile_type']}, Boy: {count['length']}, Hata: {str(e)}"
            errors.append(error_msg)
    
    # Sonuçları kullanıcıya bildir
    if errors:
        error_text = "\n".join(errors)
        frappe.msgprint(
            f"Stok güncelleme tamamlandı!\n\n"
            f"Başarılı işlem: {success_count} adet\n"
            f"Hatalı işlem: {len(errors)} adet\n\n"
            f"Hata detayları:\n{error_text}",
            title="Stok Güncelleme Sonucu",
            indicator="yellow" if errors else "green"
        )
    else:
        frappe.msgprint(
            f"Stok güncelleme başarıyla tamamlandı!\n"
            f"Toplam {success_count} adet kayıt güncellendi.",
            title="Stok Güncelleme Sonucu",
            indicator="green"
        )

def after_import(doc, method):
    """
    Import işlemi tamamlandıktan sonra otomatik olarak çalışır.
    Mevcut stok ile import edilen stok arasındaki farkı Profile Stock Ledger'da günceller.
    """
    try:
        # Import edilen verileri al
        imported_data = frappe.get_all(
            "Profile Stock Ledger",
            filters={"name": doc.name},
            fields=["profile_type", "length", "qty"]
        )
        
        if imported_data:
            reconcile_profile_stock_with_entries(imported_data)
        
    except Exception as e:
        frappe.log_error(f"Profile Stock Ledger after_import hatası: {str(e)}", "Profile Stock Ledger Import Error")
