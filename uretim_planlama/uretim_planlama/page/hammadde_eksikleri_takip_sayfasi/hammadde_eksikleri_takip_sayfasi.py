# -*- coding: utf-8 -*-
# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
Hammadde Eksikleri Takip Sayfası API Metodları
Satınalma personeli için tüm siparişlere ait hammadde eksiklerini gösterir
"""

import frappe
from frappe import _
from frappe.utils import flt


def get_real_qty(value):
	"""Gerçek miktarı float olarak döndürür"""
	if value is None:
		return 0.0
	try:
		return float(value)
	except (ValueError, TypeError):
		return 0.0


@frappe.whitelist()
def get_warehouse_stock_details(item_code):
	"""Hammadde için depo bazlı stok detaylarını döndürür"""
	try:
		warehouse_stock = frappe.db.sql("""
			SELECT 
				warehouse,
				SUM(actual_qty) as qty
			FROM `tabBin`
			WHERE item_code = %s
			GROUP BY warehouse
			HAVING SUM(actual_qty) > 0
			ORDER BY SUM(actual_qty) DESC
		""", (item_code,), as_dict=True)
		
		return {
			'success': True,
			'data': warehouse_stock
		}
	except Exception as e:
		frappe.log_error(f"get_warehouse_stock_details HATA: {str(e)}", "Hammadde Eksikleri Raporu Hata")
		return {
			'success': False,
			'error': str(e),
			'data': []
		}


@frappe.whitelist()
def get_reserve_details(item_code):
	"""Hammadde için rezerv detaylarını döndürür (hangi siparişler için ne kadar)"""
	try:
		reserve_details = frappe.db.sql("""
			SELECT 
				rr.sales_order,
				rr.quantity,
				so.customer,
				so.delivery_date,
				so.transaction_date
			FROM `tabRezerved Raw Materials` rr
			INNER JOIN `tabSales Order` so ON so.name = rr.sales_order
			WHERE rr.item_code = %s
			ORDER BY so.delivery_date ASC, so.transaction_date DESC
		""", (item_code,), as_dict=True)
		
		return {
			'success': True,
			'data': reserve_details
		}
	except Exception as e:
		frappe.log_error(f"get_reserve_details HATA: {str(e)}", "Hammadde Eksikleri Raporu Hata")
		return {
			'success': False,
			'error': str(e),
			'data': []
		}


@frappe.whitelist()
def get_material_request_details(item_code):
	"""Hammadde için malzeme talebi detaylarını döndürür"""
	try:
		mr_details = frappe.db.sql("""
			SELECT 
				mri.parent as material_request,
				mri.qty,
				mri.stock_qty,
				mri.ordered_qty,
				mri.sales_order,
				mr.transaction_date,
				mr.status
			FROM `tabMaterial Request Item` mri
			INNER JOIN `tabMaterial Request` mr ON mri.parent = mr.name
			WHERE mri.item_code = %s
				AND mr.material_request_type = 'Purchase'
				AND mr.docstatus IN (0, 1)
				AND mr.status NOT IN ('Cancelled', 'Received')
			ORDER BY mr.transaction_date DESC, mri.sales_order
		""", (item_code,), as_dict=True)
		
		for d in mr_details:
			stock_qty = get_real_qty(d.get('stock_qty') or d.get('qty', 0))
			ordered_qty = get_real_qty(d.get('ordered_qty', 0))
			d['pending_qty'] = stock_qty - ordered_qty
		
		mr_details = [d for d in mr_details if d['pending_qty'] > 0.001]
		
		return {
			'success': True,
			'data': mr_details
		}
	except Exception as e:
		frappe.log_error(f"get_material_request_details HATA: {str(e)}", "Hammadde Eksikleri Raporu Hata")
		return {
			'success': False,
			'error': str(e),
			'data': []
		}


@frappe.whitelist()
def get_purchase_order_details(item_code):
	"""Hammadde için satınalma siparişi detaylarını döndürür"""
	try:
		po_details = frappe.db.sql("""
			SELECT 
				poi.parent as purchase_order,
				poi.qty,
				poi.received_qty,
				poi.schedule_date,
				po.supplier,
				po.transaction_date,
				po.status
			FROM `tabPurchase Order Item` poi
			INNER JOIN `tabPurchase Order` po ON poi.parent = po.name
			WHERE poi.item_code = %s
				AND po.docstatus IN (0, 1)
				AND po.status NOT IN ('Cancelled', 'Completed')
			ORDER BY poi.schedule_date ASC, po.transaction_date DESC
		""", (item_code,), as_dict=True)
		
		for d in po_details:
			d['pending_qty'] = get_real_qty(d.get('qty', 0)) - get_real_qty(d.get('received_qty', 0))
		
		po_details = [d for d in po_details if d['pending_qty'] > 0.001]
		
		return {
			'success': True,
			'data': po_details
		}
	except Exception as e:
		frappe.log_error(f"get_purchase_order_details HATA: {str(e)}", "Hammadde Eksikleri Raporu Hata")
		return {
			'success': False,
			'error': str(e),
			'data': []
		}


@frappe.whitelist()
def get_all_shortages_report(filters=None):
	"""
	Tüm siparişlere ait hammadde eksiklerini detaylı rapor olarak döndürür.
	PERFORMANS OPTİMİZE EDİLDİ: Tek sorgu ile tüm hesaplamalar yapılıyor (N+1 query problemi çözüldü)
	
	Args:
		filters (dict): Filtreleme parametreleri
			- item_code: Hammadde kodu (like)
			- item_name: Hammadde adı (like)
			- item_group: Ürün grubu (=)
	"""
	try:
		if isinstance(filters, str):
			import json
			filters = json.loads(filters) if filters.strip() else {}
		elif filters is None:
			filters = {}
		
		where_conditions = []
		where_params = []
		
		if filters.get('item_code'):
			where_conditions.append("i.item_code LIKE %s")
			where_params.append(f"%{filters['item_code']}%")
		
		if filters.get('item_name'):
			where_conditions.append("i.item_name LIKE %s")
			where_params.append(f"%{filters['item_name']}%")
		
		if filters.get('item_group'):
			where_conditions.append("i.item_group = %s")
			where_params.append(filters['item_group'])
		
		where_clause = ""
		if where_conditions:
			where_clause = "AND " + " AND ".join(where_conditions)
		
		optimized_query = """
			WITH item_list AS (
				SELECT DISTINCT 
					bi.item_code,
					i.item_name,
					i.stock_uom,
					i.item_group
				FROM `tabSales Order` so
				INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
				INNER JOIN `tabBOM` b ON b.item = soi.item_code 
					AND b.is_active = 1 AND b.is_default = 1
				INNER JOIN `tabBOM Item` bi ON bi.parent = b.name
				INNER JOIN `tabItem` i ON i.item_code = bi.item_code
				WHERE so.docstatus = 1
					AND i.is_stock_item = 1 
					AND i.is_purchase_item = 1
					AND LOWER(COALESCE(i.item_group, '')) != 'camlar'
					{where_clause}
			),
			bom_needed AS (
				SELECT 
					bi.item_code,
					SUM(COALESCE(bi.stock_qty, bi.qty) * COALESCE(soi.stock_qty, soi.qty)) as total_needed
				FROM `tabSales Order` so
				INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
				INNER JOIN `tabBOM` b ON b.item = soi.item_code 
					AND b.is_active = 1 AND b.is_default = 1
				INNER JOIN `tabBOM Item` bi ON bi.parent = b.name
				WHERE so.docstatus = 1
					AND (so.status != 'Completed' OR so.status IS NULL)
				GROUP BY bi.item_code
			),
			reserved AS (
				SELECT 
					rrm.item_code,
					SUM(rrm.quantity) as total_reserved
				FROM `tabRezerved Raw Materials` rrm
				INNER JOIN `tabSales Order` so ON so.name = rrm.sales_order
				WHERE so.docstatus = 1
				GROUP BY rrm.item_code
			),
			stock AS (
				SELECT 
					item_code,
					SUM(actual_qty) as total_stock
				FROM `tabBin`
				GROUP BY item_code
			),
			pending_mr AS (
				SELECT 
					mri.item_code,
					SUM(GREATEST(0, COALESCE(mri.stock_qty, mri.qty) - COALESCE(mri.ordered_qty, 0))) as pending_qty
				FROM `tabMaterial Request Item` mri
				INNER JOIN `tabMaterial Request` mr ON mri.parent = mr.name
				WHERE mr.material_request_type = 'Purchase'
					AND mr.docstatus IN (0, 1)
					AND mr.status NOT IN ('Cancelled', 'Received')
				GROUP BY mri.item_code
			),
			pending_po AS (
				SELECT 
					poi.item_code,
					SUM(GREATEST(0, poi.qty - COALESCE(poi.received_qty, 0))) as pending_qty
				FROM `tabPurchase Order Item` poi
				INNER JOIN `tabPurchase Order` po ON poi.parent = po.name
				WHERE po.docstatus IN (0, 1)
					AND po.status NOT IN ('Cancelled', 'Completed')
				GROUP BY poi.item_code
			)
			SELECT * FROM (
				SELECT 
					il.item_code,
					il.item_name,
					il.stock_uom,
					il.item_group,
					COALESCE(bn.total_needed, 0) as total_needed,
					COALESCE(r.total_reserved, 0) as total_reserved,
					COALESCE(s.total_stock, 0) as total_stock,
					COALESCE(pmr.pending_qty, 0) as pending_mr_qty,
					COALESCE(ppo.pending_qty, 0) as pending_po_qty,
					COALESCE(s.total_stock, 0) - COALESCE(r.total_reserved, 0) as available_stock,
					GREATEST(0, COALESCE(r.total_reserved, 0) - COALESCE(s.total_stock, 0) - COALESCE(pmr.pending_qty, 0) - COALESCE(ppo.pending_qty, 0)) as shortage
				FROM item_list il
				LEFT JOIN bom_needed bn ON bn.item_code = il.item_code
				LEFT JOIN reserved r ON r.item_code = il.item_code
				LEFT JOIN stock s ON s.item_code = il.item_code
				LEFT JOIN pending_mr pmr ON pmr.item_code = il.item_code
				LEFT JOIN pending_po ppo ON ppo.item_code = il.item_code
			) as final_result
			WHERE shortage > 0.0001 OR pending_mr_qty > 0.0001
			ORDER BY shortage DESC, pending_mr_qty DESC
		"""
		
		sql_query = optimized_query.replace('{where_clause}', where_clause)
		
		if where_params:
			result_data = frappe.db.sql(sql_query, tuple(where_params), as_dict=True)
		else:
			result_data = frappe.db.sql(sql_query, as_dict=True)
		
		result = []
		for row in result_data:
			result.append({
				'item_code': row['item_code'],
				'item_name': row['item_name'],
				'stock_uom': row['stock_uom'],
				'total_needed': get_real_qty(row['total_needed']),
				'total_reserved': get_real_qty(row['total_reserved']),
				'total_stock': get_real_qty(row['total_stock']),
				'pending_mr_qty': get_real_qty(row['pending_mr_qty']),
				'pending_po_qty': get_real_qty(row['pending_po_qty']),
				'available_stock': get_real_qty(row['available_stock']),
				'shortage': get_real_qty(row['shortage'])
			})
		
		return {
			'success': True,
			'data': result,
			'summary': {
				'total_items': len(result),
				'total_shortage': sum(get_real_qty(row.get('shortage', 0)) for row in result),
				'total_needed': sum(get_real_qty(row.get('total_needed', 0)) for row in result),
				'total_stock': sum(get_real_qty(row.get('total_stock', 0)) for row in result),
				'total_reserved': sum(get_real_qty(row.get('total_reserved', 0)) for row in result)
			}
		}
	except Exception as e:
		frappe.log_error(f"get_all_shortages_report HATA: {str(e)}\n{frappe.get_traceback()}", "Hammadde Eksikleri Raporu Hata")
		return {
			'success': False,
			'error': str(e),
			'data': [],
			'summary': {}
		}


@frappe.whitelist()
def get_profile_length_shortages(filters=None):
	"""Profil boy bazında stok verileri döndürür - PERFORMANS OPTİMİZE EDİLDİ"""
	try:
		if isinstance(filters, str):
			import json
			filters = json.loads(filters) if filters.strip() else {}
		elif filters is None:
			filters = {}
		
		where_conditions = []
		where_params = []
		
		if filters.get('profile_item_code'):
			where_conditions.append("psl.item_code LIKE %s")
			where_params.append(f"%{filters['profile_item_code']}%")
		
		if filters.get('profile_item_group'):
			where_conditions.append("i.item_group = %s")
			where_params.append(filters['profile_item_group'])
		
		if filters.get('profile_length'):
			try:
				length_value = float(str(filters['profile_length']).replace(',', '.'))
				where_conditions.append("b.length = %s")
				where_params.append(length_value)
			except:
				pass
		
		where_clause = ""
		if where_conditions:
			where_clause = "AND " + " AND ".join(where_conditions)
		
		base_query = """
			SELECT 
				psl.item_code,
				i.item_name,
				i.item_group,
				psl.length,
				COALESCE(b.length, 0) as length_value,
				psl.qty as stock_qty,
				psl.total_length as stock_total_length,
				psl.is_scrap_piece
			FROM `tabProfile Stock Ledger` psl
			INNER JOIN `tabItem` i ON i.item_code = psl.item_code
			LEFT JOIN `tabBoy` b ON b.name = psl.length
			WHERE psl.qty > 0
			{where_clause}
			ORDER BY psl.item_code, b.length ASC, psl.is_scrap_piece ASC
		"""
		
		sql_query = base_query.replace('{where_clause}', where_clause)
		
		if where_params:
			profile_data = frappe.db.sql(sql_query, tuple(where_params), as_dict=True)
		else:
			profile_data = frappe.db.sql(sql_query, as_dict=True)
		
		if not profile_data:
			return {
				'success': True,
				'data': []
			}
		
		boy_map = {}
		boys = frappe.db.sql("""
			SELECT name, length
			FROM `tabBoy`
			LIMIT 10000
		""", as_dict=True)
		for b in boys:
			try:
				boy_map[b.name] = float(b.length.replace(',', '.')) if b.length else 0
			except:
				boy_map[b.name] = 0
		
		item_codes = {row['item_code'] for row in profile_data}
		length_values = {row['length'] for row in profile_data if row.get('length')}
		
		reorder_rules = {}
		if item_codes and length_values:
			rules = frappe.db.sql("""
				SELECT item_code, length, min_qty, reorder_qty
				FROM `tabProfile Reorder Rule`
				WHERE active = 1
					AND item_code IN %(item_codes)s
					AND length IN %(lengths)s
			""", {
				'item_codes': tuple(item_codes),
				'lengths': tuple(length_values)
			}, as_dict=True)
			
			for rule in rules:
				boy_len = boy_map.get(rule.length, 0)
				if boy_len:
					key = (rule.item_code, boy_len)
					reorder_rules[key] = {
						'min_qty': get_real_qty(rule.min_qty),
						'reorder_qty': get_real_qty(rule.reorder_qty)
					}
		
		result = []
		for row in profile_data:
			length_value = get_real_qty(row.get('length_value', 0))
			if not length_value:
				try:
					length_str = str(row.get('length', '0'))
					length_value = float(length_str.replace(',', '.'))
				except:
					length_value = boy_map.get(row.get('length'), 0)
			
			rule_key = (row.get('item_code'), length_value)
			rule = reorder_rules.get(rule_key, {})
			
			result.append({
				'item_code': row.get('item_code'),
				'item_name': row.get('item_name'),
				'item_group': row.get('item_group'),
				'length': length_value,
				'stock_qty': get_real_qty(row.get('stock_qty', 0)),
				'total_length': get_real_qty(row.get('stock_total_length', 0)),
				'min_qty': rule.get('min_qty', 0),
				'reorder_qty': rule.get('reorder_qty', 0),
				'is_scrap_piece': bool(row.get('is_scrap_piece', 0))
			})
		
		return {
			'success': True,
			'data': result
		}
	except Exception as e:
		frappe.log_error(f"get_profile_length_shortages HATA: {str(e)}\n{frappe.get_traceback()}", "Profil Boy Eksikleri Hata")
		return {
			'success': False,
			'error': str(e),
			'data': []
		}
