# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Boy(Document):
	def before_insert(self):
		if self.length:
			# 5 girdiğinde hem length hem name 5.0 yap
			formatted_length = f"{float(self.length):.1f}"
			self.length = float(formatted_length)
			self.name = formatted_length
