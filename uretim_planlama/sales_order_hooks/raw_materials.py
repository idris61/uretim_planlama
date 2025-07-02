import frappe
from frappe import _
from datetime import datetime, timedelta
import json

@frappe.whitelist()
def get_sales_order_raw_materials(sales_order):
	"""Satış siparişi için gerekli hammadde ve stok bilgilerini döndürür."""
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
		acik_miktar = 0 if is_submitted else float(data["qty"] or 0) - kullanilabilir_stok
		mr_items = frappe.db.sql(
			"SELECT mri.parent, mri.qty, mr.transaction_date FROM `tabMaterial Request Item` mri INNER JOIN `tabMaterial Request` mr ON mri.parent = mr.name WHERE mri.item_code = %s AND mri.docstatus = 1 AND mr.material_request_type = 'Purchase'",
			(data["raw_material"],), as_dict=True
		)
		po_items = frappe.db.sql(
			"SELECT poi.parent, poi.qty, poi.schedule_date FROM `tabPurchase Order Item` poi INNER JOIN `tabPurchase Order` po ON poi.parent = po.name WHERE poi.item_code = %s AND poi.docstatus = 1 AND po.docstatus = 1 AND (poi.qty > IFNULL(poi.received_qty, 0))",
			(data["raw_material"],), as_dict=True
		)
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
			"malzeme_talep_details": mr_items,
			"siparis_edilen_details": po_items,
			"beklenen_teslim_tarihi": beklenen_teslim_tarihi,
			"long_term_reserve_qty": data["long_term_reserve_qty"],
			"used_from_long_term_reserve": data["used_from_long_term_reserve"],
			"long_term_details": long_term_details,
			"used_long_term_details": used_long_term_details
		})
	return sorted(result, key=lambda x: float(x.get("acik_miktar", 0)), reverse=True)

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

@frappe.whitelist()
def check_long_term_reserve_availability(sales_order):
	if not sales_order or sales_order.startswith("new-"):
		frappe.throw(_("Lütfen önce Satış Siparişini kaydedin."), frappe.ValidationError)
	so = frappe.get_doc("Sales Order", sales_order)
	raw_materials = get_sales_order_raw_materials(sales_order)
	recommendations = []
	for row in raw_materials:
		acik_miktar = float(row.get("acik_miktar", 0))
		uzun_vadeli_rezerv = float(row.get("long_term_reserve_qty", 0))
		kullanilan_rezerv = float(row.get("used_from_long_term_reserve", 0))
		kullanilabilir_uzun_vadeli = max(uzun_vadeli_rezerv - kullanilan_rezerv, 0)
		if acik_miktar > 0 and kullanilabilir_uzun_vadeli > 0:
			onerilen_kullanim = min(acik_miktar, kullanilabilir_uzun_vadeli)
			recommendations.append({
				"item_code": row.get("raw_material"),
				"item_name": row.get("item_name"),
				"acik_miktar": acik_miktar,
				"uzun_vadeli_rezerv": uzun_vadeli_rezerv,
				"kullanilan_rezerv": kullanilan_rezerv,
				"kullanilabilir_uzun_vadeli": kullanilabilir_uzun_vadeli,
				"onerilen_kullanim": onerilen_kullanim
			})
	return recommendations

def delete_long_term_reserve_usage_on_cancel(doc, method):
	sales_order = getattr(doc, "name", None)
	if not sales_order:
		return
	try:
		usage_rows = frappe.get_all(
			"Long Term Reserve Usage",
			filters={"sales_order": sales_order},
			fields=["name"]
		)
		for row in usage_rows:
			frappe.delete_doc("Long Term Reserve Usage", row["name"], ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint(_("{0} için uzun vadeli rezerv kullanımları silindi.").format(sales_order), alert=True, indicator="orange")
	except Exception:
		frappe.log_error("Sales Order cancel hook (delete_long_term_reserve_usage_on_cancel) HATA", frappe.get_traceback())

def check_raw_material_stock_on_submit(doc, method):
	try:
		raw_materials = get_sales_order_raw_materials(doc.name)
		eksik_list = []
		for row in raw_materials:
			acik_miktar = float(row.get("acik_miktar", 0))
			if acik_miktar > 0:
				eksik_list.append(f"{row.get('raw_material')} ({acik_miktar})")
		if eksik_list:
			frappe.throw(
				_("Aşağıdaki hammaddeler için stok yetersiz: {0}").format(", ".join(eksik_list)),
				frappe.ValidationError
			)
	except Exception:
		frappe.log_error("Sales Order before_submit hook (check_raw_material_stock_on_submit) HATA", frappe.get_traceback())

@frappe.whitelist()
def use_long_term_reserve_bulk(sales_order, usage_data):
	"""
	usage_data: JSON string [{"item_code": "...", "qty": ...}, ...]
	"""
	if not sales_order or not usage_data:
		return {"success": False, "message": "Eksik parametre."}
	try:
		usage_list = json.loads(usage_data)
		for usage in usage_list:
			item_code = usage.get("item_code")
			qty = float(usage.get("qty", 0))
			if not item_code or qty <= 0:
				continue
			# Daha önce kullanım var mı kontrol et
			existing = frappe.get_all(
				"Long Term Reserve Usage",
				filters={"sales_order": sales_order, "item_code": item_code},
				fields=["name"]
			)
			if existing:
				usage_doc = frappe.get_doc("Long Term Reserve Usage", existing[0]["name"])
				usage_doc.used_qty += qty
				usage_doc.usage_date = frappe.utils.nowdate()
				usage_doc.save(ignore_permissions=True)
			else:
				usage_doc = frappe.new_doc("Long Term Reserve Usage")
				usage_doc.sales_order = sales_order
				usage_doc.item_code = item_code
				usage_doc.used_qty = qty
				usage_doc.usage_date = frappe.utils.nowdate()
				usage_doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return {"success": True, "message": "Uzun vadeli rezerv kullanımı başarıyla kaydedildi."}
	except Exception:
		frappe.log_error("use_long_term_reserve_bulk HATA", frappe.get_traceback())
		return {"success": False, "message": "Bir hata oluştu. Lütfen tekrar deneyin."}

@frappe.whitelist()
def create_material_request_for_shortages(sales_order):
	if not sales_order:
		return {"success": False, "message": "Satış Siparişi bulunamadı."}
	try:
		raw_materials = get_sales_order_raw_materials(sales_order)
		shortage_items = []
		for row in raw_materials:
			acik_miktar = float(row.get("acik_miktar", 0))
			if acik_miktar > 0:
				shortage_items.append({
					"item_code": row.get("raw_material"),
					"qty": acik_miktar,
					"schedule_date": frappe.utils.nowdate()
				})
		if not shortage_items:
			return {"success": False, "message": "Eksik hammadde yok, talep oluşturulmadı."}
		mr = frappe.new_doc("Material Request")
		mr.material_request_type = "Purchase"
		mr.schedule_date = frappe.utils.nowdate()
		mr.company = frappe.db.get_value("Sales Order", sales_order, "company")
		mr.set("items", [])
		for item in shortage_items:
			mr.append("items", {
				"item_code": item["item_code"],
				"qty": item["qty"],
				"schedule_date": item["schedule_date"],
				"warehouse": None
			})
		mr.insert(ignore_permissions=True)
		mr.submit()
		return {
			"success": True,
			"message": "Satınalma Talebi başarıyla oluşturuldu.",
			"mr_name": mr.name,
			"created_rows": shortage_items
		}
	except Exception:
		frappe.log_error("create_material_request_for_shortages HATA", frappe.get_traceback())
		return {"success": False, "message": "Bir hata oluştu. Lütfen tekrar deneyin."}

def restore_long_term_reserve_on_purchase_receipt(doc, method):
	try:
		for item in getattr(doc, "items", []):
			item_code = item.item_code
			qty = float(item.qty or 0)
			# Bu item ile ilişkili tüm Long Term Reserve Usage kayıtlarını bul
			usage_rows = frappe.get_all(
				"Long Term Reserve Usage",
				filters={"item_code": item_code},
				fields=["name", "used_qty"]
			)
			for usage in usage_rows:
				usage_doc = frappe.get_doc("Long Term Reserve Usage", usage["name"])
				if qty >= usage_doc.used_qty:
					qty -= usage_doc.used_qty
					usage_doc.delete(ignore_permissions=True)
				else:
					usage_doc.used_qty -= qty
					usage_doc.save(ignore_permissions=True)
					qty = 0
				if qty <= 0:
					break
		frappe.db.commit()
		frappe.msgprint(_("Satınalma fişi ile ilişkili uzun vadeli rezerv kullanımları geri yüklendi."), indicator="green")
	except Exception:
		frappe.log_error("restore_long_term_reserve_on_purchase_receipt HATA", frappe.get_traceback())
 