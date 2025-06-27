import frappe
from frappe import _

@frappe.whitelist()
def get_sales_order_raw_materials(sales_order):
	# Kaydedilmemiş veya geçici bir Sales Order ise uyarı ver
	if not sales_order or sales_order.startswith("new-"):
		frappe.throw(_("Lütfen önce Satış Siparişini kaydedin."), frappe.ValidationError)
	try:
		so = frappe.get_doc("Sales Order", sales_order)
	except frappe.DoesNotExistError:
		frappe.throw(_("Sales Order bulunamadı."))
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
				bin_row = frappe.db.get_value("Bin", {"item_code": rm.item_code, "warehouse": item.warehouse}, ["actual_qty"], as_dict=True) or {"actual_qty": 0}
				raw_materials[key]["stock"] += bin_row["actual_qty"]
				raw_materials[key]["so_items"].add(item.item_code)
	# Sonuçları listeye çevir
	result = []
	for (raw_material, warehouse), data in raw_materials.items():
		kullanilabilir_stok = float(data["stock"] or 0) - float(data["reserved_qty"] or 0)
		acik_miktar = float(data["qty"] or 0) - kullanilabilir_stok

		# Malzeme Talep Miktarı (Material Request Item)
		mr_items = frappe.db.sql(
			"""
			SELECT mri.parent, mri.qty
			FROM `tabMaterial Request Item` mri
			INNER JOIN `tabMaterial Request` mr ON mri.parent = mr.name
			WHERE mri.item_code = %s AND mri.docstatus = 1 AND mr.material_request_type = 'Purchase'
			""",
			(raw_material,), as_dict=True
		)
		malzeme_talep_miktari = sum([row.qty for row in mr_items]) if mr_items else 0
		malzeme_talep_tooltip = ", ".join([f"{row.parent} ({row.qty})" for row in mr_items])
		# Sipariş Edilen Miktar ve Beklenen Teslim Tarihi (Purchase Order Item)
		po_items = frappe.db.sql(
			"""
			SELECT poi.parent, poi.qty, poi.schedule_date
			FROM `tabPurchase Order Item` poi
			INNER JOIN `tabPurchase Order` po ON poi.parent = po.name
			WHERE poi.item_code = %s AND poi.docstatus = 1 AND po.docstatus = 1 AND (poi.qty > IFNULL(poi.received_qty, 0))
			""",
			(raw_material,), as_dict=True
		)
		siparis_edilen_miktar = sum([row.qty for row in po_items]) if po_items else 0
		siparis_edilen_tooltip = ", ".join([f"{row.parent} ({row.qty})" for row in po_items])
		beklenen_teslim_tarihi = min([row.schedule_date for row in po_items if row.schedule_date], default=None)

		result.append({
			"raw_material": raw_material,
			"item_name": data["item_name"],
			"qty": data["qty"],
			"stock": data["stock"],
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
			"beklenen_teslim_tarihi": beklenen_teslim_tarihi
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

@frappe.whitelist()
def create_material_request_for_shortages(sales_order, submit=0):
	"""
	Satış siparişi içindeki shortage > 0 hammaddeler için Material Request (Purchase) oluşturur.
	submit=1 ise belgeyi direkt onaylar.
	"""
	raw_materials = get_sales_order_raw_materials(sales_order)
	shortage_items = [row for row in raw_materials if float(row.get("acik_miktar", 0)) > 0]
	if not shortage_items:
		return {"success": False, "message": "Açık miktarı olan hammadde yok."}

	shortage_items_to_request = []
	for item in shortage_items:
		existing = frappe.db.exists(
			"Material Request Item",
			{
				"item_code": item["raw_material"],
				"sales_order": sales_order,
				"docstatus": ["<", 2]
			}
		)
		if not existing:
			shortage_items_to_request.append(item)

	if not shortage_items_to_request:
		return {"success": False, "message": "Tüm eksikler için zaten talep oluşturulmuş."}

	mr = frappe.new_doc("Material Request")
	mr.material_request_type = "Purchase"
	mr.schedule_date = frappe.utils.add_days(frappe.utils.nowdate(), 3)  # İsteğe bağlı: 3 gün sonrası
	mr.set("sales_order", sales_order)
	created_rows = []
	for item in shortage_items_to_request:
		mr.append("items", {
			"item_code": item["raw_material"],
			"item_name": item["item_name"],
			"qty": item["acik_miktar"],
			"warehouse": None,  # İsteğe bağlı: birincil depo atanabilir
			"sales_order": sales_order,
			"schedule_date": mr.schedule_date
		})
		created_rows.append({
			"item_code": item["raw_material"],
			"qty": item["acik_miktar"]
		})
	mr.save(ignore_permissions=True)
	if int(submit):
		mr.submit()
	return {
		"success": True,
		"mr_name": mr.name,
		"created_rows": created_rows
	}

# Satış Siparişi submit edilirken stok kontrolü

def check_raw_material_stock_on_submit(doc, method=None):
	raw_materials = get_sales_order_raw_materials(doc.name)
	uyarilar = []
	for row in raw_materials:
		toplam_ihtiyac = float(row.get('qty') or 0)
		rezerve = float(row.get('reserved_qty') or 0)
		stok = float(row.get('stock') or 0)
		if (toplam_ihtiyac + rezerve) > stok:
			uyarilar.append(f"{row.get('raw_material')} için toplam ihtiyaç ({toplam_ihtiyac}) + rezerve ({rezerve}) > stok ({stok})!")
	if uyarilar:
		frappe.msgprint(_("Stok Yetersiz!\n\n" + "\n".join(uyarilar)))
 