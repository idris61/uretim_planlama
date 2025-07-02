import frappe
from frappe import _
from datetime import datetime, timedelta

@frappe.whitelist()
def get_sales_order_raw_materials(sales_order):
	if not sales_order or sales_order.startswith("new-"):
		frappe.throw(_("Lütfen önce Satış Siparişini kaydedin."), frappe.ValidationError)
	try:
		so = frappe.get_doc("Sales Order", sales_order)
	except frappe.DoesNotExistError:
		frappe.throw(_("Sales Order bulunamadı."))
	raw_materials = {}
	for item in so.items:
		bom = frappe.db.get_value("BOM", {"item": item.item_code, "is_active": 1, "is_default": 1}, "name")
		if not bom:
			continue
		bom_doc = frappe.get_doc("BOM", bom)
		for rm in bom_doc.items:
			key = rm.item_code
			if key not in raw_materials:
				item_name = frappe.db.get_value("Item", rm.item_code, "item_name") or ""
				reserve_warehouse = frappe.db.get_value("Warehouse", {"name": ["in", ["REZERV DEPO", "REZERV DEPO - O"]]}, "name") or ""
				reserve_warehouse_stock = frappe.db.get_value("Bin", {"item_code": rm.item_code, "warehouse": reserve_warehouse}, "actual_qty") or 0
				reserved_qty = frappe.db.sql(
					"SELECT SUM(quantity) FROM `tabRezerved Raw Materials` WHERE item_code = %s", (rm.item_code,), as_list=True
				)[0][0] or 0
				long_term_reserve_qty = get_long_term_reserve_qty(rm.item_code)
				used_from_long_term_reserve = frappe.db.sql(
					"SELECT SUM(used_qty) FROM `tabLong Term Reserve Usage` WHERE item_code = %s",
					(rm.item_code,), as_list=True
				)[0][0] or 0
				bin_rows = frappe.db.get_all(
					"Bin",
					filters={"item_code": rm.item_code},
					fields=["warehouse", "actual_qty"]
				)
				stock_total = sum([row["actual_qty"] for row in bin_rows])
				stock_by_warehouse = {row["warehouse"]: float(row["actual_qty"]) for row in bin_rows}
				raw_materials[key] = {
					"raw_material": rm.item_code,
					"item_name": item_name,
					"qty": 0,
					"stock": stock_total,
					"stock_by_warehouse": stock_by_warehouse,
					"reserved_qty": reserved_qty,
					"reserve_warehouse": reserve_warehouse,
					"reserve_warehouse_stock": reserve_warehouse_stock,
					"so_items": set(),
					"long_term_reserve_qty": float(long_term_reserve_qty),
					"used_from_long_term_reserve": float(used_from_long_term_reserve)
				}
			raw_materials[key]["qty"] += rm.qty * item.qty
			raw_materials[key]["so_items"].add(item.item_code)
	result = []
	is_submitted = so.docstatus == 1
	for data in raw_materials.values():
		kullanilabilir_stok = float(data["stock"] or 0) - float(data["reserved_qty"] or 0)
		if is_submitted:
			acik_miktar = 0
		else:
			acik_miktar = float(data["qty"] or 0) - kullanilabilir_stok
		mr_items = frappe.db.sql(
			"SELECT mri.parent, mri.qty, mr.transaction_date FROM `tabMaterial Request Item` mri INNER JOIN `tabMaterial Request` mr ON mri.parent = mr.name WHERE mri.item_code = %s AND mri.docstatus = 1 AND mr.material_request_type = 'Purchase'",
			(data["raw_material"],), as_dict=True
		)
		malzeme_talep_miktari = sum([row.qty for row in mr_items]) if mr_items else 0
		malzeme_talep_tooltip = ", ".join([f"{row.parent} ({row.qty})" for row in mr_items])
		po_items = frappe.db.sql(
			"SELECT poi.parent, poi.qty, poi.schedule_date FROM `tabPurchase Order Item` poi INNER JOIN `tabPurchase Order` po ON poi.parent = po.name WHERE poi.item_code = %s AND poi.docstatus = 1 AND po.docstatus = 1 AND (poi.qty > IFNULL(poi.received_qty, 0))",
			(data["raw_material"],), as_dict=True
		)
		siparis_edilen_miktar = sum([row.qty for row in po_items]) if po_items else 0
		siparis_edilen_tooltip = ", ".join([f"{row.parent} ({row.qty})" for row in po_items])
		beklenen_teslim_tarihi = min([row.schedule_date for row in po_items if row.schedule_date], default=None)
		long_term_details = get_long_term_reserve_details(data["raw_material"])
		used_long_term_details = get_used_long_term_reserve_details(data["raw_material"])
		result.append({
			"raw_material": data["raw_material"],
			"item_name": data["item_name"],
			"qty": data["qty"],
			"stock": data["stock"],
			"stock_by_warehouse": data["stock_by_warehouse"],
			"reserved_qty": data["reserved_qty"],
			"reserve_warehouse": data["reserve_warehouse"],
			"reserve_warehouse_stock": data["reserve_warehouse_stock"],
			"so_items": ", ".join(data["so_items"]),
			"kullanilabilir_stok": kullanilabilir_stok,
			"acik_miktar": acik_miktar,
			"malzeme_talep_miktari": malzeme_talep_miktari,
			"malzeme_talep_tooltip": malzeme_talep_tooltip,
			"siparis_edilen_miktar": siparis_edilen_miktar,
			"siparis_edilen_tooltip": siparis_edilen_tooltip,
			"beklenen_teslim_tarihi": beklenen_teslim_tarihi,
			"long_term_reserve_qty": data["long_term_reserve_qty"],
			"used_from_long_term_reserve": data["used_from_long_term_reserve"],
			"long_term_details": long_term_details,
			"used_long_term_details": used_long_term_details,
			"malzeme_talep_details": mr_items,
			"siparis_edilen_details": po_items
		})
	result = sorted(result, key=lambda x: float(x.get("acik_miktar", 0)), reverse=True)
	return result

@frappe.whitelist()
def get_long_term_reserve_qty(item_code):
	today = frappe.utils.nowdate()
	thirty_days_later = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
	qty = frappe.db.sql('''
		SELECT SUM(rrm.quantity)
		FROM `tabRezerved Raw Materials` rrm
		INNER JOIN `tabSales Order` so ON rrm.sales_order = so.name
		WHERE rrm.item_code = %s AND so.delivery_date >= %s
	''', (item_code, thirty_days_later))[0][0] or 0
	return qty

def get_long_term_reserve_details(item_code):
	rows = frappe.db.sql('''
		SELECT so.name as sales_order, so.customer, so.delivery_date, rrm.quantity
		FROM `tabRezerved Raw Materials` rrm
		INNER JOIN `tabSales Order` so ON rrm.sales_order = so.name
		WHERE rrm.item_code = %s AND so.delivery_date >= %s
	''', (item_code, (datetime.strptime(frappe.utils.nowdate(), "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")), as_dict=True)
	return rows

def get_used_long_term_reserve_details(item_code):
	rows = frappe.db.sql('''
		SELECT ltru.sales_order, ltru.used_qty, ltru.usage_date, so.customer
		FROM `tabLong Term Reserve Usage` ltru
		INNER JOIN `tabSales Order` so ON ltru.sales_order = so.name
		WHERE ltru.item_code = %s
	''', (item_code,), as_dict=True)
	return rows

# --- STOCK ENTRY SUBMIT EVENT ---
def release_reservations_on_stock_entry(doc, method):
	if doc.purpose not in ["Manufacture", "Material Transfer for Manufacture"]:
		return
	for item in doc.items:
		work_order = getattr(doc, "work_order", None)
		sales_order = None
		if work_order:
			sales_order = frappe.db.get_value("Work Order", work_order, "sales_order")
		if not sales_order:
			continue
		qty_to_consume = abs(item.qty)
		reserved_rows = frappe.get_all(
			"Rezerved Raw Materials",
			filters={"sales_order": sales_order, "item_code": item.item_code},
			fields=["name", "quantity"],
			order_by="creation asc"
		)
		for row in reserved_rows:
			if qty_to_consume <= 0:
				break
			rm_doc = frappe.get_doc("Rezerved Raw Materials", row.name)
			consume_qty = min(qty_to_consume, rm_doc.quantity or 0)
			rm_doc.quantity -= consume_qty
			if rm_doc.quantity <= 0:
				rm_doc.delete(ignore_permissions=True)
			else:
				rm_doc.save(ignore_permissions=True)
			qty_to_consume -= consume_qty
		long_term_rows = frappe.get_all(
			"Long Term Reserve Usage",
			filters={"sales_order": sales_order, "item_code": item.item_code},
			fields=["name", "used_qty"],
			order_by="creation asc"
		)
		for usage in long_term_rows:
			if qty_to_consume <= 0:
				break
			usage_doc = frappe.get_doc("Long Term Reserve Usage", usage.name)
			consume_qty = min(qty_to_consume, usage_doc.used_qty or 0)
			usage_doc.used_qty -= consume_qty
			if usage_doc.used_qty <= 0:
				usage_doc.delete(ignore_permissions=True)
			else:
				usage_doc.save(ignore_permissions=True)
			qty_to_consume -= consume_qty
	frappe.db.commit()
	frappe.msgprint(_("Stok hareketi ile ilişkili rezervler güncellendi."), indicator="green")

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

def restore_reservations_on_work_order_cancel(doc, method):
	sales_order = getattr(doc, "sales_order", None)
	if not sales_order:
		return
	for item in getattr(doc, "required_items", []):
		item_code = item.item_code
		qty = item.required_qty
		existing = frappe.db.exists(
			"Rezerved Raw Materials",
			{"sales_order": sales_order, "item_code": item_code}
		)
		if existing:
			rm_doc = frappe.get_doc("Rezerved Raw Materials", existing)
			rm_doc.quantity += qty
			rm_doc.save(ignore_permissions=True)
		else:
			rm_doc = frappe.new_doc("Rezerved Raw Materials")
			rm_doc.sales_order = sales_order
			rm_doc.item_code = item_code
			rm_doc.quantity = qty
			rm_doc.item_name = frappe.db.get_value("Item", item_code, "item_name") or ""
			rm_doc.customer = getattr(doc, "customer", "")
			rm_doc.end_customer = getattr(doc, "custom_end_customer", "")
			rm_doc.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.msgprint(_("İş emri iptal edildi, rezervler tekrar eklendi."), indicator="orange")
 