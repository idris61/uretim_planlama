"""
Stock Entry için Material Request'ten ürün getirme fonksiyonunun child item filtreleme desteği eklenmiş hali

ERPNext'in standart make_stock_entry fonksiyonunu extend eder.
Frappe'ın MultiSelectDialog'unda uygulanan child item filtrelerini (örn: Product Group) 
backend'de uygular ve sadece filtrelenmiş itemları Stock Entry'e ekler.

Module: uretim_planlama
Author: Ozerpan ERP Team
"""

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt


@frappe.whitelist()
def make_stock_entry_with_filters(source_name, target_doc=None, args=None):
	"""
	Material Request'ten Stock Entry oluşturur, generic child item filtrelemeyi destekler
	
	ERPNext'in standart make_stock_entry metodunu extend eder:
	- ✅ Tüm Material Request Item fieldları filtrelenebilir
	- ✅ Tüm Frappe operatörleri desteklenir (=, !=, like, >, <, vb.)
	- ✅ Birden fazla filtre (VE mantığı ile)
	- ✅ get_mapped_doc kullanarak ERPNext standartlarına uygun çalışır
	
	Args:
		source_name (str): Material Request name
		target_doc (dict|Document, optional): Hedef Stock Entry document
		args (dict|str, optional): Filtreleme parametreleri
			Format: {'field_name': ['operator', 'value'], ...}
			
			Örnekler:
			- {'item_group': ['=', 'Montaj ve İzolasyon']}
			- {'item_code': ['like', '102']}
			- {'qty': ['>', 100]}
			- {'item_group': ['=', 'PVC'], 'qty': ['>', 50]}  # Birden fazla filtre
			
	Returns:
		Document: Filtrelenmiş itemlar ile Stock Entry document
		
	Örnek Kullanım:
		# Dialog'da filtre:
		# - Ürün Grubu = "Montaj ve İzolasyon"
		# - Miktar > 100
		
		# Backend'e gelen args:
		# {'item_group': ['=', 'Montaj ve İzolasyon'], 'qty': ['>', 100]}
		
		# Sonuç: Sadece "Montaj ve İzolasyon" grubunda VE miktarı 100'den 
		# büyük olan itemlar Stock Entry'e eklenir
	"""
	import json
	
	# args'ı parse et
	if isinstance(args, str):
		args = json.loads(args) if args.strip() else {}
	elif args is None:
		args = {}
	
	# Filtreleri parse et - tüm filtreler için generic
	filters = {}
	for key, value in args.items():
		# Frappe'ın filtre formatı: {'field_name': ['operator', 'value']}
		if isinstance(value, list) and len(value) >= 2:
			operator = value[0]  # '=', '!=', 'like', 'in', '>', '<', vb.
			filter_value = value[1]
			filters[key] = {"operator": operator, "value": filter_value}
	
	def apply_filter(doc_value, operator, filter_value):
		"""
		Tek bir filtreyi uygular
		
		Args:
			doc_value: Document field değeri
			operator (str): Karşılaştırma operatörü ('=', '!=', 'like', 'in', vb.)
			filter_value: Filtre değeri
			
		Returns:
			bool: Filtre geçerse True, geçmezse False
		"""
		if doc_value is None:
			return operator in ["!=", "not in"]
		
		# String operatörleri
		if operator == "=":
			return doc_value == filter_value
		elif operator == "!=":
			return doc_value != filter_value
		elif operator == "like":
			# Case-insensitive like
			return str(filter_value).lower() in str(doc_value).lower()
		elif operator == "not like":
			return str(filter_value).lower() not in str(doc_value).lower()
		elif operator == "in":
			# filter_value liste olmalı
			return doc_value in (filter_value if isinstance(filter_value, list) else [filter_value])
		elif operator == "not in":
			return doc_value not in (filter_value if isinstance(filter_value, list) else [filter_value])
		
		# Sayısal karşılaştırmalar
		elif operator == ">":
			return flt(doc_value) > flt(filter_value)
		elif operator == "<":
			return flt(doc_value) < flt(filter_value)
		elif operator == ">=":
			return flt(doc_value) >= flt(filter_value)
		elif operator == "<=":
			return flt(doc_value) <= flt(filter_value)
		
		# Varsayılan: eşitlik kontrolü
		return doc_value == filter_value
	
	# Filtreli item için condition fonksiyonu
	def should_include_item(doc):
		"""
		Item'ın dahil edilip edilmeyeceğini kontrol eder
		Tüm filtreleri dinamik olarak uygular
		"""
		# ERPNext standard: Kalan miktar kontrolü
		if flt(doc.ordered_qty, doc.precision("ordered_qty")) >= flt(doc.stock_qty, doc.precision("ordered_qty")):
			return False
		
		# Tüm filtreleri uygula (VE mantığı ile)
		for field_name, filter_info in filters.items():
			# Document'ten field değerini al
			doc_value = getattr(doc, field_name, None)
			
			# Filtreyi uygula
			if not apply_filter(doc_value, filter_info["operator"], filter_info["value"]):
				return False  # Bu filtre geçmedi, item'ı dahil etme
		
		return True  # Tüm filtreler geçti
	
	def update_item(obj, target, source_parent):
		"""Item güncellemelerini yapar"""
		qty = (
			flt(flt(obj.stock_qty) - flt(obj.ordered_qty)) / target.conversion_factor
			if flt(obj.stock_qty) > flt(obj.ordered_qty)
			else 0
		)
		target.qty = qty
		target.transfer_qty = qty * obj.conversion_factor
		target.conversion_factor = obj.conversion_factor

		if (
			source_parent.material_request_type == "Material Transfer"
			or source_parent.material_request_type == "Customer Provided"
		):
			target.t_warehouse = obj.warehouse
		else:
			target.s_warehouse = obj.warehouse

		if source_parent.material_request_type == "Customer Provided":
			target.allow_zero_valuation_rate = 1

		if source_parent.material_request_type == "Material Transfer":
			target.s_warehouse = obj.from_warehouse

	def set_missing_values(source, target):
		"""Target doc'un eksik değerlerini ayarlar"""
		target.purpose = source.material_request_type
		target.from_warehouse = source.set_from_warehouse
		target.to_warehouse = source.set_warehouse

		if source.job_card:
			target.purpose = "Material Transfer for Manufacture"

		if source.material_request_type == "Customer Provided":
			target.purpose = "Material Receipt"

		target.set_transfer_qty()
		target.set_actual_qty()
		target.calculate_rate_and_amount(raise_error_if_no_rate=False)
		target.stock_entry_type = target.purpose
		target.set_job_card_data()

		if source.job_card:
			job_card_details = frappe.get_all(
				"Job Card", filters={"name": source.job_card}, fields=["bom_no", "for_quantity"]
			)

			if job_card_details and job_card_details[0]:
				target.bom_no = job_card_details[0].bom_no
				target.fg_completed_qty = job_card_details[0].for_quantity
				target.from_bom = 1

	# get_mapped_doc kullanarak mapping yap
	doclist = get_mapped_doc(
		"Material Request",
		source_name,
		{
			"Material Request": {
				"doctype": "Stock Entry",
				"validation": {
					"docstatus": ["=", 1],
					"material_request_type": [
						"in",
						["Material Transfer", "Material Issue", "Customer Provided"],
					],
				},
			},
			"Material Request Item": {
				"doctype": "Stock Entry Detail",
				"field_map": {
					"name": "material_request_item",
					"parent": "material_request",
					"uom": "stock_uom",
					"job_card_item": "job_card_item",
				},
				"field_no_map": ["expense_account"],
				"postprocess": update_item,
				"condition": should_include_item,  # FİLTRELEME BURADA!
			},
		},
		target_doc,
		set_missing_values,
	)
	
	return doclist

