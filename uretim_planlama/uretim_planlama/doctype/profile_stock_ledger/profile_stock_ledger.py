# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document

# Reorder fonksiyonu için import
from uretim_planlama.uretim_planlama.api.reorder import ensure_reorder_for_profile
from uretim_planlama.uretim_planlama.utils import (
    normalize_length_to_string, get_length_value_from_boy_doctype, is_profile_item_group
)


def on_doctype_update():
	"""DocType güncellendiğinde index ekle"""
	frappe.db.add_index("Profile Stock Ledger", ["item_code", "length", "is_scrap_piece"])
	frappe.db.add_index("Profile Stock Ledger", ["item_code", "length"])
	frappe.db.add_index("Profile Stock Ledger", ["item_code"])


class ProfileStockLedger(Document):
	"""Profile Stock Ledger DocType"""
	
	def validate(self):
		"""Doğrulama işlemleri"""
		try:
			# Temel validasyonlar
			if self.qty < 0:
				frappe.throw(_("Miktar negatif olamaz"))
			
			if not self.length:
				frappe.throw(_("Boy seçilmelidir"))
			
			if not self.item_code:
				frappe.throw(_("Ürün kodu boş olamaz"))
			
			# Import sırasında length float olarak gelebilir, string'e çevir
			self.length = normalize_length_to_string(self.length)
			
			# Boy değerini Boy DocType'ından al ve toplam uzunluk hesapla
			length_value = get_length_value_from_boy_doctype(self.length)
			if not length_value:
				frappe.throw(_("Boy değeri bulunamadı: {0}").format(self.length))
			
			self.total_length = flt(length_value) * flt(self.qty)
			
			# Item_code'dan item_name ve item_group bilgilerini otomatik doldur
			if self.item_code:
				item_data = frappe.db.get_value("Item", self.item_code, 
												["item_name", "item_group"], as_dict=True)
				if not item_data:
					frappe.throw(_("Ürün bulunamadı: {0}").format(self.item_code))
				
				if not self.item_name:
					self.item_name = item_data.item_name
				if not self.item_group:
					self.item_group = item_data.item_group
				
				# Profil ürünü kontrolü (import sırasında bypass edilebilir)
				if not frappe.flags.in_import and not is_profile_item_group(item_data.item_group):
					frappe.throw(_("Sadece profil ürünleri kaydedilebilir: {0}").format(item_data.item_group))
			
			# is_scrap_piece değerini normalize et
			self.is_scrap_piece = self.is_scrap_piece or 0
			
			# Unique constraint kontrolü (import sırasında bypass et)
			if not frappe.flags.in_import:
				self.validate_unique_constraint()
				
		except Exception as e:
			error_msg = f"Validation hatası: {str(e)}"
			frappe.log_error(error_msg, "Profile Stock Ledger Validation Error")
			frappe.throw(_(error_msg))
	
	def check_for_duplicates(self):
		"""Duplicate kayıt kontrolü - aynı kombinasyon var mı?"""
		length_str = normalize_length_to_string(self.length)
		
		existing_records = frappe.get_all(
			"Profile Stock Ledger",
			filters={
				"item_code": self.item_code,
				"length": length_str,
				"is_scrap_piece": self.is_scrap_piece or 0
			},
			fields=["name", "qty", "creation"],
			order_by="creation DESC"
		)
		
		# Eğer birden fazla kayıt varsa, duplicate var demektir - temizle
		if len(existing_records) > 1:
			self.cleanup_duplicate_records(existing_records)
		elif len(existing_records) == 1:
			# Tek kayıt var - duplicate değil ama mevcut kayıt var
			# Bu durumda normal insert işlemi devam edecek
			# Import değilse hata ver
			if not frappe.flags.in_import:
				frappe.throw(_(
					f"Aynı ürün ({self.item_code}) ve boy ({length_str}m) kombinasyonu zaten mevcut. "
					f"Lütfen mevcut kaydı güncelleyin veya farklı bir boy kullanın."
				))
	
	def before_insert(self):
		"""Kayıt oluşturulmadan önce kontrol et"""
		# Her durumda duplicate kontrolü yap
		self.check_for_duplicates()
		
		# Import sırasında skip flag'i varsa insert'i iptal et
		if getattr(self.flags, 'skip_insert', False):
			frappe.throw(_("Bu kayıt güncelleniyor, yeni kayıt oluşturulmayacak"))
		
		# Import sırasında özel işlem yap
		if frappe.flags.in_import:
			try:
				self.handle_import_record()
				# Import başarılı, bu kaydı insert etme
				self.flags.skip_insert = True
				# Hook'u sonlandır - insert işlemi yapılmayacak
				return
			except Exception as e:
				# Import hatası - database bağlantısı kopmuş olabilir
				error_msg = f"Import işlemi hatası: {str(e)}"
				try:
					frappe.logger().error(error_msg)
				except:
					# Database bağlantısı yoksa sadece print ile logla
					print(error_msg)
				raise e
		
		# Import değilse ve skip_insert flag'i varsa, insert'i iptal et
		if getattr(self.flags, 'skip_insert', False):
			frappe.throw(_("Bu kayıt güncelleniyor, yeni kayıt oluşturulmayacak"))
	
	def handle_import_record(self):
		"""Import sırasında kayıt işleme"""
		# Duplicate kontrolü - aynı item_code, length, is_scrap_piece kombinasyonu var mı?
		length_str = normalize_length_to_string(self.length)
		
		# Daha sıkı duplicate kontrolü - tüm kombinasyonları kontrol et
		existing_records = frappe.get_all(
			"Profile Stock Ledger",
			filters={
				"item_code": self.item_code,
				"length": length_str,
				"is_scrap_piece": self.is_scrap_piece or 0
			},
			fields=["name", "qty", "creation"],
			order_by="creation DESC"
		)
		
		# Eğer birden fazla kayıt varsa, duplicate var demektir - temizle
		if len(existing_records) > 1:
			self.cleanup_duplicate_records(existing_records)
			# Temizlik sonrası tekrar kontrol et
			existing_records = frappe.get_all(
				"Profile Stock Ledger",
				filters={
					"item_code": self.item_code,
					"length": length_str,
					"is_scrap_piece": self.is_scrap_piece or 0
				},
				fields=["name", "qty", "creation"],
				limit=1
			)
			existing_record = existing_records
		elif len(existing_records) == 1:
			existing_record = existing_records
		else:
			existing_record = []
		
		if existing_record:
			# Mevcut kayıt var - güncelle
			existing_name = existing_record[0].name
			old_qty = existing_record[0].qty
			new_qty = self.qty
			
			# Bu kayıt güncellenecek, yeni kayıt oluşturma
			self.flags.skip_insert = True
			
			# Eğer yeni miktar 0 ise, mevcut kaydı sil ve Profile Exit oluştur
			if new_qty == 0:
				# Güvenli loglama
				try:
					frappe.logger().info(
						f"Import: Stok silme - {self.item_code} {length_str} "
						f"Mevcut: {old_qty} adet, Profile Exit oluşturulacak"
					)
				except:
					print(f"Import: Stok silme - {self.item_code} {length_str} "
						f"Mevcut: {old_qty} adet, Profile Exit oluşturulacak")
				
				# Profile Exit oluştur (stok çıkışı)
				try:
					self.create_stock_adjustment_entry(existing_name, length_str, -old_qty, old_qty, 0)
				except Exception as e:
					# Güvenli loglama
					try:
						frappe.logger().warning(f"Profile Exit oluşturulamadı: {str(e)}")
					except:
						print(f"❌ Profile Exit oluşturulamadı: {str(e)}")
				
				# Mevcut kaydı sil
				frappe.delete_doc("Profile Stock Ledger", existing_name, force=1)
				
			else:
				# Stok farkını hesapla
				stock_difference = new_qty - old_qty
				
				# Güvenli loglama
				try:
					frappe.logger().info(
						f"Import: Mevcut kayıt güncellendi: {self.item_code} {length_str} "
						f"Mevcut: {old_qty} → Yeni: {new_qty} (Fark: {stock_difference:+d})"
					)
				except:
					print(f"Import: Mevcut kayıt güncellendi: {self.item_code} {length_str} Mevcut: {old_qty} → Yeni: {new_qty} (Fark: {stock_difference:+d})")
				
				# Mevcut kaydı güncelle
				frappe.db.set_value("Profile Stock Ledger", existing_name, {
					"qty": new_qty,
					"total_length": self.total_length or 0,
					"item_name": self.item_name,
					"item_group": self.item_group
				})
				
				# Stok farkı için Profile Entry/Exit oluştur
				if stock_difference != 0:
					try:
						self.create_stock_adjustment_entry(existing_name, length_str, stock_difference, old_qty, new_qty)
					except Exception as e:
						# Güvenli loglama
						try:
							frappe.logger().warning(f"Profile Entry/Exit oluşturulamadı: {str(e)}")
						except:
							print(f"Profile Entry/Exit oluşturulamadı: {str(e)}")
		else:
			# Mevcut kayıt yok - Profile Entry ile yeni kayıt ekle
			# Bu kayıt Profile Entry ile oluşturulacak, yeni kayıt oluşturma
			self.flags.skip_insert = True
			
			try:
				frappe.logger().info(
					f"Import: Yeni kayıt - Profile Entry ile eklenecek: {self.item_code} {length_str} {self.qty} adet"
				)
			except:
				print(f"Import: Yeni kayıt - Profile Entry ile eklenecek: {self.item_code} {length_str} {self.qty} adet")
			
			# Profile Entry ile yeni kayıt ekle
			try:
				self.create_profile_entry_for_new_record(length_str)
				try:
					frappe.logger().info(f"Profile Entry başarıyla oluşturuldu: {self.item_code} {length_str}")
				except:
					print(f"Profile Entry başarıyla oluşturuldu: {self.item_code} {length_str}")
			except Exception as e:
				try:
					frappe.logger().error(f"Profile Entry oluşturulamadı: {str(e)}")
				except:
					print(f"Profile Entry oluşturulamadı: {str(e)}")
				raise e
	
	def after_insert(self):
		"""Kayıt oluşturulduktan sonra Profile Entry oluştur"""
		# Import sırasında yeni kayıt oluşturulmamalı - sadece mevcut kayıtlar güncellenir
		# Bu fonksiyon import sırasında çalışmamalı
		pass
	
	def cleanup_duplicate_records(self, duplicate_records):
		"""Duplicate kayıtları temizle - toplam miktarı en eski kayıtta birleştir"""
		if len(duplicate_records) <= 1:
			return
		
		# En eski kayıt (ilk kayıt) - bunu güncelleyeceğiz
		keep_record = duplicate_records[-1]  # En eski kayıt (creation ASC'de son)
		
		# Toplam miktarı hesapla
		total_qty = sum(record.qty for record in duplicate_records)
		
		# Boy değerini Boy DocType'ından al
		length_value = get_length_value_from_boy_doctype(self.length)
		if not length_value:
			length_value = flt(self.length)  # Fallback
		
		# En eski kayıtı toplam miktarla güncelle
		frappe.db.set_value('Profile Stock Ledger', keep_record.name, {
			'qty': total_qty,
			'total_length': flt(length_value) * flt(total_qty)
		})
		
		# Diğer duplicate kayıtları sil
		for record in duplicate_records[:-1]:  # En eski hariç diğerleri
			frappe.delete_doc("Profile Stock Ledger", record.name, force=1)
		
		# Loglama
		try:
			frappe.logger().info(
				f"Import: Duplicate temizlendi - {self.item_code} {self.length}m "
				f"Toplam: {total_qty} adet, {len(duplicate_records)-1} duplicate silindi"
			)
		except:
			print(f"Import: Duplicate temizlendi - {self.item_code} {self.length}m "
				f"Toplam: {total_qty} adet, {len(duplicate_records)-1} duplicate silindi")
	
	def create_stock_adjustment_entry(self, existing_name, length_str, stock_difference, old_qty, new_qty):
		"""Stok farkı için Profile Entry veya Exit oluştur"""
		try:
			if stock_difference > 0:
				# Ürün bilgilerini al
				item_info = frappe.db.get_value("Item", self.item_code, ["item_name", "item_group"], as_dict=True)
				if not item_info:
					frappe.throw(f"Ürün bulunamadı: {self.item_code}")
				
				# Boy değerini hesapla
				length_value = get_length_value_from_boy_doctype(length_str)
				if not length_value:
					frappe.throw(f"Boy değeri bulunamadı: {length_str}")
				
				total_length = flt(length_value) * flt(stock_difference)
				
				# Stok artışı - Profile Entry oluştur
				entry_doc = frappe.get_doc({
					"doctype": "Profile Entry",
					"date": frappe.utils.today(),
					"supplier": None,
					"remarks": f"Import Sayım Artışı - {frappe.session.user} | "
							f"Mevcut: {old_qty} → Yeni: {new_qty} | "
							f"Artış: +{stock_difference} adet",
					"items": [{
						"doctype": "Profile Entry Item",
						"item_code": self.item_code,
						"item_name": item_info.item_name,
						"item_group": item_info.item_group,
						"length": length_str,
						"received_quantity": stock_difference,
						"reference_doc": existing_name
					}]
				})
				
				entry_doc.flags.ignore_validate = True
				entry_doc.flags.ignore_permissions = True
				entry_doc.flags.bypass_group_check = True
				
				# Total değerleri hesapla ve set et
				entry_doc.calculate_totals()
				entry_doc.copy_item_details_to_main()
				
				entry_doc.insert()
				entry_doc.submit()
				
				frappe.logger().info(
					f"Import: Profile Entry oluşturuldu - {self.item_code} {length_str} "
					f"+{stock_difference} adet (Entry: {entry_doc.name})"
				)
				
			elif stock_difference < 0:
				# Ürün bilgilerini al
				item_info = frappe.db.get_value("Item", self.item_code, ["item_name", "item_group"], as_dict=True)
				if not item_info:
					frappe.throw(f"Ürün bulunamadı: {self.item_code}")
				
				# Boy değerini hesapla
				length_value = get_length_value_from_boy_doctype(length_str)
				if not length_value:
					frappe.throw(f"Boy değeri bulunamadı: {length_str}")
				
				total_length = flt(length_value) * flt(abs(stock_difference))
				
				# Stok azalışı - Profile Exit oluştur
				exit_doc = frappe.get_doc({
					"doctype": "Profile Exit",
					"date": frappe.utils.today(),
					"customer": None,
					"remarks": f"Import Sayım Azalışı - {frappe.session.user} | "
							f"Mevcut: {old_qty} → Yeni: {new_qty} | "
							f"Azalış: {stock_difference} adet",
					"items": [{
						"doctype": "Profile Exit Item",
						"item_code": self.item_code,
						"item_name": item_info.item_name,
						"item_group": item_info.item_group,
						"length": length_str,
						"output_quantity": abs(stock_difference),
						"reference_doc": existing_name
					}]
				})
				
				exit_doc.flags.ignore_validate = True
				exit_doc.flags.ignore_permissions = True
				exit_doc.flags.bypass_group_check = True
				
				# Total değerleri hesapla ve set et
				exit_doc.calculate_totals()
				exit_doc.copy_item_details_to_main()
				
				exit_doc.insert()
				exit_doc.submit()
				
				frappe.logger().info(
					f"Import: Profile Exit oluşturuldu - {self.item_code} {length_str} "
					f"{stock_difference} adet (Exit: {exit_doc.name})"
				)
				
		except Exception as e:
			error_msg = f"Stok ayarlama kaydı oluşturma hatası: {str(e)}"
			frappe.log_error(error_msg, "Stock Adjustment Entry Error")
			frappe.throw(_(error_msg))
	
	def create_profile_entry_for_new_record(self, length_str):
		"""Import sırasında yeni kayıt için Profile Entry oluştur"""
		try:
			# Ürün bilgilerini al
			item_info = frappe.db.get_value("Item", self.item_code, ["item_name", "item_group"], as_dict=True)
			if not item_info:
				frappe.throw(f"Ürün bulunamadı: {self.item_code}")
			
			# Boy değerini hesapla
			length_value = get_length_value_from_boy_doctype(length_str)
			if not length_value:
				frappe.throw(f"Boy değeri bulunamadı: {length_str}")
			
			total_length = flt(length_value) * flt(self.qty)
			
			# Profile Entry oluştur
			entry_doc = frappe.get_doc({
				"doctype": "Profile Entry",
				"date": frappe.utils.today(),
				"supplier": None,
				"reference_type": None,
				"reference_name": None,
				"remarks": f"Import: Yeni stok eklendi - {self.item_code} {length_str}m",
				"items": [{
					"item_code": self.item_code,
					"item_name": item_info.item_name,
					"item_group": item_info.item_group,
					"received_quantity": self.qty,
					"length": length_str,
					"is_scrap_piece": self.is_scrap_piece or 0
				}]
			})
			
			# Import sırasında validation'ları bypass et
			entry_doc.flags.ignore_validate = True
			entry_doc.flags.ignore_permissions = True
			entry_doc.flags.bypass_group_check = True
			
			# Manuel olarak toplam değerleri hesapla ve set et
			entry_doc.calculate_totals()
			
			# Insert öncesi total değerleri hesapla ve set et
			total_length = flt(length_value) * flt(self.qty)
			entry_doc.total_received_length = total_length
			entry_doc.total_received_qty = self.qty
			
			# Item bilgilerini ana dokümana kopyala
			entry_doc.copy_item_details_to_main()
			
			entry_doc.insert()
			entry_doc.submit()
			
			# Güvenli loglama
			try:
				frappe.logger().info(
					f"Import: Yeni stok Profile Entry ile eklendi - "
					f"{self.item_code} {length_str} - {self.qty} adet (Entry: {entry_doc.name})"
				)
			except:
				print(f"Import: Yeni stok Profile Entry ile eklendi - {self.item_code} {length_str} - {self.qty} adet (Entry: {entry_doc.name})")
			
		except Exception as e:
			error_msg = str(e)
			detail = f"Item Code: {self.item_code or 'BOŞ'}, Length: {length_str or 'BOŞ'}, Qty: {self.qty or 0}"
			# Güvenli loglama
			try:
				frappe.logger().warning(f"Profile Entry oluşturulamadı: {error_msg}\n{detail}")
			except:
				print(f"Profile Entry oluşturulamadı: {error_msg}\n{detail}")
			raise e
	
	def create_profile_exit_for_count_adjustment(self, item_code, length, exit_qty, old_stock, new_stock):
		"""Sayım güncellemesi için Profile Exit oluştur (stok azalması)"""
		try:
			exit_doc = frappe.get_doc({
				"doctype": "Profile Exit",
				"date": frappe.utils.today(),
				"customer": None,  # Sayım için müşteri bilgisi yok
				"remarks": f"Sayım Güncellemesi (Stok Azalması) - {frappe.session.user} | "
							f"Mevcut: {old_stock} adet → Yeni: {new_stock} adet | "
							f"Çıkış: {exit_qty} adet",
				"items": [{
					"doctype": "Profile Exit Item",
					"item_code": item_code,
					"length": length,
					"output_quantity": exit_qty,
					"reference_type": "Manual Entry",
					"reference_doc": None
				}]
			})
			
			# Validation'ları bypass et (import sırasında)
			exit_doc.flags.ignore_validate = True
			exit_doc.flags.ignore_permissions = True
			exit_doc.flags.bypass_group_check = True
			
			# Manuel olarak totals hesapla
			exit_doc.calculate_totals()
			
			exit_doc.insert()
			exit_doc.submit()
			
			frappe.logger().info(
				f"Profile Exit oluşturuldu (Sayım): {exit_doc.name} - "
				f"{item_code} {length} {exit_qty} adet çıkış"
			)
			
		except Exception as e:
			frappe.log_error(
				f"Profile Exit oluşturma hatası (Sayım): {str(e)}",
				"Profile Exit Count Error"
			)
			frappe.throw(_(f"Sayım için stok çıkışı oluşturulamadı: {str(e)}"))
	
	def validate_unique_constraint(self):
		"""Aynı profil tipi, boy ve scrap durumu için tek kayıt olmalı"""
		filters = {
			"item_code": self.item_code,
			"length": self.length,
			"is_scrap_piece": self.is_scrap_piece
		}
		
		if self.name:
			filters["name"] = ["!=", self.name]
		
		existing = frappe.get_all("Profile Stock Ledger", filters=filters, limit=1)
		if existing:
			frappe.throw(
				_("Bu profil tipi ({0}), boy ({1}m) ve parça durumu için zaten bir kayıt mevcut!").format(
					self.item_code, self.length
				),
				title=_("Duplicate Kayıt Hatası")
			)


def _check_reorder(item_code, length, qty):
	"""Reorder kontrolü yapar"""
	try:
		ensure_reorder_for_profile(item_code, float(length), float(qty))
	except Exception as e:
		frappe.log_error(f"Reorder ensure error: {item_code} {length} -> {e}", "Profile Reorder Ensure Error")


def update_profile_stock(item_code, length, qty, action, is_scrap_piece=0):
	"""
	Profile stok güncellemesi yapar.
	action: "add" veya "subtract"
	
	Bu fonksiyon duplicate kayıtları önlemek için:
	1. Mevcut kaydı bulur
	2. Varsa günceller, yoksa yeni oluşturur
	3. Unique constraint kontrolü yapar
	"""
	# Length normalize ve validate et
	length_name = normalize_length_to_string(length)
	length_value = get_length_value_from_boy_doctype(length_name)
	
	qty = flt(qty)
	
	# Mevcut stok kaydını bul - tüm kayıtları al (duplicate kontrolü için)
	existing_records = frappe.get_all(
		"Profile Stock Ledger",
		filters={
			"item_code": item_code,
			"length": length_name,
			"is_scrap_piece": is_scrap_piece
		},
		fields=["name", "qty"],
		order_by="creation desc"
	)
	
	if existing_records:
		# Duplicate kayıt varsa birleştir
		if len(existing_records) > 1:
			frappe.log_error(
				f"Duplicate Profile Stock Ledger kayıtları bulundu: {item_code} {length or 'None'}. Birleştiriliyor...",
				"Profile Stock Ledger Duplicate Fix"
			)
			_consolidate_duplicate_records(existing_records, item_code, length, is_scrap_piece)
			
			# Birleştirme sonrası tekrar al
			existing_records = frappe.get_all(
				"Profile Stock Ledger",
				filters={
					"item_code": item_code,
					"length": length,
					"is_scrap_piece": is_scrap_piece
				},
				fields=["name", "qty"],
				limit=1
			)
		
		# Mevcut kaydı güncelle
		doc = frappe.get_doc("Profile Stock Ledger", existing_records[0].name)
		old_qty = doc.qty
		
		if action == "add":
			doc.qty = flt(doc.qty) + qty
		elif action == "subtract":
			doc.qty = flt(doc.qty) - qty
		else:
			frappe.throw(f"Geçersiz action: {action}. Sadece 'add' veya 'subtract' kullanın.")
		
		if doc.qty <= 0:
			doc.delete()
			frappe.logger().info(f"Profile Stock Ledger kaydı silindi: {item_code} {length or 'None'} (qty: {old_qty} -> 0)")
			# Reorder kontrolü (sıfır stok için)
			_check_reorder(item_code, length, 0)
		else:
			doc.save()
			frappe.logger().info(f"Profile Stock Ledger güncellendi: {item_code} {length or 'None'} (qty: {old_qty} -> {doc.qty})")
			# Reorder kontrolü
			_check_reorder(item_code, length, doc.qty)
			
	else:
		# Yeni kayıt oluştur
		if action == "add":
			# Item'dan item_name ve item_group bilgilerini al
			item_data = frappe.db.get_value("Item", item_code, 
											["item_name", "item_group"], as_dict=True)
			
			doc = frappe.get_doc({
				"doctype": "Profile Stock Ledger",
				"item_code": item_code,
				"item_name": item_data.item_name if item_data else "",
				"item_group": item_data.item_group if item_data else "",
				"length": length,
				"qty": qty,
				"is_scrap_piece": is_scrap_piece
			})
			doc.insert()
			frappe.logger().info(f"Yeni Profile Stock Ledger kaydı oluşturuldu: {item_code} {length or 'None'} (qty: {qty})")
			
			# Reorder kontrolü
			_check_reorder(item_code, length, qty)
		else:
			frappe.throw(f"Stok çıkışı yapılamaz: {item_code} {length or 'None'} profil stoku bulunamadı")


def _consolidate_duplicate_records(records, item_code, length, is_scrap_piece):
	"""Duplicate kayıtları birleştirir"""
	total_qty = sum(flt(record.qty) for record in records)
	
	# İlk kaydı tut, diğerlerini sil
	main_record = records[0]
	main_doc = frappe.get_doc("Profile Stock Ledger", main_record.name)
	main_doc.qty = total_qty
	main_doc.save()
	
	# Diğer kayıtları sil
	for record in records[1:]:
		frappe.delete_doc("Profile Stock Ledger", record.name)
	
	frappe.logger().info(
		f"Duplicate kayıtlar birleştirildi: {item_code} {length or 'None'} -> Toplam qty: {total_qty}"
	)


def get_all_profile_stocks(item_code=None, is_scrap_piece=0):
	"""Tüm profil stoklarını döner."""
	filters = {"is_scrap_piece": is_scrap_piece}
	if item_code:
		filters["item_code"] = item_code
	
	stocks = frappe.get_all(
		"Profile Stock Ledger",
		filters=filters,
		fields=["item_code", "length", "qty"],
		order_by="item_code, length"
	)
	
	return stocks
