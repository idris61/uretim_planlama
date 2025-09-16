# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document

# Reorder fonksiyonu için import
from uretim_planlama.uretim_planlama.api.reorder import ensure_reorder_for_profile


class ProfileStockLedger(Document):
	"""Profile Stock Ledger DocType"""
	
	def validate(self):
		"""Doğrulama işlemleri"""
		if self.qty < 0:
			frappe.throw(_("Miktar negatif olamaz"))
		
		if self.length <= 0:
			frappe.throw(_("Boy değeri 0'dan büyük olmalıdır"))
		
		# Toplam uzunluk hesapla
		self.total_length = flt(self.length) * flt(self.qty)


def _check_reorder(profile_type, length, qty):
	"""Reorder kontrolü yapar"""
	try:
		ensure_reorder_for_profile(profile_type, float(length), float(qty))
	except Exception as e:
		frappe.log_error(f"Reorder ensure error: {profile_type} {length} -> {e}", "Profile Reorder Ensure Error")


def update_profile_stock(profile_type, length, qty, action, is_scrap_piece=0):
	"""
	Profile stok güncellemesi yapar.
	action: "add" veya "subtract"
	"""
	# Mevcut stok kaydını bul
	existing = frappe.get_all(
		"Profile Stock Ledger",
		filters={
			"profile_type": profile_type,
			"length": length,
			"is_scrap_piece": is_scrap_piece
		},
		fields=["name", "qty"],
		limit=1
	)
	
	if existing:
		# Mevcut kaydı güncelle
		doc = frappe.get_doc("Profile Stock Ledger", existing[0].name)
		if action == "add":
			doc.qty = flt(doc.qty) + flt(qty)
		elif action == "subtract":
			doc.qty = flt(doc.qty) - flt(qty)
		
		if doc.qty <= 0:
			doc.delete()
		else:
			doc.save()
			
		# Reorder kontrolü (sadece 1 kez)
		_check_reorder(profile_type, length, doc.qty)
	else:
		# Yeni kayıt oluştur
		if action == "add":
			doc = frappe.get_doc({
				"doctype": "Profile Stock Ledger",
				"profile_type": profile_type,
				"length": length,
				"qty": qty,
				"is_scrap_piece": is_scrap_piece
			})
			doc.insert()
			
			# Reorder kontrolü (sadece 1 kez)
			_check_reorder(profile_type, length, qty)
		else:
			frappe.throw(f"Stok çıkışı yapılamaz: {profile_type} {length}m profil stoku bulunamadı")


def get_profile_stock(profile_type, length, is_scrap_piece=0):
	"""Belirli profil boyunda mevcut stok miktarını döner."""
	existing = frappe.get_all(
		"Profile Stock Ledger",
		filters={
			"profile_type": profile_type,
			"length": length,
			"is_scrap_piece": is_scrap_piece
		},
		fields=["qty"],
		limit=1
	)
	
	return flt(existing[0].qty) if existing else 0


def get_all_profile_stocks(profile_type=None, is_scrap_piece=0):
	"""Tüm profil stoklarını döner."""
	filters = {"is_scrap_piece": is_scrap_piece}
	if profile_type:
		filters["profile_type"] = profile_type
	
	stocks = frappe.get_all(
		"Profile Stock Ledger",
		filters=filters,
		fields=["profile_type", "length", "qty"],
		order_by="profile_type, length"
	)
	
	return stocks
