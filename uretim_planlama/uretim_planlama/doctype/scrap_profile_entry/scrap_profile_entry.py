# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger import update_profile_stock
from frappe import _

class ScrapProfileEntry(Document):
    def validate(self):
        """Scrap profil girişi doğrulama"""
        self.validate_profile_item()
        self.validate_scrap_reason()
        self.calculate_total_length()
    
    def validate_profile_item(self):
        """Profil ürününü doğrula"""
        if not self.profile_code:
            frappe.throw(_("Profil kodu boş olamaz."), title=_("Doğrulama Hatası"))
        
        # Ürünün profil olup olmadığını kontrol et
        item_group = frappe.db.get_value("Item", self.profile_code, "item_group")
        if item_group not in ['PVC', 'Camlar']:
            frappe.throw(_("{0} ürünü profil değildir. Sadece PVC ve Camlar grubundaki ürünler scrap olarak eklenebilir.").format(
                self.profile_code), title=_("Doğrulama Hatası"))
    
    def validate_scrap_reason(self):
        """Scrap nedenini doğrula"""
        if not self.scrap_reason:
            frappe.throw(_("Scrap nedeni belirtilmelidir."), title=_("Doğrulama Hatası"))
    
    def calculate_total_length(self):
        """Toplam uzunluğu hesapla"""
        if self.length and self.qty:
            try:
                length_float = float(str(self.length).replace(' m', '').replace(',', '.'))
                self.total_length = length_float * int(self.qty)
            except ValueError:
                frappe.throw(_("Geçersiz boy formatı: {0}").format(self.length), title=_("Doğrulama Hatası"))
        else:
            self.total_length = 0
    
    
    def before_save(self):
        """Kaydetmeden önce işlemler"""
        self.calculate_total_length()
    
    def on_submit(self):
        """Profile Stock Ledger'a parça kaydı ekle (toplam stoklara dahil edilmez)"""
        try:
            # Boy değerini float'a çevir
            length_float = float(str(self.length).replace(' m', '').replace(',', '.'))
            
            # Scrap stok güncelle
            update_profile_stock(
                profile_type=self.profile_code,
                length=length_float,
                qty=self.qty,
                action="in",
                is_scrap_piece=1
            )
            
            # Başarı mesajı
            frappe.msgprint(
                f"✅ Scrap profil stoku başarıyla eklendi!\n"
                f"📦 Profil: {self.profile_code}\n"
                f"📏 Boy: {length_float} m\n"
                f"🔢 Adet: {self.qty}\n"
                f"📊 Toplam: {self.total_length:.3f} m\n"
                f"🏷️ Neden: {self.scrap_reason}",
                title=_("Scrap Stok Ekleme Başarılı"),
                indicator="green"
            )
            
            # Log kaydı
            frappe.logger().info(f"Scrap Profile Entry: {self.profile_code} {length_float}m {self.qty}adet scrap stok eklendi. Neden: {self.scrap_reason}")
            
        except Exception as e:
            frappe.log_error(f"Scrap Profile Entry on_submit hatası: {str(e)}", "Scrap Profile Entry Submit Error")
            frappe.throw(f"Scrap profil stok ekleme sırasında hata oluştu: {str(e)}", title=_("Sistem Hatası"))
    
    def on_cancel(self):
        """Scrap profil girişi iptal edildiğinde stok geri al"""
        try:
            # Boy değerini float'a çevir
            length_float = float(str(self.length).replace(' m', '').replace(',', '.'))
            
            # Scrap stok geri al
            update_profile_stock(
                profile_type=self.profile_code,
                length=length_float,
                qty=self.qty,
                action="out",
                is_scrap_piece=1
            )
            
            # Başarı mesajı
            frappe.msgprint(
                f"✅ Scrap profil stoku başarıyla geri alındı!\n"
                f"📦 Profil: {self.profile_code}\n"
                f"📏 Boy: {length_float} m\n"
                f"🔢 Adet: {self.qty}",
                title=_("Scrap Stok Geri Alma Başarılı"),
                indicator="green"
            )
            
            # Log kaydı
            frappe.logger().info(f"Scrap Profile Entry Cancel: {self.profile_code} {length_float}m {self.qty}adet scrap stok geri alındı")
            
        except Exception as e:
            frappe.log_error(f"Scrap Profile Entry on_cancel hatası: {str(e)}", "Scrap Profile Entry Cancel Error")
            frappe.throw(f"Scrap profil stok geri alma sırasında hata oluştu: {str(e)}", title=_("Sistem Hatası")) 