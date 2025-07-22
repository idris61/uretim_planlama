# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger import update_profile_stock


class ProfileEntry(Document):
	def on_submit(self):
		# Giriş onaylandığında stok artır
		for item in self.items:
			# lenght alanı string, ör: '5 m' -> float'a çevir
			length = float(str(item.lenght).replace(' m', '').replace(',', '.'))
			update_profile_stock(
				profile_type=item.item_code,
				length=length,
				qty=item.received_quantity,
				action="in"
			)

	def on_cancel(self):
		# Giriş iptal edildiğinde stok azalt (geri al)
		for item in self.items:
			length = float(str(item.lenght).replace(' m', '').replace(',', '.'))
			update_profile_stock(
				profile_type=item.item_code,
				length=length,
				qty=item.received_quantity,
				action="out"
			)
