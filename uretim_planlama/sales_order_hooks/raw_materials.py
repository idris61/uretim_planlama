import frappe
from frappe import _

@frappe.whitelist()
def get_sales_order_raw_materials(sales_order):
	so = frappe.get_doc("Sales Order", sales_order)
	raw_materials = {}
	for item in so.items:
		# BOM bul, raw materials ve stok miktarlarını çek
		bom = frappe.db.get_value("BOM", {"item": item.item_code, "is_active": 1, "is_default": 1}, "name")
		if bom:
			bom_doc = frappe.get_doc("BOM", bom)
			for rm in bom_doc.items:
				key = (rm.item_code, item.warehouse)
				if key not in raw_materials:
					item_name = frappe.db.get_value("Item", rm.item_code, "item_name") or ""
					# Sadece adı tam olarak 'REZERV DEPO' veya 'REZERV DEPO - O' olan depoyu kullan
					reserve_warehouse = frappe.db.get_value("Warehouse", {"name": "REZERV DEPO"}, "name") or ""
					if not reserve_warehouse:
						reserve_warehouse = frappe.db.get_value("Warehouse", {"name": "REZERV DEPO - O"}, "name") or ""
					reserve_warehouse_stock = 0
					if reserve_warehouse:
						reserve_bin = frappe.db.get_value("Bin", {"item_code": rm.item_code, "warehouse": reserve_warehouse}, "actual_qty")
						reserve_warehouse_stock = reserve_bin or 0
					# Reserved Qty: Rezerved Raw Materials doctype'ındaki toplam quantity
					reserved_qty = frappe.db.sql(
						"""
						SELECT SUM(quantity) FROM `tabRezerved Raw Materials` WHERE item_code = %s
						""", (rm.item_code,), as_list=True
					)
					reserved_qty = reserved_qty[0][0] if reserved_qty and reserved_qty[0][0] else 0
					raw_materials[key] = {
						"raw_material": rm.item_code,
						"item_name": item_name,
						"qty": 0,
						"stock": 0,
						"reserved_qty": reserved_qty,
						"reserve_warehouse": reserve_warehouse,
						"reserve_warehouse_stock": reserve_warehouse_stock,
						"so_items": set()
					}
				raw_materials[key]["qty"] += rm.qty * item.qty
				bin_row = frappe.db.get_value("Bin", {"item_code": rm.item_code, "warehouse": item.warehouse}, ["actual_qty", "reserved_qty"], as_dict=True) or {"actual_qty": 0, "reserved_qty": 0}
				raw_materials[key]["stock"] += bin_row["actual_qty"]
				raw_materials[key]["so_items"].add(item.item_code)
	# Sonuçları listeye çevir
	result = []
	for (raw_material, warehouse), data in raw_materials.items():
		result.append({
			"raw_material": raw_material,
			"item_name": data["item_name"],
			"qty": data["qty"],
			"stock": data["stock"],
			"reserved_qty": data["reserved_qty"],
			"reserve_warehouse": data["reserve_warehouse"],
			"reserve_warehouse_stock": data["reserve_warehouse_stock"],
			"so_items": ", ".join(data["so_items"])
		})
	return result

def create_reserved_raw_materials_on_submit(doc, method):
	try:
		raw_materials = get_sales_order_raw_materials(doc.name)
		for row in raw_materials:
			existing = frappe.db.exists(
				"Rezerved Raw Materials",
				{"sales_order": doc.name, "item_code": row["raw_material"]}
			)
			if existing:
				rm_doc = frappe.get_doc("Rezerved Raw Materials", existing)
				rm_doc.quantity = row["qty"]
				rm_doc.item_name = row["item_name"]
				rm_doc.customer = getattr(doc, "customer", "")
				rm_doc.end_customer = getattr(doc, "custom_end_customer", "")
				rm_doc.save(ignore_permissions=True)
			else:
				rm_doc = frappe.new_doc("Rezerved Raw Materials")
				rm_doc.sales_order = doc.name
				rm_doc.item_code = row["raw_material"]
				rm_doc.quantity = row["qty"]
				rm_doc.item_name = row["item_name"]
				rm_doc.customer = getattr(doc, "customer", "")
				rm_doc.end_customer = getattr(doc, "custom_end_customer", "")
				rm_doc.insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint(_("{0} için rezerve oluşturuldu.").format(doc.name), alert=True, indicator="green")
	except Exception:
		frappe.log_error("Sales Order submit hook HATA", frappe.get_traceback())

def delete_reserved_raw_materials_on_cancel(doc, method):
	try:
		reserved = frappe.get_all(
			"Rezerved Raw Materials",
			filters={"sales_order": doc.name},
			fields=["name"]
		)
		for row in reserved:
			frappe.delete_doc("Rezerved Raw Materials", row["name"], ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint(_("{0} için rezerve iptal edildi.").format(doc.name), alert=True, indicator="orange")
	except Exception:
		frappe.log_error("Sales Order cancel hook HATA", frappe.get_traceback())

def delete_reserved_raw_materials_on_delivery_or_invoice(doc, method):
	try:
		sales_orders = set()
		if hasattr(doc, "items"):
			for item in doc.items:
				# Eğer Sales Invoice, Delivery Note'a bağlıysa ve Sales Order'a bağlı değilse, atla
				if getattr(item, "delivery_note", None):
					continue
				# 1. Öncelik: against_sales_order
				if getattr(item, "against_sales_order", None):
					sales_orders.add(item.against_sales_order)
				# 2. Alternatif: sales_order (özellikle direkt Sales Invoice için)
				elif getattr(item, "sales_order", None):
					sales_orders.add(item.sales_order)
		for so in sales_orders:
			reserved = frappe.get_all(
				"Rezerved Raw Materials",
				filters={"sales_order": so},
				fields=["name"]
			)
			for row in reserved:
				frappe.delete_doc("Rezerved Raw Materials", row["name"], ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint(_("Rezerve iptal edildi."), alert=True, indicator="orange")
	except Exception:
		frappe.log_error("Sevk/Invoice ile rezerv silme HATA", frappe.get_traceback())

def restore_reserved_raw_materials_on_cancel(doc, method):
	try:
		sales_orders = set()
		if hasattr(doc, "items"):
			for item in doc.items:
				if getattr(item, "delivery_note", None):
					continue
				if getattr(item, "against_sales_order", None):
					sales_orders.add(item.against_sales_order)
				elif getattr(item, "sales_order", None):
					sales_orders.add(item.sales_order)
		for so in sales_orders:
			# Satış siparişi hâlâ onaylıysa rezervasyonu tekrar oluştur
			so_doc = frappe.get_doc("Sales Order", so)
			if so_doc.docstatus == 1:
				create_reserved_raw_materials_on_submit(so_doc, None)
		frappe.db.commit()
		frappe.msgprint(_("Rezerve tekrar oluşturuldu."), alert=True, indicator="green")
	except Exception:
		frappe.log_error("Sevk/Invoice iptal ile rezerv geri getirme HATA", frappe.get_traceback())
 