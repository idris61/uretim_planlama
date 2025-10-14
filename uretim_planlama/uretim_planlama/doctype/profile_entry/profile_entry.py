# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger import update_profile_stock
from uretim_planlama.uretim_planlama.utils import (
    log_profile_operation, show_operation_result,
    normalize_length_to_string, get_length_value_from_boy_doctype,
    is_profile_item_group
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
				if not is_profile_item_group(item_group):
					frappe.throw(_("Satır {0}: {1} ürünü profil değildir. Sadece profil gruplarındaki ürünler eklenebilir.").format(
						item.idx, item.item_code), title=_("Doğrulama Hatası"))
	
	def calculate_totals(self):
		"""Toplam uzunlukları hesapla"""
		total_length = 0
		total_qty = 0
		
		for item in self.items:
			# Import sırasında length float olarak gelebilir, string'e çevir
			item.length = normalize_length_to_string(item.length)
			
			# Boy değerini Boy DocType'ından al
			length_value = get_length_value_from_boy_doctype(item.length)
			if not length_value:
				length_value = flt(item.length)  # Fallback: direkt item.length'den al
			item.total_length = flt(length_value) * flt(item.received_quantity)
			total_length += flt(item.total_length)
			total_qty += flt(item.received_quantity)
		
		# Ana dokümana toplam değerleri ekle
		self.total_received_length = total_length
		self.total_received_qty = total_qty
	
	def copy_item_details_to_main(self):
		"""İlk item'ın bilgilerini ana dokümana kopyala (liste görünümü için)"""
		if self.items and len(self.items) > 0:
			first_item = self.items[0]
			self.item_code = first_item.item_code
			self.received_quantity = first_item.received_quantity
			self.length = first_item.length
		else:
			self.item_code = None
			self.received_quantity = 0
			self.length = None
	
	def before_save(self):
		"""Kaydetmeden önce toplam değerleri hesapla ve item bilgilerini ana dokümana kopyala"""
		self.calculate_totals()
		self.copy_item_details_to_main()
	
	def on_submit(self):
		"""Giriş onaylandığında stok artır"""
		# Toplam değerleri hesapla (import sırasında da gerekli)
		self.calculate_totals()
		
		# Import sırasında stok güncelleme yapma - çünkü stok zaten güncellenmiş
		if frappe.flags.in_import:
			return
			
		success_count = 0
		error_count = 0
		
		for item in self.items:
			try:
				# Gerekli alanları kontrol et
				if not item.length:
					frappe.throw(_(f"Satır {item.idx}: Boy (Length) alanı boş olamaz"))
				if not item.item_code:
					frappe.throw(_(f"Satır {item.idx}: Ürün Kodu (Item Code) boş olamaz"))
				
				# Stok güncelle (length artık Link tipinde)
				update_profile_stock(
					item_code=item.item_code,
					length=item.length,
					qty=item.received_quantity,
					action="add"
				)
				
				success_count += 1
				log_profile_operation("Entry", item.item_code, item.length, item.received_quantity, "in")
				
			except Exception as e:
				error_count += 1
				# Import sırasında database bağlantısı kopabiliyor, güvenli loglama
				try:
					frappe.log_error(f"Profile Entry stok güncelleme hatası: {str(e)}", "Profile Entry Stock Error")
				except:
					# Database bağlantısı yoksa sadece print ile logla
					print(f"Profile Entry stok güncelleme hatası: {str(e)}")
		
		# Sonuç bildirimi
		show_operation_result(success_count, error_count, self.total_received_length, self.total_received_qty, "Entry")

	def on_cancel(self):
		"""Giriş iptal edildiğinde stok azalt (geri al)"""
		try:
			success_count = 0
			error_count = 0
			
			for item in self.items:
				try:
					# Stok güncelle (geri al) - length artık Link tipinde
					update_profile_stock(
						item_code=item.item_code,
						length=item.length,
						qty=item.received_quantity,
						action="subtract"
					)
					
					success_count += 1
					log_profile_operation("Entry Cancel", item.item_code, item.length, item.received_quantity, "out")
					
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
