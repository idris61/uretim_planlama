# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger import update_profile_stock, get_profile_stock
from frappe import _

class ProfileExit(Document):
	def validate(self):
		"""Profil çıkışı doğrulama"""
		self.validate_items()
		self.calculate_totals()
		self.validate_warehouse()
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
			item_group = frappe.db.get_value("Item", item.item_code, "item_group")
			if item_group not in ['PVC', 'Camlar']:
				frappe.throw(_("Satır {0}: {1} ürünü profil değildir. Sadece PVC ve Camlar grubundaki ürünler çıkış yapılabilir.").format(
					item.idx, item.item_code), title=_("Doğrulama Hatası"))
	
	def calculate_totals(self):
		"""Toplam uzunlukları hesapla"""
		total_length = 0
		total_qty = 0
		
		for item in self.items:
			try:
				# Boy değerini float'a çevir
				length_float = float(str(item.length).replace(' m', '').replace(',', '.'))
				item.total_length = length_float * item.output_quantity
				total_length += item.total_length
				total_qty += item.output_quantity
			except ValueError:
				frappe.throw(_("Satır {0}: Geçersiz boy formatı: {1}").format(item.idx, item.length), title=_("Doğrulama Hatası"))
		
		# Ana dokümana toplam değerleri ekle
		self.total_output_length = total_length
		self.total_output_qty = total_qty
	
	def validate_warehouse(self):
		"""Depo bilgisini doğrula"""
		if not self.warehouse:
			# Varsayılan depo ayarla
			default_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
			if default_warehouse:
				self.warehouse = default_warehouse
			else:
				frappe.throw(_("Depo bilgisi belirtilmelidir."), title=_("Doğrulama Hatası"))
	
	def check_stock_availability(self):
		"""Stok yeterliliğini kontrol et"""
		for item in self.items:
			try:
				# Boy değerini float'a çevir
				length_float = float(str(item.length).replace(' m', '').replace(',', '.'))
				
				# Mevcut stok kontrolü
				available_stock = get_profile_stock(item.item_code)
				available_qty = 0
				
				for stock in available_stock:
					if stock.length == length_float:
						available_qty = stock.qty
						break
				
				if available_qty < item.output_quantity:
					frappe.throw(_("Satır {0}: Yetersiz stok! {1} {2}m profilden {3} adet çıkış yapılamaz. Mevcut stok: {4} adet").format(
						item.idx, item.item_code, length_float, item.output_quantity, available_qty), 
						title=_("Yetersiz Stok Hatası"))
						
			except ValueError:
				frappe.throw(_("Satır {0}: Geçersiz boy formatı: {1}").format(item.idx, item.length), title=_("Doğrulama Hatası"))
	
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
					# Boy değerini float'a çevir
					length_float = float(str(item.length).replace(' m', '').replace(',', '.'))
					
					# Stok güncelle
					update_profile_stock(
						profile_type=item.item_code,
						length=length_float,
						qty=item.output_quantity,
						action="out"
					)
					
					success_count += 1
					
					# Log kaydı
					frappe.logger().info(f"Profile Exit: {item.item_code} {length_float}m {item.output_quantity}adet stok çıkışı yapıldı")
					
				except Exception as e:
					error_count += 1
					frappe.log_error(f"Profile Exit stok güncelleme hatası: {str(e)}", "Profile Exit Stock Error")
			
			# Sonuç bildirimi
			if error_count == 0:
				frappe.msgprint(
					f"✅ Profil stokları başarıyla güncellendi!\n"
					f"📊 Toplam {success_count} satır işlendi\n"
					f"📏 Toplam uzunluk: {self.total_output_length:.3f} m\n"
					f"📦 Toplam adet: {self.total_output_qty}",
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
			frappe.log_error(f"Profile Exit on_submit hatası: {str(e)}", "Profile Exit Submit Error")
			frappe.throw(f"Profil stok güncellemesi sırasında hata oluştu: {str(e)}", title=_("Sistem Hatası"))

	def on_cancel(self):
		"""Çıkış iptal edildiğinde stok geri ekle"""
		try:
			success_count = 0
			error_count = 0
			
			for item in self.items:
				try:
					# Boy değerini float'a çevir
					length_float = float(str(item.length).replace(' m', '').replace(',', '.'))
					
					# Stok güncelle (geri ekle)
					update_profile_stock(
						profile_type=item.item_code,
						length=length_float,
						qty=item.output_quantity,
						action="in"
					)
					
					success_count += 1
					
					# Log kaydı
					frappe.logger().info(f"Profile Exit Cancel: {item.item_code} {length_float}m {item.output_quantity}adet stok geri eklendi")
					
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
