# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger import update_profile_stock

class ScrapProfileEntry(Document):
    def before_save(self):
        # Toplam uzunluk otomatik hesaplanır
        if self.length and self.qty:
            self.total_length = float(self.length) * int(self.qty)
        else:
            self.total_length = 0

    def on_submit(self):
        # Profile Stock Ledger'a parça kaydı ekle (toplam stoklara dahil edilmez)
        update_profile_stock(
            profile_type=self.profile_code,
            length=self.length,
            qty=self.qty,
            action="in",
            is_scrap_piece=1
        ) 