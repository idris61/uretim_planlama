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
			
			# Tüm olası formatları kontrol et
			alt_variant = fixed_str.replace('.', ',')
			# Tam sayı formatları da dahil et (6.0 -> 6, 6,0 -> 6)
			if fixed_str.endswith('.0'):
				integer_format = fixed_str[:-2]  # "6.0" -> "6"
				candidates = list({fixed_str, alt_variant, integer_format})
			else:
				candidates = list({fixed_str, alt_variant})
			
			# Ayrıca sayısal değere eşit olan tüm kayıtları da kontrol et
			existing = frappe.db.sql("""
				SELECT name, length 
				FROM `tabBoy` 
				WHERE name != %s 
				AND (
					length IN %s
					OR CAST(REPLACE(REPLACE(length, ',', '.'), ' m', '') AS DECIMAL(10,2)) = %s
				)
				LIMIT 1
			""", [self.name or '', tuple(candidates), numeric_length], as_dict=True)
			
			if existing:
				frappe.throw(
					_("Boy {0} zaten mevcut: {1}").format(
						fixed_str, existing[0].name
					),
					title=_("Çoklu İsim")
				)
