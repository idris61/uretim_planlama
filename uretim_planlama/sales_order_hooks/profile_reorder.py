import frappe
from frappe import _


def check_profile_reorder_on_sales_order(doc, method):
	"""Sales Order submit edildiğinde profile reorder kontrolü yap (sessiz)."""
	# Test amaçlı bırakılan çağrı ve kullanıcıya mesaj gösterimi kaldırıldı.
	# Gerçek entegrasyon için Sales Order kalemlerinden profil tipi/boy bilgisi okunarak
	# ensure_reorder_for_profile çağrısı yapılmalıdır.
	return


def get_current_profile_stock(profile_type, length):
	"""Profil tipine ve boyuna göre mevcut stok miktarını al"""
	try:
		stock_records = frappe.get_all(
			"Profile Stock Ledger",
			filters={
				"item_code": profile_type,
				"length": length,
				"is_scrap_piece": 0
			},
			fields=["qty"]
		)
		
		total_stock = sum(float(record.qty or 0) for record in stock_records)
		return total_stock
		
	except Exception as e:
		frappe.log_error(f"Get profile stock error: {str(e)}", "Profile Stock Error")
		return 0
