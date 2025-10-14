# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger import update_profile_stock
from uretim_planlama.uretim_planlama.utils import (
    validate_profile_item, log_profile_operation, show_operation_result,
    normalize_length_to_string, get_length_value_from_boy_doctype,
    get_profile_stock
)
from frappe import _

class ProfileExit(Document):
	def validate(self):
		"""Profil çıkışı doğrulama"""
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
			
			if not item.output_quantity or item.output_quantity < 1:
				frappe.throw(_("Satır {0}: Geçersiz çıkış adedi. Minimum 1 olmalıdır.").format(item.idx), title=_("Doğrulama Hatası"))
			
			# Ürünün profil olup olmadığını kontrol et
			validate_profile_item(item.item_code, item.idx)
	
	def calculate_totals(self):
		"""Toplam uzunlukları hesapla"""
		total_length = 0
		total_qty = 0
		
		for item in self.items:
			try:
				# Import sırasında length float olarak gelebilir, string'e çevir
				item.length = normalize_length_to_string(item.length)
				
				# Boy değerini Boy DocType'ından al
				length_value = get_length_value_from_boy_doctype(item.length)
				if not length_value:
					length_value = flt(item.length)  # Fallback: direkt item.length'den al
				item.total_length = flt(length_value) * flt(item.output_quantity or 0)
				total_length += item.total_length
				total_qty += flt(item.output_quantity or 0)
			except Exception as e:
				frappe.throw(_("Satır {0}: {1}").format(item.idx, str(e)), title=_("Hesaplama Hatası"))
		
		# Ana dokümana toplam değerleri ekle
		self.total_output_length = total_length
		self.total_output_qty = total_qty
	
	def copy_item_details_to_main(self):
		"""İlk item'ın bilgilerini ana dokümana kopyala (liste görünümü için)"""
		if self.items and len(self.items) > 0:
			first_item = self.items[0]
			self.item_code = first_item.item_code
			self.issued_quantity = first_item.output_quantity
			self.length = first_item.length
		else:
			self.item_code = None
			self.issued_quantity = 0
			self.length = None
	
	def before_save(self):
		"""Kaydetmeden önce toplam değerleri hesapla ve item bilgilerini ana dokümana kopyala"""
		self.calculate_totals()
		self.copy_item_details_to_main()
	
	def before_submit(self):
		"""Submit öncesi stok kontrolü yap"""
		self.check_stock_availability()
	
	def check_stock_availability(self):
		"""Stok yeterliliğini kontrol et"""
		for item in self.items:
			try:
				# Import sırasında length float olarak gelebilir, string'e çevir
				item.length = normalize_length_to_string(item.length)
				
				# Boy değerini Boy DocType'ından al
				length_value = get_length_value_from_boy_doctype(item.length)
				
				# Mevcut stok kontrolü
				available_qty = get_profile_stock(item.item_code, length_value)
				
				if available_qty < item.output_quantity:
					frappe.throw(_("Satır {0}: Yetersiz stok! {1} {2}m profilden {3} adet çıkış yapılamaz. Mevcut stok: {4} adet").format(
						item.idx, item.item_code, length_value, item.output_quantity, available_qty), 
						title=_("Yetersiz Stok Hatası"))
						
			except Exception as e:
				frappe.throw(_("Satır {0}: {1}").format(item.idx, str(e)), title=_("Stok Kontrol Hatası"))
	
	def on_submit(self):
		"""Çıkış onaylandığında stok azalt"""
		# Toplam değerleri hesapla (import sırasında da gerekli)
		self.calculate_totals()
		
		# Import sırasında stok güncelleme yapma - çünkü stok zaten güncellenmiş
		if frappe.flags.in_import:
			return
			
		try:
			success_count = 0
			error_count = 0
			
			for item in self.items:
				try:
					# Stok güncelle (length artık Link tipinde)
					update_profile_stock(
						item_code=item.item_code,
						length=item.length,
						qty=item.output_quantity,
						action="subtract"
					)
					
					success_count += 1
					log_profile_operation("Exit", item.item_code, item.length, item.output_quantity, "out")
					
				except Exception as e:
					error_count += 1
					# Import sırasında database bağlantısı kopabiliyor, güvenli loglama
					try:
						frappe.log_error(f"Profile Exit stok güncelleme hatası: {str(e)}", "Profile Exit Stock Error")
					except:
						# Database bağlantısı yoksa sadece print ile logla
						print(f"Profile Exit stok güncelleme hatası: {str(e)}")
			
			# Sonuç bildirimi
			show_operation_result(success_count, error_count, self.total_output_length, self.total_output_qty, "Exit")
				
		except Exception as e:
			# Import sırasında database bağlantısı kopabiliyor, güvenli loglama
			try:
				frappe.log_error(f"Profile Exit on_submit hatası: {str(e)}", "Profile Exit Submit Error")
			except:
				# Database bağlantısı yoksa sadece print ile logla
				print(f"Profile Exit on_submit hatası: {str(e)}")
			frappe.throw(f"Profil stok güncellemesi sırasında hata oluştu: {str(e)}", title=_("Sistem Hatası"))

	def on_cancel(self):
		"""Çıkış iptal edildiğinde stok geri ekle"""
		try:
			success_count = 0
			error_count = 0
			
			for item in self.items:
				try:
					# Stok güncelle (geri ekle) - length artık Link tipinde
					update_profile_stock(
						item_code=item.item_code,
						length=item.length,
						qty=item.output_quantity,
						action="add"
					)
					
					success_count += 1
					log_profile_operation("Exit Cancel", item.item_code, item.length, item.output_quantity, "in")
					
				except Exception as e:
					error_count += 1
					frappe.log_error(f"Profile Exit cancel stok güncelleme hatası: {str(e)}", "Profile Exit Cancel Stock Error")
			
			# Sonuç bildirimi (cancel için özel mesaj - geri ekleme)
			if error_count == 0:
				frappe.msgprint(
					f"✅ Profil stokları başarıyla geri eklendi!\n"
					f"📊 Toplam {success_count} satır işlendi",
					title=_("Stok Geri Ekleme Başarılı"),
					indicator="green"
				)
			else:
				frappe.msgprint(
					f"⚠️ Profil stok geri ekleme işlemi kısmen başarısız!\n"
					f"✅ Başarılı: {success_count} satır\n"
					f"❌ Hatalı: {error_count} satır",
					title=_("Stok Geri Ekleme Kısmen Başarısız"),
					indicator="orange"
				)
				
		except Exception as e:
			frappe.log_error(f"Profile Exit on_cancel hatası: {str(e)}", "Profile Exit Cancel Error")
			frappe.throw(f"Profil stok geri ekleme işlemi sırasında hata oluştu: {str(e)}", title=_("Sistem Hatası"))
