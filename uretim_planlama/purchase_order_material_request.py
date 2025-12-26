"""
Purchase Order için Material Request'ten ürün getirme fonksiyonunun child item filtreleme desteği eklenmiş hali

ERPNext'in standart make_purchase_order fonksiyonunu extend eder.
Frappe'ın MultiSelectDialog'unda uygulanan child item filtrelerini (örn: Product Group) 
backend'de uygular ve sadece filtrelenmiş itemları Purchase Order'a ekler.

Module: uretim_planlama
Author: Ozerpan ERP Team
"""

import json
import time

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
	# PERFORMANS İZLEME: Başlangıç zamanı
	total_start_time = time.time()
	debug_log = []
	
	def log_step(step_name, start_time=None):
		"""Adım bazlı log kaydı"""
		if start_time:
			elapsed = time.time() - start_time
			debug_log.append(f"{step_name}: {elapsed:.3f}s")
			return time.time()
		else:
			return time.time()
	
	log_step("Fonksiyon başlangıcı")
	
	# args'ı parse et
	parse_start = log_step("Args parse başlangıcı")
	if isinstance(args, str):
		args = json.loads(args) if args.strip() else {}
	elif args is None:
		args = {}
	log_step("Args parse", parse_start)
	
	# Filtreleri parse et - tüm filtreler için generic
	filter_start = log_step("Filtre parse başlangıcı")
	filters = {}
	item_fields_needed = set()  # Item tablosundan alınması gereken field'lar
	
	for key, value in args.items():
		# filtered_children'ı atla (bu ayrı işleniyor)
		if key == "filtered_children":
			continue
		# Frappe'ın filtre formatı: {'field_name': ['operator', 'value']}
		if isinstance(value, list) and len(value) >= 2:
			operator = value[0]  # '=', '!=', 'like', 'in', '>', '<', vb.
			filter_value = value[1]
			filters[key] = {"operator": operator, "value": filter_value}
			# Eğer bu field Material Request Item'da yoksa, Item tablosundan alınmalı
			mri_fields = {'item_code', 'item_name', 'qty', 'stock_qty', 'ordered_qty', 'received_qty', 
			              'uom', 'stock_uom', 'conversion_factor', 'warehouse', 'description', 
			              'sales_order', 'sales_order_item', 'name', 'parent'}
			if key not in mri_fields:
				item_fields_needed.add(key)
	
	log_step("Filtre parse", filter_start)
	
	# PERFORMANS: Item bilgilerini toplu olarak çek (tek sorgu)
	item_cache_start = log_step("Item cache başlangıcı")
	item_cache = {}
	
	if item_fields_needed:
		try:
			# Önce Material Request Item'ları çek ve item_code'ları topla
			mri_query_start = time.time()
			item_codes = frappe.db.sql("""
				SELECT DISTINCT item_code
				FROM `tabMaterial Request Item`
				WHERE parent = %s AND item_code IS NOT NULL
			""", (source_name,), as_list=True)
			item_codes = [row[0] for row in item_codes if row[0]]
			log_step(f"Material Request Item sorgusu ({len(item_codes)} item)", mri_query_start)
			
			if item_codes:
				# Tüm item'ları tek sorguda çek - sadece ihtiyaç duyulan field'lar
				item_query_start = time.time()
				fields_str = ", ".join(item_fields_needed)
				item_data = frappe.db.sql("""
					SELECT name, {}
					FROM `tabItem`
					WHERE name IN %s
				""".format(fields_str), 
					(tuple(item_codes),), as_dict=True)
				
				# Cache'e ekle (dict olarak)
				for item in item_data:
					item_cache[item.name] = item
				
				log_step(f"Item sorgusu ({len(item_cache)} item cache'lendi)", item_query_start)
		except Exception as e:
			# Hata durumunda cache'i boş bırak, filtreleme çalışmaya devam etsin
			frappe.log_error(
				f"Purchase Order Material Request - Item cache oluşturulurken hata: {str(e)}\n{frappe.get_traceback()}",
				"PO_MR_FILTER_ERROR"
			)
			item_cache = {}
	
	log_step("Item cache oluşturma", item_cache_start)
	
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
	
	# KALICI ÇÖZÜM: "Malzeme Talebi Kalemi Seçimi" checkbox için filtered_children desteği
	filtered_children = args.get("filtered_children", [])
	
	# PERFORMANS İZLEME: Cache miss sayacı
	select_item_cache_misses = 0
	
	def update_item(source, target, source_parent):
		"""Item güncellemelerini yapar"""
		target.conversion_factor = source.conversion_factor or 1
		target.qty = flt(source.stock_qty) - flt(source.ordered_qty)
		target.stock_qty = flt(source.stock_qty) - flt(source.ordered_qty)
	
	def postprocess(source, target_doc):
		"""Target doc'un eksik değerlerini ayarlar"""
		postprocess_start = log_step("Postprocess başlangıcı")
		
		# Default supplier filtresi - OPTİMİZE EDİLMİŞ VERSİYON
		if frappe.flags.args and frappe.flags.args.default_supplier:
			# items only for given default supplier
			# PERFORMANS: Her item için ayrı get_item_defaults çağrısı yerine
			# tüm item'ların default supplier'larını tek sorguda çek
			if target_doc.items:
				supplier_filter_start = time.time()
				item_codes = [d.item_code for d in target_doc.items if d.item_code]
				if item_codes:
					# Item Default tablosundan default_supplier'ları toplu olarak çek
					supplier_map = frappe.db.sql("""
						SELECT parent as item_code, default_supplier
						FROM `tabItem Default`
						WHERE parent IN %s
							AND company = %s
							AND default_supplier = %s
					""", (tuple(item_codes), target_doc.company, frappe.flags.args.default_supplier), as_dict=True)
					
					# Hızlı lookup için dict oluştur
					valid_items = {row.item_code for row in supplier_map}
					
					# Sadece default_supplier'ı eşleşen itemları tut
					supplier_items = [d for d in target_doc.items if d.item_code in valid_items]
					target_doc.items = supplier_items
					log_step(f"Default supplier filtresi ({len(item_codes)} -> {len(supplier_items)} item)", supplier_filter_start)
		
		# ERPNext standard postprocess - OPTİMİZE EDİLMİŞ
		# set_missing_values çok yavaş (2.5+ saniye), sadece kritik alanları ayarla
		set_missing_start = time.time()
		try:
			# Sadece temel alanları ayarla
			if not target_doc.company:
				target_doc.company = source.company
			if not target_doc.transaction_date:
				target_doc.transaction_date = source.transaction_date
			if not target_doc.schedule_date:
				target_doc.schedule_date = source.schedule_date
			
			# set_missing_values'ı çağır ama calculate_taxes_and_totals'ı atla
			# (frontend'de otomatik olarak çağrılacak)
			from erpnext.stock.doctype.material_request.material_request import set_missing_values
			# Sadece temel set_missing_values işlemlerini yap
			target_doc.run_method("set_missing_values")
		except Exception as e:
			# Hata durumunda minimal ayarlar
			frappe.log_error(
				f"set_missing_values hatası (devam ediliyor): {str(e)}",
				"PO_MR_SET_MISSING_VALUES_WARNING"
			)
			if not target_doc.company:
				target_doc.company = source.company
			if not target_doc.transaction_date:
				target_doc.transaction_date = source.transaction_date
		log_step("set_missing_values", set_missing_start)
		
		log_step("Postprocess", postprocess_start)
	
	# PERFORMANS OPTİMİZASYONU: Önce item'ları filtrele, sonra get_mapped_doc'a ver
	# Bu şekilde get_mapped_doc daha az item işleyecek
	prefilter_start = log_step("Item ön filtreleme başlangıcı")
	
	# Material Request'i çek
	source_doc = frappe.get_cached_doc("Material Request", source_name)
	
	# Tüm item'ları önceden filtrele
	filtered_item_names = set()
	for item in source_doc.items:
		# select_item mantığını burada uygula
		# KALICI ÇÖZÜM: Eğer filtered_children varsa (child item selection yapıldıysa)
		if filtered_children:
			if item.name not in filtered_children:
				continue  # Bu item seçilmemiş, dahil etme
		
		# ERPNext standard: Kalan miktar kontrolü
		qty = item.ordered_qty or item.received_qty
		if not (qty < item.stock_qty):
			continue
		
		# Eğer filtre yoksa, hemen ekle
		if not filters:
			filtered_item_names.add(item.name)
			continue
		
		# Tüm filtreleri uygula (VE mantığı ile)
		include_item = True
		for field_name, filter_info in filters.items():
			# Document'ten field değerini al
			doc_value = getattr(item, field_name, None)
			
			# Eğer field Material Request Item'da yoksa, Item tablosundan al
			if doc_value is None and hasattr(item, 'item_code') and item.item_code:
				# Cache'den kontrol et
				if item.item_code in item_cache:
					item_data = item_cache[item.item_code]
					doc_value = item_data.get(field_name) if isinstance(item_data, dict) else getattr(item_data, field_name, None)
				else:
					# Cache'de yoksa, Item tablosundan çek (fallback)
					select_item_cache_misses += 1
					try:
						item_doc = frappe.get_cached_doc("Item", item.item_code)
						item_cache[item.item_code] = item_doc
						doc_value = getattr(item_doc, field_name, None)
					except:
						doc_value = None
			
			# Filtreyi uygula
			if not apply_filter(doc_value, filter_info["operator"], filter_info["value"]):
				include_item = False
				break  # Bir filtre geçmedi, item'ı dahil etme
		
		if include_item:
			filtered_item_names.add(item.name)
	
	log_step(f"Item ön filtreleme ({len(source_doc.items)} -> {len(filtered_item_names)} item)", prefilter_start)
	
	# OPTİMİZE EDİLMİŞ select_item: Sadece önceden filtrelenmiş item'ları kabul et
	# Bu çok hızlı çünkü sadece set kontrolü yapıyor
	def optimized_select_item(d):
		"""Optimize edilmiş select_item - sadece önceden filtrelenmiş item'ları kabul et"""
		# Önce filtered_item_names kontrolü (çok hızlı - set lookup O(1))
		if d.name not in filtered_item_names:
			return False
		
		# Kalan miktar kontrolü
		qty = d.ordered_qty or d.received_qty
		return qty < d.stock_qty
	
	# get_mapped_doc kullanarak mapping yap
	# NOT: get_mapped_doc içinde her item için optimized_select_item çağrılacak
	# Ama bu çok hızlı çünkü sadece set kontrolü yapıyor
	mapping_start = log_step("get_mapped_doc başlangıcı")
	
	try:
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
					"condition": optimized_select_item,  # OPTİMİZE EDİLMİŞ FİLTRELEME!
				},
			},
			target_doc,
			postprocess,
		)
		
		log_step("get_mapped_doc", mapping_start)
		
		# PERFORMANS İSTATİSTİKLERİ
		total_elapsed = time.time() - total_start_time
		debug_log.append(f"TOPLAM SÜRE: {total_elapsed:.3f}s")
		debug_log.append(f"Ön filtreleme sonucu: {len(filtered_item_names)} item")
		debug_log.append(f"select_item cache miss sayısı: {select_item_cache_misses}")
		debug_log.append(f"Sonuç item sayısı: {len(doclist.items)}")
		
		# Detaylı log kaydet
		log_message = f"""
Purchase Order Material Request - PERFORMANS RAPORU
==================================================
Material Request: {source_name}
Filtreler: {filters}
Item Fields Needed: {item_fields_needed}
Item Cache Size: {len(item_cache)}

ADIM BAZLI SÜRELER:
{chr(10).join(debug_log)}

ÖNERİLER:
- select_item çağrı sayısı çok yüksekse, filtreleme mantığını optimize edin
- Cache miss sayısı > 0 ise, item cache önceden doldurulmalı
- Toplam süre > 5s ise, performans optimizasyonu gerekli
"""
		frappe.log_error(log_message, "PO_MR_PERFORMANCE_DEBUG")
		
		doclist.set_onload("load_after_mapping", False)
		return doclist
	except Exception as e:
		# Hata durumunda da log kaydet
		total_elapsed = time.time() - total_start_time
		error_log = f"""
Purchase Order Material Request - HATA
=======================================
Material Request: {source_name}
Hata: {str(e)}
Toplam Süre (hata öncesi): {total_elapsed:.3f}s

ADIM BAZLI SÜRELER (hata öncesi):
{chr(10).join(debug_log)}

TRACEBACK:
{frappe.get_traceback()}
"""
		frappe.log_error(error_log, "PO_MR_FILTER_ERROR")
		raise


