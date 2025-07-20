# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ProfileExitItem(Document):
    def validate(self):
        # length alanı string ise float'a çevir
        try:
            length = float(str(self.length).replace(' m', '').replace(',', '.'))
        except Exception:
            length = 0
        qty = self.output_quantity or 0
        self.total_length = round(length * qty, 3)
