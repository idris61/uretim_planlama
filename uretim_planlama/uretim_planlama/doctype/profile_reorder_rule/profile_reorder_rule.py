# Copyright (c) 2025, idris
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ProfileReorderRule(Document):
	"""Boy bazlı asgari stok eşiği tanımı. (profile_type, length) tekildir."""

	def validate(self):
		self._validate_numbers()
		self._validate_unique_key()

	def _validate_numbers(self):
		if self.min_qty is None or self.min_qty < 0:
			frappe.throw(_("Minimum Quantity must be >= 0"))
		if self.reorder_qty is None or self.reorder_qty <= 0:
			frappe.throw(_("Reorder Quantity must be > 0"))

	def _validate_unique_key(self):
		filters = {
			"profile_type": self.profile_type,
			"length": self.length,
		}
		# Warehouse field DocType'da yok, sadece profile_type ve length ile kontrol et
		if self.name:
			filters["name"] = ["!=", self.name]
		
		existing = frappe.get_all("Profile Reorder Rule", filters=filters, pluck="name")
		if existing:
			frappe.throw(_("Duplicate rule for same Profile Type/Length combination"))
