# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from uretim_planlama.uretim_planlama.utils import parse_length, calculate_total_length


class ProfileExitItem(Document):
    def validate(self):
        """Satır doğrulama ve hesaplama"""
        try:
            length = parse_length(self.length)
            qty = self.output_quantity or 0
            self.total_length = calculate_total_length(length, qty)
        except Exception:
            self.total_length = 0
