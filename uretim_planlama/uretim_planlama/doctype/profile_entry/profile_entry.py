# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger import update_profile_stock
from uretim_planlama.uretim_planlama.utils import (
    parse_length, validate_profile_item, calculate_total_length, 
    log_profile_operation, show_operation_result,
    parse_and_format_length
)
from frappe import _

class ProfileEntry(Document):
	def validate(self):
		"""Profil girişi doğrulama"""
		self.validate_items()
		self.calculate_totals()
	
	def validate_items(self):
		"""Satır öğelerini doğrula"""
		if not self.items:
			frappe.throw(_("En az bir ürün satırı eklenmelidir."), title=_("Doğrulama Hatası"))
		
		for item in self.items:
			if not item.item_code:
				frappe.throw(_("Satır {0}: Ürün kodu boş olamaz.").format(item.idx), title=_("Doğrulama Hatası"))
			
			if not item.length:
				frappe.throw(_("Satır {0}: Boy bilgisi boş olamaz.").format(item.idx), title=_("Doğrulama Hatası"))
			
			if not item.received_quantity or item.received_quantity < 1:
				frappe.throw(_("Satır {0}: Geçersiz adet bilgisi. Minimum 1 olmalıdır.").format(item.idx), title=_("Doğrulama Hatası"))
			
			# Ürünün profil olup olmadığını kontrol et (yalnızca manuel girişlerde)
			if not getattr(self.flags, 'bypass_group_check', False):
				item_group = frappe.db.get_value("Item", item.item_code, "item_group")
				allowed_groups = [
					'PVC', 'Camlar', 
					'Pvc Hat1 Ana Profiller', 'Pvc Hat2 Ana Profiller', 'Destek Sacı, Profiller',
					'Pvc Destek Sacları', 'Pvc Hat1 Destek Sacları', 'Pvc Hat1 Yardımcı Profiller',
					'Pvc Hat2 Yardımcı Profiller', 'Yardımcı Profiller'
				]
				if item_group not in allowed_groups:
					frappe.throw(_("Satır {0}: {1} ürünü profil değildir. Sadece profil gruplarındaki ürünler eklenebilir.").format(
						item.idx, item.item_code), title=_("Doğrulama Hatası"))
	
	def calculate_totals(self):
		"""Toplam uzunlukları hesapla"""
		total_length = 0
		total_qty = 0
		
		for item in self.items:
			# Boy değerini float'a çevir ve standart formata getir
			length_float, fixed_str = parse_and_format_length(item.length, decimals=1)
			item.length = fixed_str
			item.total_length = length_float * item.received_quantity
			total_length += item.total_length
			total_qty += item.received_quantity
		
		# Ana dokümana toplam değerleri ekle
		self.total_received_length = total_length
		self.total_received_qty = total_qty
	
	
	def before_save(self):
		"""Kaydetmeden önce işlemler"""
		self.calculate_totals()
	
	def on_submit(self):
		"""Giriş onaylandığında stok artır"""
		try:
			success_count = 0
			error_count = 0
			
			for item in self.items:
				try:
					# Boy değerini float'a çevir ve standart formata getir
					length_float, fixed_str = parse_and_format_length(item.length, decimals=1)
					item.length = fixed_str
					
					# Stok güncelle
					update_profile_stock(
						profile_type=item.item_code,
						length=length_float,
						qty=item.received_quantity,
						action="add"
					)
					
					success_count += 1
					
					# Log kaydı
					frappe.logger().info(f"Profile Entry: {item.item_code} {length_float}m {item.received_quantity}adet stok girişi yapıldı")
					
				except Exception as e:
					error_count += 1
					frappe.log_error(f"Profile Entry stok güncelleme hatası: {str(e)}", "Profile Entry Stock Error")
			
			# Sonuç bildirimi
			if error_count == 0:
				frappe.msgprint(
					f"✅ Profil stokları başarıyla güncellendi!\n"
					f"📊 Toplam {success_count} satır işlendi\n"
					f"📏 Toplam uzunluk: {self.total_received_length:.3f} m\n"
					f"📦 Toplam adet: {self.total_received_qty}",
					title=_("Stok Güncelleme Başarılı"),
					indicator="green"
				)
			else:
				frappe.msgprint(
					f"⚠️ Profil stok güncellemesi kısmen başarısız!\n"
					f"✅ Başarılı: {success_count} satır\n"
					f"❌ Hatalı: {error_count} satır\n"
					f"📋 Hata detayları için logları kontrol edin",
					title=_("Stok Güncelleme Kısmen Başarısız"),
					indicator="orange"
				)
				
		except Exception as e:
			frappe.log_error(f"Profile Entry on_submit hatası: {str(e)}", "Profile Entry Submit Error")
			frappe.throw(f"Profil stok güncellemesi sırasında hata oluştu: {str(e)}", title=_("Sistem Hatası"))

	def on_cancel(self):
		"""Giriş iptal edildiğinde stok azalt (geri al)"""
		try:
			success_count = 0
			error_count = 0
			
			for item in self.items:
				try:
					# Boy değerini float'a çevir ve standart formata getir
					length_float, fixed_str = parse_and_format_length(item.length, decimals=1)
					item.length = fixed_str
					
					# Stok güncelle (geri al)
					update_profile_stock(
						profile_type=item.item_code,
						length=length_float,
						qty=item.received_quantity,
						action="subtract"
					)
					
					success_count += 1
					
					# Log kaydı
					frappe.logger().info(f"Profile Entry Cancel: {item.item_code} {length_float}m {item.received_quantity}adet stok geri alındı")
					
				except Exception as e:
					error_count += 1
					frappe.log_error(f"Profile Entry cancel stok hatası: {str(e)[:100]}", "Profile Entry Cancel Error")
			
			# Sonuç bildirimi
			if error_count == 0:
				frappe.msgprint(
					f"✅ Profil stokları başarıyla geri alındı!\n"
					f"📊 Toplam {success_count} satır işlendi",
					title=_("Stok Geri Alma Başarılı"),
					indicator="green"
				)
			else:
				frappe.msgprint(
					f"⚠️ Profil stok geri alma işlemi kısmen başarısız!\n"
					f"✅ Başarılı: {success_count} satır\n"
					f"❌ Hatalı: {error_count} satır",
					title=_("Stok Geri Alma Kısmen Başarısız"),
					indicator="orange"
				)
				
		except Exception as e:
			frappe.log_error(f"Profile Entry on_cancel hatası: {str(e)[:100]}", "Profile Entry Cancel Error")
			frappe.throw(f"Profil stok geri alma hatası: {str(e)[:100]}", title=_("Sistem Hatası"))
