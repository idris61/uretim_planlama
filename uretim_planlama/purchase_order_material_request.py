"""
Purchase Order için Material Request'ten ürün getirme fonksiyonunun child item filtreleme desteği eklenmiş hali

ERPNext'in standart make_purchase_order fonksiyonunu extend eder.
Frappe'ın MultiSelectDialog'unda uygulanan child item filtrelerini (örn: Product Group) 
backend'de uygular ve sadece filtrelenmiş itemları Purchase Order'a ekler.

Module: uretim_planlama
Author: Ozerpan ERP Team
"""

import json

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt


@frappe.whitelist()
def make_purchase_order_with_filters(source_name, target_doc=None, args=None):
	"""
	Material Request'ten Purchase Order oluşturur, generic child item filtrelemeyi destekler
	
	ERPNext'in standart make_purchase_order metodunu extend eder:
	- ✅ Tüm Material Request Item fieldları filtrelenebilir
	- ✅ Tüm Frappe operatörleri desteklenir (=, !=, like, >, <, vb.)
	- ✅ Birden fazla filtre (VE mantığı ile)
	- ✅ get_mapped_doc kullanarak ERPNext standartlarına uygun çalışır
	
	Args:
		source_name (str): Material Request name
		target_doc (dict|Document, optional): Hedef Purchase Order document
		args (dict|str, optional): Filtreleme parametreleri
			Format: {'field_name': ['operator', 'value'], ...}
			
			Örnekler:
			- {'item_group': ['=', 'Montaj ve İzolasyon']}
			- {'item_code': ['like', '102']}
			- {'qty': ['>', 100]}
			- {'item_group': ['=', 'PVC'], 'qty': ['>', 50]}  # Birden fazla filtre
			
	Returns:
		Document: Filtrelenmiş itemlar ile Purchase Order document
		
	Örnek Kullanım:
		# Dialog'da filtre:
		# - Ürün Grubu = "Montaj ve İzolasyon"
		# - Miktar > 100
		
		# Backend'e gelen args:
		# {'item_group': ['=', 'Montaj ve İzolasyon'], 'qty': ['>', 100]}
		
		# Sonuç: Sadece "Montaj ve İzolasyon" grubunda VE miktarı 100'den 
		# büyük olan itemlar Purchase Order'a eklenir
	"""
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
	
	def select_item(d):
		"""
		Item'ın dahil edilip edilmeyeceğini kontrol eder
		Tüm filtreleri dinamik olarak uygular
		"""
		# ERPNext standard: Kalan miktar kontrolü
		qty = d.ordered_qty or d.received_qty
		if not (qty < d.stock_qty):
			return False
		
		# Tüm filtreleri uygula (VE mantığı ile)
		for field_name, filter_info in filters.items():
			# Document'ten field değerini al
			doc_value = getattr(d, field_name, None)
			
			# Filtreyi uygula
			if not apply_filter(doc_value, filter_info["operator"], filter_info["value"]):
				return False  # Bu filtre geçmedi, item'ı dahil etme
		
		return True  # Tüm filtreler geçti
	
	def update_item(source, target, source_parent):
		"""Item güncellemelerini yapar"""
		target.conversion_factor = source.conversion_factor or 1
		target.qty = flt(source.stock_qty) - flt(source.ordered_qty)
		target.stock_qty = flt(source.stock_qty) - flt(source.ordered_qty)
	
	def postprocess(source, target_doc):
		"""Target doc'un eksik değerlerini ayarlar"""
		# Default supplier filtresi
		if frappe.flags.args and frappe.flags.args.default_supplier:
			# items only for given default supplier
			from erpnext.stock.doctype.item.item import get_item_defaults
			
			supplier_items = []
			for d in target_doc.items:
				default_supplier = get_item_defaults(d.item_code, target_doc.company).get("default_supplier")
				if frappe.flags.args.default_supplier == default_supplier:
					supplier_items.append(d)
			target_doc.items = supplier_items
		
		# ERPNext standard postprocess
		from erpnext.stock.doctype.material_request.material_request import set_missing_values
		set_missing_values(source, target_doc)
	
	# get_mapped_doc kullanarak mapping yap
	doclist = get_mapped_doc(
		"Material Request",
		source_name,
		{
			"Material Request": {
				"doctype": "Purchase Order",
				"validation": {"docstatus": ["=", 1], "material_request_type": ["=", "Purchase"]},
			},
			"Material Request Item": {
				"doctype": "Purchase Order Item",
				"field_map": [
					["name", "material_request_item"],
					["parent", "material_request"],
					["uom", "stock_uom"],
					["uom", "uom"],
					["sales_order", "sales_order"],
					["sales_order_item", "sales_order_item"],
					["wip_composite_asset", "wip_composite_asset"],
				],
				"postprocess": update_item,
				"condition": select_item,  # FİLTRELEME BURADA!
			},
		},
		target_doc,
		postprocess,
	)
	
	doclist.set_onload("load_after_mapping", False)
	return doclist

