# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger import update_profile_stock, get_profile_stock
from uretim_planlama.uretim_planlama.utils import (
    parse_length, validate_profile_item, calculate_total_length, 
    validate_warehouse, log_profile_operation, show_operation_result
)
from frappe import _

class ProfileExit(Document):
	def validate(self):
		"""Profil çıkışı doğrulama"""
		self.validate_items()
		self.calculate_totals()
		self.warehouse = validate_warehouse(self.warehouse)
		self.check_stock_availability()
	
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
				# Boy uzunluğunu güvenle hesapla: önce total_length/qty, yoksa field'dan parse
				if getattr(item, "total_length", 0) and getattr(item, "output_quantity", 0):
					length_float = float(item.total_length) / float(item.output_quantity)
				else:
					length_float = parse_length(item.length)
				item.total_length = calculate_total_length(length_float, item.output_quantity)
				total_length += item.total_length
				total_qty += item.output_quantity
			except Exception as e:
				frappe.throw(_("Satır {0}: {1}").format(item.idx, str(e)), title=_("Hesaplama Hatası"))
		
		# Ana dokümana toplam değerleri ekle
		self.total_output_length = total_length
		self.total_output_qty = total_qty
	
	def check_stock_availability(self):
		"""Stok yeterliliğini kontrol et"""
		for item in self.items:
			try:
				# Boy uzunluğunu güvenle hesapla: önce total_length/qty, yoksa field'dan parse
				if getattr(item, "total_length", 0) and getattr(item, "output_quantity", 0):
					length_float = float(item.total_length) / float(item.output_quantity)
				else:
					length_float = parse_length(item.length)
				
				# Mevcut stok kontrolü
				available_qty = get_profile_stock(item.item_code, length_float)
				
				if available_qty < item.output_quantity:
					frappe.throw(_("Satır {0}: Yetersiz stok! {1} {2}m profilden {3} adet çıkış yapılamaz. Mevcut stok: {4} adet").format(
						item.idx, item.item_code, length_float, item.output_quantity, available_qty), 
						title=_("Yetersiz Stok Hatası"))
						
			except Exception as e:
				frappe.throw(_("Satır {0}: {1}").format(item.idx, str(e)), title=_("Stok Kontrol Hatası"))
	
	def before_save(self):
		"""Kaydetmeden önce işlemler"""
		self.calculate_totals()
	
	def on_submit(self):
		"""Çıkış onaylandığında stok azalt"""
		try:
			success_count = 0
			error_count = 0
			
			for item in self.items:
				try:
					# Boy uzunluğunu güvenle hesapla: önce total_length/qty, yoksa field'dan parse
					if getattr(item, "total_length", 0) and getattr(item, "output_quantity", 0):
						length_float = float(item.total_length) / float(item.output_quantity)
					else:
						length_float = parse_length(item.length)
					
					# Stok güncelle
					update_profile_stock(
						profile_type=item.item_code,
						length=length_float,
						qty=item.output_quantity,
						action="subtract"
					)
					
					success_count += 1
					log_profile_operation("Exit", item.item_code, length_float, item.output_quantity, "out")
					
				except Exception as e:
					error_count += 1
					frappe.log_error(f"Profile Exit stok güncelleme hatası: {str(e)}", "Profile Exit Stock Error")
			
			# Sonuç bildirimi
			show_operation_result(success_count, error_count, self.total_output_length, self.total_output_qty, "Exit")
				
		except Exception as e:
			frappe.log_error(f"Profile Exit on_submit hatası: {str(e)}", "Profile Exit Submit Error")
			frappe.throw(f"Profil stok güncellemesi sırasında hata oluştu: {str(e)}", title=_("Sistem Hatası"))

	def on_cancel(self):
		"""Çıkış iptal edildiğinde stok geri ekle"""
		try:
			success_count = 0
			error_count = 0
			
			for item in self.items:
				try:
					length_float = parse_length(item.length)
					
					# Stok güncelle (geri ekle)
					update_profile_stock(
						profile_type=item.item_code,
						length=length_float,
						qty=item.output_quantity,
						action="add"
					)
					
					success_count += 1
					log_profile_operation("Exit Cancel", item.item_code, length_float, item.output_quantity, "in")
					
				except Exception as e:
					error_count += 1
					frappe.log_error(f"Profile Exit cancel stok güncelleme hatası: {str(e)}", "Profile Exit Cancel Stock Error")
			
			# Sonuç bildirimi
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
