# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from uretim_planlama.uretim_planlama.utils import parse_and_format_length


class Boy(Document):
	def before_save(self):
		"""Boy kaydı kaydedilmeden önce length değerini normalize et"""
		if self.length:
			numeric_length, fixed_str = parse_and_format_length(self.length, decimals=1)
			self.length = fixed_str
	
	def validate(self):
		"""Boy kaydı validasyonu - duplicate kontrolü"""
		if self.length:
			# Normalize edilmiş eşdeğerleriyle birlikte duplicate kontrolü yap
			numeric_length, fixed_str = parse_and_format_length(self.length, decimals=1)
			alt_variant = fixed_str.replace('.', ',')
			candidates = list({fixed_str, alt_variant})
			existing = frappe.get_all(
				"Boy",
				filters={"name": ["!=", self.name], "length": ["in", candidates]},
				fields=["name", "length"],
				limit=1,
			)
			if existing:
				frappe.throw(
					_("Bu boy değeri ({0}) zaten mevcut: {1}").format(
						fixed_str, existing[0].name
					),
					title=_("Duplicate Boy Değeri")
				)
