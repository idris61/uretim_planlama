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
		# Tüm onaylı siparişleri bul (child siparişler hariç)
		query = """
			SELECT name, customer, custom_end_customer
			FROM `tabSales Order`
			WHERE docstatus = 1
				AND (status != 'Completed' OR status IS NULL)
				AND (is_long_term_child = 0 OR is_long_term_child IS NULL)
				AND (parent_sales_order IS NULL OR parent_sales_order = '')
		"""

		if limit:
			query += f" LIMIT {int(limit)}"

		sales_orders = frappe.db.sql(query, as_dict=True)

		total_orders = len(sales_orders)
		processed = 0
		skipped = 0
		updated = 0
		total_materials = 0
		errors = []

		results = {
			'total_orders': total_orders,
			'processed': 0,
			'skipped': 0,
			'updated': 0,
			'total_materials': 0,
			'errors': [],
			'dry_run': dry_run
		}

		if not dry_run:
			frappe.msgprint(
				_("Toplam {0} sipariş bulundu. İşlem başlatılıyor...").format(total_orders),
				alert=True,
			)
		else:
			frappe.msgprint(
				_("DRY RUN: Toplam {0} sipariş bulundu. Değişiklik yapılmayacak.").format(total_orders),
				alert=True,
				indicator="orange",
			)

		for idx, so_row in enumerate(sales_orders, 1):
			so_name = so_row['name']

			try:
				# Child siparişlerde rezerv oluşturulmaz, kontrol et (ekstra güvenlik)
				so = frappe.get_doc("Sales Order", so_name)
				if getattr(so, "is_long_term_child", 0) or getattr(so, "parent_sales_order", None):
					skipped += 1
					continue

				# Rezerv kayıtlarını hesapla
				raw_materials = get_sales_order_raw_materials(so_name)

				if not raw_materials:
					# BOM'u olmayan veya hammaddesi olmayan siparişler
					skipped += 1
					continue

				material_count = len(raw_materials)
				total_materials += material_count

				# Her hammadde için rezerv kaydını güncelle
				for row in raw_materials:
					if not dry_run:
						try:
							upsert_reserved_raw_material(
								sales_order=so_name,
								item_code=row.get("raw_material", ""),
								qty=row.get("qty", 0),
								item_name=row.get("item_name", ""),
								customer=so_row.get("customer", ""),
								end_customer=so_row.get("custom_end_customer", ""),
							)
						except Exception as mat_error:
							error_msg = f"Sipariş {so_name}, Hammadde {row.get('raw_material', 'N/A')}: {str(mat_error)}"
							errors.append(error_msg)
							frappe.log_error(
								f"fix_all_reserved_raw_materials hammadde hatası: {error_msg}",
								frappe.get_traceback(),
							)

				if not dry_run:
					# Commit her 50 siparişte bir
					if idx % 50 == 0:
						frappe.db.commit()
						frappe.msgprint(
							_("{0}/{1} sipariş işlendi ({2} hammadde güncellendi)...").format(
								idx, total_orders, total_materials
							),
							indicator="blue",
						)

				processed += 1
				updated += 1

			except Exception as e:
				error_msg = f"Sipariş {so_name}: {str(e)}"
				errors.append(error_msg)
				frappe.log_error(
					f"fix_all_reserved_raw_materials hatası: {error_msg}\n{frappe.get_traceback()}",
					"Fix All Reserves Error",
				)
				# Hata olsa bile devam et
				continue

		if not dry_run:
			frappe.db.commit()

		results['processed'] = processed
		results['skipped'] = skipped
		results['updated'] = updated
		results['total_materials'] = total_materials
		results['errors'] = errors

		# Sonuç mesajı
		success_msg = _(
			"İşlem tamamlandı!\n"
			"İşlenen: {0}\n"
			"Atlanan: {1}\n"
			"Güncellenen: {2}\n"
			"Toplam Hammadde: {3}\n"
			"Hata: {4}"
		).format(
			processed, skipped, updated, total_materials, len(errors)
		)

		if not dry_run:
			frappe.msgprint(success_msg, alert=True, indicator="green" if len(errors) == 0 else "orange")
		else:
			frappe.msgprint(
				_("DRY RUN tamamlandı. Yukarıdaki sonuçlar gerçek değişiklikler değildir."),
				alert=True,
				indicator="blue",
			)

		return results

	finally:
		frappe.flags.in_import = False
