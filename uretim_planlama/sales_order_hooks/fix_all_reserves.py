# -*- coding: utf-8 -*-
"""
Tüm onaylı satış siparişlerinin rezerv kayıtlarını düzeltir
"""

import frappe
from frappe import _
from frappe.utils import flt
from uretim_planlama.sales_order_hooks.raw_materials import (
	get_sales_order_raw_materials,
	upsert_reserved_raw_material,
)


@frappe.whitelist()
def fix_all_reserved_raw_materials(dry_run=True, limit=None):
	"""
	Tüm onaylı satış siparişlerinin rezerv kayıtlarını düzeltir.
	
	Args:
		dry_run: True ise sadece rapor döner, değişiklik yapmaz. False ise rezerv kayıtlarını günceller.
		limit: İşlenecek maksimum sipariş sayısı (test için)
	
	Returns:
		dict: İşlem sonuçları
	"""
	frappe.flags.in_import = True
	
	try:
		# Tüm onaylı siparişleri bul
		query = """
			SELECT name, customer, custom_end_customer
			FROM `tabSales Order`
			WHERE docstatus = 1
				AND (status != 'Completed' OR status IS NULL)
		"""
		
		if limit:
			query += f" LIMIT {limit}"
		
		sales_orders = frappe.db.sql(query, as_dict=True)
		
		total_orders = len(sales_orders)
		processed = 0
		updated = 0
		errors = []
		
		results = {
			'total_orders': total_orders,
			'processed': 0,
			'updated': 0,
			'errors': [],
			'dry_run': dry_run
		}
		
		if not dry_run:
			frappe.msgprint(
				_("Toplam {0} sipariş bulundu. İşlem başlatılıyor...").format(total_orders),
				alert=True,
			)
		
		for idx, so_row in enumerate(sales_orders, 1):
			so_name = so_row['name']
			
			try:
				# Child siparişlerde rezerv oluşturulmaz, kontrol et
				so = frappe.get_doc("Sales Order", so_name)
				if getattr(so, "is_long_term_child", 0) or getattr(so, "parent_sales_order", None):
					continue
				
				# Rezerv kayıtlarını hesapla
				raw_materials = get_sales_order_raw_materials(so_name)
				
				# Her hammadde için rezerv kaydını güncelle
				for row in raw_materials:
					if not dry_run:
						upsert_reserved_raw_material(
							sales_order=so_name,
							item_code=row["raw_material"],
							qty=row["qty"],
							item_name=row["item_name"],
							customer=so_row.get("customer", ""),
							end_customer=so_row.get("custom_end_customer", ""),
						)
				
				if not dry_run:
					# Commit her 50 siparişte bir
					if idx % 50 == 0:
						frappe.db.commit()
						frappe.msgprint(
							_("{0}/{1} sipariş işlendi...").format(idx, total_orders),
							indicator="blue",
						)
				
				processed += 1
				updated += 1
				
			except Exception as e:
				error_msg = f"Sipariş {so_name}: {str(e)}"
				errors.append(error_msg)
				frappe.log_error(
					f"fix_all_reserved_raw_materials hatası: {error_msg}",
					frappe.get_traceback(),
				)
		
		if not dry_run:
			frappe.db.commit()
		
		results['processed'] = processed
		results['updated'] = updated
		results['errors'] = errors
		
		return results
		
	finally:
		frappe.flags.in_import = False

