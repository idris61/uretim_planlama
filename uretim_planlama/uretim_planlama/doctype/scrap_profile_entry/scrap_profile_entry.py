# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger import update_profile_stock
from uretim_planlama.uretim_planlama.utils import (
    normalize_length_to_string, get_length_value_from_boy_doctype,
    is_profile_item_group
)
from frappe import _

class ScrapProfileEntry(Document):
    def validate(self):
        """Scrap profil girişi doğrulama"""
        self.validate_profile_item()
        self.calculate_total_length()
    
    def validate_profile_item(self):
        """Profil ürününü doğrula"""
        if not self.item_code:
            frappe.throw(_("Profil kodu boş olamaz."), title=_("Doğrulama Hatası"))
        
        # Ürünün profil olup olmadığını kontrol et
        item_group = frappe.db.get_value("Item", self.item_code, "item_group")
        if not is_profile_item_group(item_group):
            frappe.throw(_("{0} ürünü profil değildir. Sadece profil gruplarındaki ürünler scrap olarak eklenebilir.").format(
                self.item_code), title=_("Doğrulama Hatası"))
    
    def calculate_total_length(self):
        """Toplam uzunluğu hesapla"""
        if self.length and self.qty:
            # Import sırasında length float olarak gelebilir, string'e çevir
            self.length = normalize_length_to_string(self.length)
            
            # Boy değerini Boy DocType'ından al
            length_value = get_length_value_from_boy_doctype(self.length)
            self.total_length = flt(length_value) * self.qty
        else:
            self.total_length = 0
    
    def on_submit(self):
        """Profile Stock Ledger'a parça kaydı ekle (toplam stoklara dahil edilmez)"""
        try:
            # Scrap stok güncelle (length artık Link tipinde)
            update_profile_stock(
                item_code=self.item_code,
                length=self.length,
                qty=self.qty,
                action="add",
                is_scrap_piece=1
            )
            
            # Başarı mesajı
            frappe.msgprint(
                f"✅ Scrap profil stoku başarıyla eklendi!\n"
                f"📦 Profil: {self.item_code}\n"
                f"📏 Boy: {self.length}\n"
                f"🔢 Adet: {self.qty}\n"
                f"📊 Toplam: {self.total_length:.3f} m\n",
                title=_("Scrap Stok Ekleme Başarılı"),
                indicator="green"
            )
            
            # Log kaydı
            frappe.logger().info(f"Scrap Profile Entry: {self.item_code} {self.length} {self.qty}adet scrap stok eklendi.")
            
        except Exception as e:
            frappe.log_error(f"Scrap Profile Entry on_submit hatası: {str(e)}", "Scrap Profile Entry Submit Error")
            frappe.throw(f"Scrap profil stok ekleme sırasında hata oluştu: {str(e)}", title=_("Sistem Hatası"))
    
    def on_cancel(self):
        """Scrap profil girişi iptal edildiğinde stok geri al"""
        try:
            # Scrap stok geri al (length artık Link tipinde)
            update_profile_stock(
                item_code=self.item_code,
                length=self.length,
                qty=self.qty,
                action="subtract",
                is_scrap_piece=1
            )
            
            # Başarı mesajı
            frappe.msgprint(
                f"✅ Scrap profil stoku başarıyla geri alındı!\n"
                f"📦 Profil: {self.item_code}\n"
                f"📏 Boy: {self.length}\n"
                f"🔢 Adet: {self.qty}",
                title=_("Scrap Stok Geri Alma Başarılı"),
                indicator="green"
            )
            
            # Log kaydı
            frappe.logger().info(f"Scrap Profile Entry Cancel: {self.item_code} {self.length} {self.qty}adet scrap stok geri alındı")
            
        except Exception as e:
            frappe.log_error(f"Scrap Profile Entry on_cancel hatası: {str(e)}", "Scrap Profile Entry Cancel Error")
            frappe.throw(f"Scrap profil stok geri alma sırasında hata oluştu: {str(e)}", title=_("Sistem Hatası")) 