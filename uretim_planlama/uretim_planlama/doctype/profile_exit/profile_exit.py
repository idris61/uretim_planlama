# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger import update_profile_stock


class ProfileExit(Document):
	def on_submit(self):
		# Çıkış onaylandığında stok azalt
		for item in self.items:
			length = float(str(item.length).replace(' m', '').replace(',', '.'))
			update_profile_stock(
				profile_type=item.item_code,
				length=length,
				qty=item.output_quantity,
				action="out"
			)

	def on_cancel(self):
		# Çıkış iptal edildiğinde stok geri ekle
		for item in self.items:
			length = float(str(item.length).replace(' m', '').replace(',', '.'))
			update_profile_stock(
				profile_type=item.item_code,
				length=length,
				qty=item.output_quantity,
				action="in"
			)
