import json
from datetime import datetime, timedelta

import frappe
from frappe import _


# FLOAT/PRECISION/TOLERANCE ile ilgili tüm fonksiyonlar kaldırıldı. Artık miktar işlemlerinde gelen qty olduğu gibi kullanılacaktır.

# Utility functions for quantity handling - Gerçek değerlerle çalışır, yuvarlama yapmaz
def get_real_qty(qty):
    """Get real quantity value without any rounding or precision changes"""
    if qty is None:
        return 0.0
    return float(qty)

def qty_equals(qty1, qty2):
    """Check if two quantities are exactly equal"""
    return get_real_qty(qty1) == get_real_qty(qty2)

def qty_greater_or_equal(qty1, qty2):
    """Check if qty1 is greater than or equal to qty2"""
    return get_real_qty(qty1) >= get_real_qty(qty2)

def safe_qty_compare(qty1, qty2):
    """Safely compare two quantities, returns True if qty1 >= qty2"""
    return qty_greater_or_equal(qty1, qty2)


def get_rezerv_map(item_codes):
	"""
	Verilen item_codes için tüm sales_order ve item_code kombinasyonlarında toplam rezerv miktarını döndürür.
	"""
	if not item_codes:
		return {}
	
	rezerv_rows = frappe.db.sql(
		"""
        SELECT sales_order, item_code, SUM(quantity) as quantity
        FROM `tabRezerved Raw Materials`
        WHERE item_code IN %s
        GROUP BY sales_order, item_code
        """,
		(tuple(item_codes),),
		as_dict=True,
	)
	rezerv_map = {}
	for row in rezerv_rows:
		rezerv_map[(row.sales_order, row.item_code)] = get_real_qty(row.quantity)
	return rezerv_map


def get_usage_map(item_codes):
	"""
	Verilen item_codes için tüm sales_order ve item_code kombinasyonlarında toplam kullanılan uzun vadeli rezerv miktarını döndürür.
	"""
	if not item_codes:
		return {}
	
	usage_rows = frappe.db.sql(
		"""
        SELECT sales_order, parent_sales_order, item_code, SUM(used_qty) as used_qty
        FROM `tabLong Term Reserve Usage`
        WHERE item_code IN %s
        GROUP BY sales_order, parent_sales_order, item_code
        """,
		(tuple(item_codes),),
		as_dict=True,
	)
	usage_map = {}
	for row in usage_rows:
		usage_map[(row.sales_order, row.item_code)] = get_real_qty(row.used_qty)
		if row.parent_sales_order:
			usage_map[(row.parent_sales_order, row.item_code)] = usage_map.get(
				(row.parent_sales_order, row.item_code), 0
			) + get_real_qty(row.used_qty)
		# Bağımsız usage kayıtları için (None, item_code) anahtarları da ekle
		if not row.sales_order:
			usage_map[(None, row.item_code)] = usage_map.get(
				(None, row.item_code), 0
			) + get_real_qty(row.used_qty)
	return usage_map


def get_stock_maps(item_codes):
	"""
	Verilen item_codes için toplam stok ve depo bazında stok miktarlarını döndürür.
	"""
	if not item_codes:
		return {}, {}
	
	bin_rows = frappe.db.get_all(
		"Bin",
		filters={"item_code": ["in", item_codes]},
		fields=["item_code", "warehouse", "actual_qty"],
	)
	stock_map = {}
	stock_by_warehouse_map = {}
	for row in bin_rows:
		stock_map[row.item_code] = get_real_qty(row.actual_qty)
		stock_by_warehouse_map.setdefault(row.item_code, {})[row.warehouse] = (
			get_real_qty(row.actual_qty)
		)
	return stock_map, stock_by_warehouse_map


def get_item_names(item_codes):
	"""
	Verilen item_codes için ürün isimlerini döndürür.
	"""
	if not item_codes:
		return {}
	
	item_names = {}
	for item in frappe.get_all(
		"Item",
		filters={"item_code": ["in", item_codes]},
		fields=["item_code", "item_name"],
	):
		item_names[item["item_code"]] = item["item_name"]
	return item_names


def get_reserve_warehouse_stock_map(item_codes, reserve_warehouse):
	"""
	Verilen item_codes için rezerv depodaki stok miktarlarını döndürür.
	"""
	if not item_codes or not reserve_warehouse:
		return {}
	
	reserve_warehouse_stock_map = {}
	reserve_bin_rows = frappe.db.get_all(
		"Bin",
		filters={"item_code": ["in", item_codes], "warehouse": reserve_warehouse},
		fields=["item_code", "actual_qty"],
	)
	for row in reserve_bin_rows:
		reserve_warehouse_stock_map[row.item_code] = get_real_qty(row.actual_qty)
	return reserve_warehouse_stock_map


@frappe.whitelist()
def get_sales_order_raw_materials(sales_order):
	"""
	Verilen satış siparişi için, siparişin item'ları üzerinden her bir hammaddeye ait toplam ihtiyaç, stok, rezerv, uzun vadeli rezerv ve kullanılan rezerv gibi bilgileri döndürür.
	Clean code ve performans için toplu sorgu ve yardımcı fonksiyonlar kullanır.
	"""
	if not sales_order or sales_order.startswith("new-"):
		frappe.throw(_("Lütfen önce Satış Siparişini kaydedin."), frappe.ValidationError)
	try:
		so = frappe.get_doc("Sales Order", sales_order)
	except frappe.DoesNotExistError:
		frappe.throw(_("Sales Order bulunamadı."))
	is_long_term_child = getattr(so, "is_long_term_child", 0)
	parent_sales_order = getattr(so, "parent_sales_order", None)
	raw_materials = {}

	# 1. Siparişteki tüm hammaddeleri topla
	all_item_codes = set()
	item_bom_map = {}
	for item in so.items:
		bom = frappe.db.get_value(
			"BOM", {"item": item.item_code, "is_active": 1, "is_default": 1}, "name"
		)
		if not bom:
			continue
		bom_doc = frappe.get_doc("BOM", bom)
		for rm in bom_doc.items:
			# Sadece gerçek hammadde olanlar eklensin
			is_hammadde = frappe.db.get_value(
				"Item", rm.item_code, ["is_stock_item", "is_purchase_item"], as_dict=True
			)
			if not is_hammadde or not (is_hammadde.is_stock_item and is_hammadde.is_purchase_item):
				continue  # Nihai ürün veya satılamaz/tedarik edilemez ürün, atla
			all_item_codes.add(rm.item_code)
			item_bom_map.setdefault(rm.item_code, []).append((item, rm))
	all_item_codes = list(all_item_codes)

	# Eğer hiç hammadde bulunamadıysa boş liste döndür
	if not all_item_codes:
		return []

	# 2. Toplu olarak rezerv, usage, stok, isim, depo verilerini çek (yardımcı fonksiyonlarla)
	# --- item_code'ları normalize et ---
	all_item_codes = [str(code).strip() for code in all_item_codes]
	rezerv_map = get_rezerv_map(all_item_codes)
	usage_map = get_usage_map(all_item_codes)
	stock_map, stock_by_warehouse_map = get_stock_maps(all_item_codes)
	item_names = get_item_names(all_item_codes)
	reserve_warehouse = (
		frappe.db.get_value(
			"Warehouse", {"name": ["in", ["REZERV DEPO", "REZERV DEPO - O"]]}, "name"
		)
		or ""
	)
	reserve_warehouse_stock_map = get_reserve_warehouse_stock_map(
		all_item_codes, reserve_warehouse
	)

	# --- YENİ: Her item için sistemdeki toplam rezerv ve uzun vadeli rezervi çek ---
	# Tüm aktif/onaylanmış siparişler için toplam rezerv (aktif rezerv)
	total_rezerv_rows = frappe.db.sql(
		"""
        SELECT item_code, SUM(quantity) as total_quantity
        FROM `tabRezerved Raw Materials`
        GROUP BY item_code
        """,
		as_dict=True,
	)
	total_rezerv_map = {
		row.item_code: get_real_qty(row.total_quantity) for row in total_rezerv_rows
	}

	# --- YENİ: Kullanılmış rezervleri (usage) da topla ---
	total_usage_rows = frappe.db.sql(
		"""
        SELECT item_code, SUM(used_qty) as total_used
        FROM `tabLong Term Reserve Usage`
        GROUP BY item_code
        """,
		as_dict=True,
	)
	total_usage_map = {
		row.item_code: get_real_qty(row.total_used) for row in total_usage_rows
	}

	# --- YENİ: Tüm aktif/onaylanmış uzun vadeli siparişler için toplam uzun vadeli rezerv ---
	today = frappe.utils.nowdate()
	thirty_days_later = (
		datetime.strptime(today, "%Y-%m-%d") + timedelta(days=30)
	).strftime("%Y-%m-%d")
	total_long_term_rows = frappe.db.sql(
		"""
        SELECT rrm.item_code, SUM(rrm.quantity) as total_long_term
        FROM `tabRezerved Raw Materials` rrm
        INNER JOIN `tabSales Order` so ON rrm.sales_order = so.name
        WHERE so.delivery_date >= %s
        GROUP BY rrm.item_code
        """,
		(thirty_days_later,),
		as_dict=True,
	)
	total_long_term_map = {
		row.item_code: get_real_qty(row.total_long_term) for row in total_long_term_rows
	}

	# --- Ana döngü ---
	for item_code, item_pairs in item_bom_map.items():
		item_code = str(item_code).strip()  # normalize
		# Parent/child ve uzun vadeli rezerv ayrımı
		long_term_reserve_qty = 0
		used_from_long_term_reserve = 0
		if is_long_term_child and parent_sales_order:
			# SADECE child usage alınacak, parent usage eklenmeyecek
			used_from_long_term_reserve = usage_map.get((so.name, item_code), 0)
			if so.docstatus == 1:
				long_term_reserve_qty = rezerv_map.get((so.name, item_code), 0)
			else:
				long_term_reserve_qty = rezerv_map.get((parent_sales_order, item_code), 0)
		else:
			long_term_key = (so.name, item_code)
			used_from_long_term_reserve = usage_map.get(long_term_key, 0) + usage_map.get(
				(None, item_code), 0
			)
			long_term_reserve_qty = rezerv_map.get(long_term_key, 0)
		# --- toplam rezerv detayları ---
		total_reserved_details = frappe.db.sql(
			"""
            SELECT rrm.sales_order, so.customer, IFNULL(so.custom_end_customer, '') as custom_end_customer, so.delivery_date, rrm.quantity,
                   so.is_long_term_child, so.parent_sales_order
            FROM `tabRezerved Raw Materials` rrm
            INNER JOIN `tabSales Order` so ON rrm.sales_order = so.name
            WHERE rrm.item_code = %s
        """,
			(item_code,),
			as_dict=True,
		)

		# --- YENİ: Child siparişlere aktarılan rezerv detaylarını ekle ---
		child_usage_details = frappe.db.sql(
			"""
            SELECT ltru.sales_order as child_sales_order, ltru.parent_sales_order, ltru.used_qty as quantity,
                   so.customer, IFNULL(so.custom_end_customer, '') as custom_end_customer, so.delivery_date,
                   so.is_long_term_child, so.parent_sales_order
            FROM `tabLong Term Reserve Usage` ltru
            INNER JOIN `tabSales Order` so ON ltru.sales_order = so.name
            WHERE ltru.item_code = %s AND ltru.parent_sales_order IS NOT NULL
        """,
			(item_code,),
			as_dict=True,
		)

		# Child usage detaylarını total_reserved_details'e ekle
		for child_detail in child_usage_details:
			# Child satırı için sales_order alanını child_sales_order olarak ayarla
			child_detail["sales_order"] = child_detail["child_sales_order"]
			child_detail["is_child_usage"] = (
				True  # Bu satırın child usage olduğunu belirt
			)
			total_reserved_details.append(child_detail)
		# İlk kez ekleniyorsa
		if item_code not in raw_materials:
			reserved_qty = rezerv_map.get((so.name, item_code), 0)
			stock_total = stock_map.get(item_code, 0)
			stock_by_warehouse = stock_by_warehouse_map.get(item_code, {})
			item_name = item_names.get(item_code, "")
			reserve_warehouse_stock = reserve_warehouse_stock_map.get(item_code, 0)
			# --- YENİ: toplam rezerv ve toplam uzun vadeli rezerv ---
			aktif_rezerv = total_rezerv_map.get(item_code, 0)
			kullanilmis_rezerv = total_usage_map.get(item_code, 0)
			toplam_rezerv = aktif_rezerv
			toplam_uzun_vadeli_rezerv = total_long_term_map.get(item_code, 0)
			raw_materials[item_code] = {
				"raw_material": item_code,
				"item_name": item_name,
				"qty": 0,
				"stock": stock_total,
				"stock_by_warehouse": stock_by_warehouse,
				"reserved_qty": reserved_qty,
				"reserve_warehouse": reserve_warehouse,
				"reserve_warehouse_stock": reserve_warehouse_stock,
				"so_items": set(),
						"long_term_reserve_qty": get_real_qty(long_term_reserve_qty),
		"used_from_long_term_reserve": get_real_qty(used_from_long_term_reserve),
				# --- yeni toplamlar ---
				"total_reserved_qty": toplam_rezerv,
				"total_long_term_reserve_qty": toplam_uzun_vadeli_rezerv,
				"total_reserved_details": total_reserved_details,
			}
		# Miktarları topla
		for item, rm in item_pairs:
			raw_materials[item_code]["qty"] += rm.qty
			raw_materials[item_code]["so_items"].add(item.item_code)

	result = []
	is_submitted = so.docstatus == 1
	for data in raw_materials.values():
		toplam_stok = get_real_qty(data["stock"] or 0)
		toplam_rezerv = get_real_qty(
			data["total_reserved_qty"] or 0
		)  # sistemdeki tüm rezervlerin toplamı
		if is_long_term_child and parent_sales_order:
			acik_miktar = get_real_qty(data["qty"] or 0)
			kullanilabilir_stok = 0
		else:
			kullanilabilir_stok = toplam_stok - toplam_rezerv
			acik_miktar = max(get_real_qty(data["qty"] or 0) - kullanilabilir_stok, 0)
		mr_items = frappe.db.sql(
			"""
            SELECT mri.parent, mri.qty, mr.transaction_date
            FROM `tabMaterial Request Item` mri
            INNER JOIN `tabMaterial Request` mr ON mri.parent = mr.name
            WHERE mri.item_code = %s
              AND mri.sales_order = %s
              AND mr.material_request_type = 'Purchase'
              AND mr.docstatus IN (0, 1)
              AND mr.status IN ('Draft', 'Pending', 'Partially Ordered', 'Partially Received', 'Ordered')
            """,
			(data["raw_material"], sales_order),
			as_dict=True,
		)
		# Sadece karşılanmamış (tamamlanmamış) talepleri göster
		filtered_mr_items = []
		for d in mr_items:
			received_qty_po = frappe.db.sql(
				"""
                SELECT SUM(received_qty)
                FROM `tabPurchase Order Item`
                WHERE material_request = %s
                  AND material_request_item = %s
                  AND item_code = %s
                """,
				(d["parent"], d.get("name", d["parent"]), data["raw_material"])
			)[0][0] or 0
			received_qty_pr = frappe.db.sql(
				"""
                SELECT SUM(received_qty)
                FROM `tabPurchase Receipt Item`
                WHERE material_request = %s
                  AND material_request_item = %s
                  AND item_code = %s
                """,
				(d["parent"], d.get("name", d["parent"]), data["raw_material"])
			)[0][0] or 0
			received_qty = max(get_real_qty(received_qty_po), get_real_qty(received_qty_pr))
			if get_real_qty(d["qty"]) - received_qty > 0:
				filtered_mr_items.append(d)
		mr_items = filtered_mr_items
		# Detayları normalize et
		for d in mr_items:
			d["qty"] = d.get("qty", "") or ""
			d["quantity"] = d["qty"]
			d["parent"] = d.get("parent", "") or ""
			d["name"] = d["parent"]
			d["transaction_date"] = str(d.get("transaction_date", "") or "")
			d["schedule_date"] = d["transaction_date"]
			d["date"] = d["transaction_date"]
		po_items = frappe.db.sql(
			"""
            SELECT poi.parent, poi.qty, poi.schedule_date, poi.received_qty
            FROM `tabPurchase Order Item` poi
            INNER JOIN `tabPurchase Order` po ON poi.parent = po.name
            WHERE poi.item_code = %s
              AND poi.docstatus = 1
              AND po.docstatus = 1
              AND (poi.qty > IFNULL(poi.received_qty, 0))
            """,
			(data["raw_material"],),
			as_dict=True,
		)
		# Sadece tamamlanmamış (kalan miktar > 0) olanları göster
		po_items = [d for d in po_items if get_real_qty(d.get("qty", 0)) > get_real_qty(d.get("received_qty", 0))]
		for d in po_items:
			d["qty"] = d.get("qty", "") or ""
			d["quantity"] = d["qty"]
			d["parent"] = d.get("parent", "") or ""
			d["name"] = d["parent"]
			d["schedule_date"] = str(d.get("schedule_date", "") or "")
			d["transaction_date"] = d["schedule_date"]
			d["date"] = d["schedule_date"]
		beklenen_teslim_tarihi = min(
			[row.schedule_date for row in po_items if row.schedule_date], default=None
		)
		long_term_details = get_long_term_reserve_details(data["raw_material"])
		for d in long_term_details:
			if not d.get("custom_end_customer") and d.get("sales_order"):
				d["custom_end_customer"] = (
					frappe.db.get_value(
						"Sales Order", d["sales_order"], "custom_end_customer"
					)
					or ""
				)
		used_long_term_details = get_used_long_term_reserve_details(data["raw_material"])
		for d in used_long_term_details:
			if not d.get("custom_end_customer") and d.get("sales_order"):
				d["custom_end_customer"] = (
					frappe.db.get_value(
						"Sales Order", d["sales_order"], "custom_end_customer"
					)
					or ""
				)
		result.append(
			{
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
				"used_long_term_details": used_long_term_details,
				# --- yeni toplamlar ---
				"total_reserved_qty": data["total_reserved_qty"],
				"total_long_term_reserve_qty": data["total_long_term_reserve_qty"],
				"total_reserved_details": data["total_reserved_details"],
				# Child bilgisini ekle
				"is_long_term_child": is_long_term_child,
				"parent_sales_order": parent_sales_order,
			}
		)
	return sorted(result, key=lambda x: get_real_qty(x.get("acik_miktar", 0)), reverse=True)


@frappe.whitelist()
def get_long_term_reserve_qty(item_code):
	qty = (
		frappe.db.sql(
			"""
        SELECT SUM(quantity)
        FROM `tabRezerved Raw Materials`
        WHERE item_code = %s
    """,
			(item_code,),
		)[0][0]
		or 0
	)
	return get_real_qty(qty)


def get_long_term_reserve_details(item_code):
	"""
	Verilen hammadde (item_code) için, teslim tarihi bugünden 30 gün sonrası ve daha ileri olan satış siparişlerine ait uzun vadeli rezerv detaylarını döndürür.
	Dönen detaylar: sales_order, customer, delivery_date, custom_end_customer, quantity
	"""
	thirty_days_later = (
		datetime.strptime(frappe.utils.nowdate(), "%Y-%m-%d") + timedelta(days=30)
	).strftime("%Y-%m-%d")
	rows = frappe.db.sql(
		"""
        SELECT so.name as sales_order, so.customer, so.delivery_date, IFNULL(so.custom_end_customer, '') as custom_end_customer, rrm.quantity
        FROM `tabRezerved Raw Materials` rrm
        INNER JOIN `tabSales Order` so ON rrm.sales_order = so.name
        WHERE rrm.item_code = %s AND so.delivery_date >= %s
    """,
		(item_code, thirty_days_later),
		as_dict=True,
	)
	# Eksik custom_end_customer varsa, satış siparişinden çek
	for row in rows:
		if not row.get("custom_end_customer") and row.get("sales_order"):
			row["custom_end_customer"] = (
				frappe.db.get_value(
					"Sales Order", row["sales_order"], "custom_end_customer"
				)
				or ""
			)
	return rows


def get_used_long_term_reserve_details(item_code):
	rows = frappe.db.sql(
		"""
        SELECT ltru.sales_order, ltru.parent_sales_order, ltru.used_qty, ltru.usage_date, so.customer, IFNULL(so.custom_end_customer, '') as custom_end_customer
        FROM `tabLong Term Reserve Usage` ltru
        INNER JOIN `tabSales Order` so ON ltru.sales_order = so.name
        WHERE ltru.item_code = %s
    """,
		(item_code,),
		as_dict=True,
	)
	for row in rows:
		if not row.get("custom_end_customer") and row.get("sales_order"):
			row["custom_end_customer"] = (
				frappe.db.get_value(
					"Sales Order", row["sales_order"], "custom_end_customer"
				)
				or ""
			)
	return rows


def update_or_delete_reserved_raw_material(row_name, consume_qty):
    """
    Rezerved Raw Materials kaydını verilen miktar kadar azaltır, sıfırlanırsa siler. Ek olarak, hata durumunda otomatik log atar.
    """
    try:
        rm_doc = frappe.get_doc("Rezerved Raw Materials", row_name)
        rm_doc.quantity = get_real_qty(rm_doc.quantity) - get_real_qty(consume_qty)
        if rm_doc.quantity <= 0:
            rm_doc.delete(ignore_permissions=True)
            frappe.logger().info(f"Rezerv {row_name} sifirlandi ve silindi. Kalan miktar: {rm_doc.quantity}")
        else:
            rm_doc.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"update_or_delete_reserved_raw_material ERROR: {e}", frappe.get_traceback())


def update_or_delete_long_term_reserve_usage(usage_name, consume_qty):
    """
    Long Term Reserve Usage kaydını verilen miktar kadar azaltır, sıfırlanırsa siler. Ek olarak hata durumunda log atar.
    """
    try:
        usage_doc = frappe.get_doc("Long Term Reserve Usage", usage_name)
        usage_doc.used_qty = get_real_qty(usage_doc.used_qty) - get_real_qty(consume_qty)
        if usage_doc.used_qty <= 0:
            usage_doc.delete(ignore_permissions=True)
            frappe.logger().info(f"Usage {usage_name} sifirlandi ve silindi. Kalan miktar: {usage_doc.used_qty}")
        else:
            usage_doc.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"update_or_delete_long_term_reserve_usage ERROR: {e}", frappe.get_traceback())


def release_reservations_on_stock_entry(doc, method):
	"""
	Üretim veya transfer (Stock Entry) işlemlerinde, ilgili satış siparişi ve hammadde için rezerv ve usage kayıtlarını kullanılan miktar kadar azaltır veya siler.
	Clean code için güncelleme/silme işlemleri yardımcı fonksiyonlara taşınmıştır.
	"""
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
			order_by="creation asc",
		)
		for row in reserved_rows:
			if qty_to_consume <= 0:
				break
			consume_qty = min(qty_to_consume, row.quantity or 0)
			update_or_delete_reserved_raw_material(row.name, consume_qty)
			qty_to_consume -= consume_qty
		long_term_rows = frappe.get_all(
			"Long Term Reserve Usage",
			filters={"sales_order": sales_order, "item_code": item.item_code},
			fields=["name", "used_qty"],
			order_by="creation asc",
		)
		for usage in long_term_rows:
			if qty_to_consume <= 0:
				break
			consume_qty = min(qty_to_consume, usage.used_qty or 0)
			update_or_delete_long_term_reserve_usage(usage.name, consume_qty)
			qty_to_consume -= consume_qty
	frappe.db.commit()
	frappe.msgprint(
		_("Stok hareketi ile ilişkili rezervler güncellendi."), indicator="green"
	)


def upsert_reserved_raw_material(
	sales_order, item_code, qty, item_name, customer, end_customer
):
	"""
	Verilen satış siparişi ve hammadde için Rezerved Raw Materials kaydını ekler veya günceller.
	"""
	# qty'yi normalize etmiyoruz
	existing = frappe.db.exists(
		"Rezerved Raw Materials", {"sales_order": sales_order, "item_code": item_code}
	)
	if existing:
		rm_doc = frappe.get_doc("Rezerved Raw Materials", existing)
		rm_doc.quantity = get_real_qty(qty)
		rm_doc.item_name = item_name
		rm_doc.customer = customer
		rm_doc.end_customer = end_customer
		rm_doc.save(ignore_permissions=True)
	else:
		rm_doc = frappe.new_doc("Rezerved Raw Materials")
		rm_doc.sales_order = sales_order
		rm_doc.item_code = item_code
		rm_doc.quantity = get_real_qty(qty)
		rm_doc.item_name = item_name
		rm_doc.customer = customer
		rm_doc.end_customer = end_customer
		rm_doc.insert(ignore_permissions=True)


def create_reserved_raw_materials_on_submit(doc, method):
	"""
	Satış siparişi submit edildiğinde, ilgili hammaddeler için Rezerved Raw Materials kaydını otomatik oluşturur veya günceller.
	Clean code için kayıt işlemleri yardımcı fonksiyona taşınmıştır.
	YENİ: Child (parça) siparişlerde rezerv oluşturulmaz!
	"""
	try:
		# Child siparişlerde rezerv oluşturulmaz
		if getattr(doc, "is_long_term_child", 0) or getattr(
			doc, "parent_sales_order", None
		):
			return
		raw_materials = get_sales_order_raw_materials(doc.name)
		for row in raw_materials:
			upsert_reserved_raw_material(
				sales_order=doc.name,
				item_code=row["raw_material"],
				qty=row["qty"],
				item_name=row["item_name"],
				customer=getattr(doc, "customer", ""),
				end_customer=getattr(doc, "custom_end_customer", ""),
			)
		frappe.db.commit()
		frappe.msgprint(
			_("{0} için rezerve oluşturuldu.").format(doc.name),
			alert=True,
			indicator="green",
		)
	except Exception:
		frappe.log_error("Sales Order submit hook HATA", frappe.get_traceback())


def delete_reserved_raw_materials_on_cancel(doc, method):
	try:
		# Child siparişlerde rezerve hammaddeler silinmemeli
		if getattr(doc, "is_long_term_child", 0) or getattr(
			doc, "parent_sales_order", None
		):
			return
		# Sadece kendi sales_order'ına ait rezervleri sil
		reserved = frappe.get_all(
			"Rezerved Raw Materials", filters={"sales_order": doc.name}, fields=["name"]
		)
		for row in reserved:
			frappe.delete_doc(
				"Rezerved Raw Materials", row["name"], ignore_permissions=True
			)
		frappe.db.commit()
		frappe.msgprint(
			_("{0} için rezerve iptal edildi.").format(doc.name),
			alert=True,
			indicator="orange",
		)
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
			"Rezerved Raw Materials", {"sales_order": sales_order, "item_code": item_code}
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
	frappe.msgprint(
		_("İş emri iptal edildi, rezervler tekrar eklendi."), indicator="orange"
	)


@frappe.whitelist()
def check_long_term_reserve_availability(sales_order):
	if not sales_order or sales_order.startswith("new-"):
		frappe.throw(_("Lütfen önce Satış Siparişini kaydedin."), frappe.ValidationError)
	so = frappe.get_doc("Sales Order", sales_order)
	is_long_term_child = getattr(so, "is_long_term_child", 0)
	parent_sales_order = getattr(so, "parent_sales_order", None)
	raw_materials = get_sales_order_raw_materials(sales_order)
	recommendations = []
	for row in raw_materials:
		acik_miktar = get_real_qty(row.get("acik_miktar", 0) or 0)
		item_code = row.get("raw_material")
		if is_long_term_child and parent_sales_order:
			parent_so = parent_sales_order
			parent_rezerv = get_real_qty(
				frappe.db.get_value(
					"Rezerved Raw Materials",
					{"sales_order": parent_so, "item_code": item_code},
					"quantity",
				)
			)
			total_usage = get_real_qty(
				frappe.db.sql(
					"""
                SELECT SUM(used_qty) FROM `tabLong Term Reserve Usage`
                WHERE (sales_order = %s OR parent_sales_order = %s) AND item_code = %s
            """,
					(parent_so, parent_so, item_code),
				)[0][0]
			)
			kalan_kullanilabilir = max(parent_rezerv - total_usage, 0)
			onerilen_kullanim = min(acik_miktar, kalan_kullanilabilir)
		else:
			# Bağımsız siparişler için sistemdeki tüm aktif uzun vadeli rezervleri item_code bazında bul
			# parent_rezerv = get_long_term_reserve_qty(item_code)
			parent_rezerv_result = get_long_term_reserve_details(item_code)
			parent_rezerv = (
				parent_rezerv_result[0].quantity if parent_rezerv_result else 0
			)

			total_usage = get_real_qty(
				frappe.db.sql(
					"""
                SELECT SUM(used_qty) FROM `tabLong Term Reserve Usage`
                WHERE item_code = %s
            """,
					(item_code,),
				)[0][0]
			)
			kalan_kullanilabilir = max(parent_rezerv - total_usage, 0)
			onerilen_kullanim = min(acik_miktar, kalan_kullanilabilir)
		if acik_miktar > 0 and parent_rezerv > 0 and onerilen_kullanim > 0:
			recommendations.append(
				{
					"item_code": item_code,
					"item_name": row.get("item_name"),
								"acik_miktar": get_real_qty(acik_miktar or 0),
			"uzun_vadeli_rezerv": get_real_qty(parent_rezerv or 0),
			"kullanilan_rezerv": get_real_qty(total_usage or 0),
			"kullanilabilir_uzun_vadeli": get_real_qty(kalan_kullanilabilir or 0),
			"onerilen_kullanim": get_real_qty(onerilen_kullanim or 0),
					"gecici_kullanim": not is_long_term_child and not parent_sales_order,
				}
			)
	return recommendations


def delete_long_term_reserve_usage_on_cancel(doc, method):
	sales_order = getattr(doc, "name", None)
	if not sales_order:
		return
	try:
		is_long_term_child = getattr(doc, "is_long_term_child", 0)
		parent_sales_order = getattr(doc, "parent_sales_order", None)
		usage_rows = frappe.get_all(
			"Long Term Reserve Usage",
			filters={"sales_order": sales_order},
			fields=["name", "item_code", "used_qty"],
		)
		for row in usage_rows:
			# Child usage ise parent rezervi geri ekle
			if is_long_term_child and parent_sales_order:
				parent_reserve = frappe.get_all(
					"Rezerved Raw Materials",
					filters={
						"sales_order": parent_sales_order,
						"item_code": row["item_code"],
					},
					fields=["name", "quantity"],
				)
				if parent_reserve:
					reserve_doc = frappe.get_doc(
						"Rezerved Raw Materials", parent_reserve[0]["name"]
					)
					reserve_doc.quantity = get_real_qty(
						reserve_doc.quantity + get_real_qty(row["used_qty"])
					)
					reserve_doc.save(ignore_permissions=True)
				else:
					upsert_reserved_raw_material(
						sales_order=parent_sales_order,
						item_code=row["item_code"],
						qty=get_real_qty(float(row["used_qty"])),
						item_name=frappe.db.get_value(
							"Item", row["item_code"], "item_name"
						)
						or "",
						customer=getattr(doc, "customer", ""),
						end_customer=getattr(doc, "custom_end_customer", ""),
					)
			frappe.delete_doc(
				"Long Term Reserve Usage", row["name"], ignore_permissions=True
			)
		frappe.db.commit()
		frappe.msgprint(
			_(
				"{0} için uzun vadeli rezerv kullanımları silindi ve parent rezervler geri yüklendi."
			).format(sales_order),
			alert=True,
			indicator="orange",
		)
	except Exception:
		frappe.log_error(
			"Sales Order cancel hook (delete_long_term_reserve_usage_on_cancel) HATA",
			frappe.get_traceback(),
		)


def check_raw_material_stock_on_submit(doc, method):
	# --- PASİF ---
	# Stok ve rezerv kontrolü şimdilik devre dışı bırakıldı. İleride tekrar açılabilir.
	pass


def upsert_long_term_reserve_usage(
	sales_order, item_code, qty, is_long_term_child, parent_sales_order
):
	"""
	Verilen satış siparişi ve hammadde için Long Term Reserve Usage kaydını ekler veya günceller.
	Child siparişlerde parent_sales_order referansı da eklenir.
	"""
	# qty'yi normalize etmiyoruz
	existing = frappe.get_all(
		"Long Term Reserve Usage",
		filters={"sales_order": sales_order, "item_code": item_code},
		fields=["name"],
	)
	if existing:
		usage_doc = frappe.get_doc("Long Term Reserve Usage", existing[0]["name"])
		usage_doc.used_qty = get_real_qty(qty)  # <-- Birikmeli değil, yeni miktarı yaz
		usage_doc.usage_date = frappe.utils.nowdate()
		if is_long_term_child and parent_sales_order:
			usage_doc.parent_sales_order = parent_sales_order
		usage_doc.save(ignore_permissions=True)
	else:
		usage_doc = frappe.new_doc("Long Term Reserve Usage")
		usage_doc.sales_order = sales_order
		usage_doc.item_code = item_code
		usage_doc.used_qty = get_real_qty(qty)
		usage_doc.usage_date = frappe.utils.nowdate()
		if is_long_term_child and parent_sales_order:
			usage_doc.parent_sales_order = parent_sales_order
		usage_doc.insert(ignore_permissions=True)


@frappe.whitelist()
def use_long_term_reserve_bulk(sales_order, usage_data):
	"""
	Bir satış siparişi için, verilen hammaddeler ve miktarlar kadar uzun vadeli rezerv kullanımını kaydeder.
	Child siparişlerde ana rezervden düşer ve usage kaydında parent_sales_order referansını ekler.
	Bağımsız siparişlerde hem usage kaydı oluşturulur hem de kendi adına rezerv kaydı açılır (toplam rezerv artar, ana rezerv azalır).
	Clean code için kayıt işlemleri yardımcı fonksiyona taşınmıştır.
	"""
	if not sales_order or not usage_data:
		return {"success": False, "message": "Eksik parametre."}
	try:
		so = frappe.get_doc("Sales Order", sales_order)
		is_long_term_child = getattr(so, "is_long_term_child", 0)
		parent_sales_order = getattr(so, "parent_sales_order", None)
		usage_list = json.loads(usage_data)
		for usage in usage_list:
			item_code = str(usage.get("item_code")).strip()
			qty = get_real_qty(usage.get("qty", 0))
			if not item_code or qty <= 0:
				continue
			# Parent'ı belirle
			if is_long_term_child and parent_sales_order:
				parent_so = parent_sales_order
				parent_rezerv = get_real_qty(
					frappe.db.get_value(
						"Rezerved Raw Materials",
						{"sales_order": parent_so, "item_code": item_code},
						"quantity",
					)
				)
			else:
				# BAĞIMSIZ SİPARİŞ: Tüm uzun vadeli rezervlerin toplamı alınmalı
				parent_rezerv = get_long_term_reserve_qty(item_code)
			# Parent'ın toplam usage'ı (tüm usage kayıtları)
			if is_long_term_child and parent_sales_order:
				total_usage = get_real_qty(
					frappe.db.sql(
						"""
                    SELECT SUM(used_qty) FROM `tabLong Term Reserve Usage`
                    WHERE (sales_order = %s OR parent_sales_order = %s) AND item_code = %s
                """,
						(parent_so, parent_so, item_code),
					)[0][0]
				)
			else:
				total_usage = get_real_qty(
					frappe.db.sql(
						"""
                    SELECT SUM(used_qty) FROM `tabLong Term Reserve Usage`
                    WHERE item_code = %s
                """,
						(item_code,),
					)[0][0]
				)
			kalan_kullanilabilir = max(parent_rezerv - total_usage, 0)
			if not safe_qty_compare(kalan_kullanilabilir, qty):
				return {
					"success": False,
					"message": f"{item_code} için toplam uzun vadeli rezerv miktarı aşılamaz! (Kalan: {kalan_kullanilabilir})",
				}
			if is_long_term_child and parent_sales_order:
				# Child: Sadece usage kaydı oluştur, parent rezervi düşür, child'a yeni rezerv OLUŞTURMA!
				upsert_long_term_reserve_usage(
					sales_order=sales_order,
					item_code=item_code,
					qty=qty,
					is_long_term_child=is_long_term_child,
					parent_sales_order=parent_sales_order,
				)
				parent_reserve = frappe.get_all(
					"Rezerved Raw Materials",
					filters={"sales_order": parent_sales_order, "item_code": item_code},
					fields=["name", "quantity"],
				)
				if parent_reserve:
					reserve_doc = frappe.get_doc(
						"Rezerved Raw Materials", parent_reserve[0]["name"]
					)
					reserve_doc.quantity -= qty
					if get_real_qty(reserve_doc.quantity) <= 0:
						reserve_doc.delete(ignore_permissions=True)
					else:
						reserve_doc.save(ignore_permissions=True)
				# Child'a yeni rezerv oluşturulmaz!
			else:
				# Bağımsız sipariş: hem usage kaydı hem kendi adına rezerv aç
				upsert_long_term_reserve_usage(
					sales_order=sales_order,
					item_code=item_code,
					qty=qty,
					is_long_term_child=is_long_term_child,
					parent_sales_order=parent_sales_order,
				)
				upsert_reserved_raw_material(
					sales_order=sales_order,
					item_code=item_code,
					qty=qty,
					item_name=frappe.db.get_value("Item", item_code, "item_name") or "",
					customer=getattr(so, "customer", ""),
					end_customer=getattr(so, "custom_end_customer", ""),
				)
		frappe.db.commit()
		return {
			"success": True,
			"message": "Uzun vadeli rezerv kullanımı başarıyla kaydedildi.",
		}
	except Exception:
		frappe.log_error("use_long_term_reserve_bulk HATA", frappe.get_traceback())
		return {"success": False, "message": "Bir hata oluştu. Lütfen tekrar deneyin."}


# Bağımsız sipariş tamamlanınca veya iptal edilince usage kayıtlarını sil (ana rezerv değişmez)


@frappe.whitelist()
def get_long_term_reserve_usage_summary(parent_sales_order):
	# Ana siparişin toplam uzun vadeli rezervi
	ana_rezerv = frappe.db.sql(
		"""
        SELECT SUM(quantity) as total
        FROM `tabRezerved Raw Materials` rrm
        WHERE rrm.sales_order = %s
    """,
		(parent_sales_order,),
		as_dict=True,
	)
	return ana_rezerv


@frappe.whitelist()
def clear_remaining_reserves(parent_sales_order, reason=None):
	"""
	Ana (parent) satış siparişine ait kalan uzun vadeli rezervleri topluca siler.
	Silinen rezervler için Deleted Long Term Reserve doctype'ında kalıcı kayıt oluşturur.
	"""
	if not parent_sales_order:
		return {"success": False, "message": "Ana satış siparişi belirtilmedi."}
	try:
		rezervler = frappe.get_all(
			"Rezerved Raw Materials",
			filters={"sales_order": parent_sales_order},
			fields=["name", "item_code", "quantity", "customer", "end_customer"],
		)
		for row in rezervler:
			# Silinen rezerv için kalıcı kayıt oluştur
			deleted_doc = frappe.new_doc("Deleted Long Term Reserve")
			deleted_doc.sales_order = parent_sales_order
			deleted_doc.item_code = row["item_code"]
			deleted_doc.quantity = row["quantity"]
			deleted_doc.customer = row["customer"]
			deleted_doc.end_customer = row["end_customer"]
			deleted_doc.deleted_by = frappe.session.user
			deleted_doc.deleted_at = frappe.utils.now()
			if reason:
				deleted_doc.reason = reason
			deleted_doc.insert(ignore_permissions=True)
			frappe.delete_doc(
				"Rezerved Raw Materials", row["name"], ignore_permissions=True
			)
		frappe.db.commit()
		return {"success": True, "message": "Kalan uzun vadeli rezervler silindi."}
	except Exception:
		frappe.log_error("clear_remaining_reserves HATA", frappe.get_traceback())
		return {"success": False, "message": "Bir hata oluştu. Lütfen tekrar deneyin."}


def delete_long_term_reserve_usage_on_delivery_or_invoice(doc, method):
	sales_order = getattr(doc, "sales_order", None) or getattr(doc, "name", None)
	if not sales_order:
		return
	try:
		usage_rows = frappe.get_all(
			"Long Term Reserve Usage",
			filters={"sales_order": sales_order},
			fields=["name"],
		)
		for row in usage_rows:
			frappe.delete_doc(
				"Long Term Reserve Usage", row["name"], ignore_permissions=True
			)
		frappe.db.commit()
		frappe.msgprint(
			_("{0} için uzun vadeli rezerv kullanımları silindi.").format(sales_order),
			alert=True,
			indicator="orange",
		)
	except Exception:
		frappe.log_error(
			"Delivery/Invoice/StockEntry/WorkOrder hook (delete_long_term_reserve_usage_on_delivery_or_invoice) HATA",
			frappe.get_traceback(),
		)


def restore_reserved_raw_materials_on_cancel(doc, method):
	sales_order = getattr(doc, "name", None)
	if not sales_order:
		return
	try:
		reserved = frappe.get_all(
			"Rezerved Raw Materials",
			filters={"sales_order": sales_order},
			fields=["name"],
		)
		for row in reserved:
			frappe.delete_doc(
				"Rezerved Raw Materials", row["name"], ignore_permissions=True
			)
		frappe.db.commit()
		frappe.msgprint(
			_("{0} için rezerve iptal edildi.").format(sales_order),
			alert=True,
			indicator="orange",
		)
	except Exception:
		frappe.log_error(
			"Sales Order cancel hook (restore_reserved_raw_materials_on_cancel) HATA",
			frappe.get_traceback(),
		)


def handle_child_sales_order_reserves(doc, method):
	if not getattr(doc, "is_long_term_child", 0) or not getattr(
		doc, "parent_sales_order", None
	):
		return

	parent_so = doc.parent_sales_order
	# 1. Child'ın tüm item'ları için BOM'dan çıkan hammaddeleri ve miktarlarını topla
	toplam_ihtiyac = {}
	for item in doc.items:
		bom = frappe.db.get_value(
			"BOM", {"item": item.item_code, "is_active": 1, "is_default": 1}, "name"
		)
		if not bom:
			continue
		bom_doc = frappe.get_doc("BOM", bom)
		for rm in bom_doc.items:
			hammadde_code = str(rm.item_code).strip()
			ihtiyac = get_real_qty(rm.qty * item.qty)
			toplam_ihtiyac[hammadde_code] = toplam_ihtiyac.get(hammadde_code, 0) + ihtiyac
	# 2. Her hammadde için parent rezervde yeterli miktar var mı kontrol et
	for hammadde_code, ihtiyac_raw in toplam_ihtiyac.items():
		ihtiyac = get_real_qty(ihtiyac_raw)
		parent_reserve = frappe.get_all(
			"Rezerved Raw Materials",
			filters={"sales_order": parent_so, "item_code": hammadde_code},
			fields=["name", "quantity"],
		)
		if parent_reserve:
			mevcut_rezerv = get_real_qty(parent_reserve[0]["quantity"])
			if safe_qty_compare(mevcut_rezerv, ihtiyac):
				# 3. Usage ve düşüm işlemini tek seferde yap
				reserve_doc = frappe.get_doc(
					"Rezerved Raw Materials", parent_reserve[0]["name"]
				)
				reserve_doc.quantity = get_real_qty(reserve_doc.quantity - ihtiyac)
				if get_real_qty(reserve_doc.quantity) <= 0:
					reserve_doc.delete(ignore_permissions=True)
				else:
					reserve_doc.save(ignore_permissions=True)
				upsert_long_term_reserve_usage(
					sales_order=doc.name,
					item_code=hammadde_code,
					qty=ihtiyac,
					is_long_term_child=True,
					parent_sales_order=parent_so,
				)
			else:
				frappe.throw(
					_(
						f"Ana siparişte {hammadde_code} için yeterli uzun vadeli rezerv yok! (Gereken: {ihtiyac}, Mevcut: {mevcut_rezerv}, Fark: {abs(mevcut_rezerv - ihtiyac):.4f})"
					)
				)
		else:
			frappe.throw(
				_(f"Ana siparişte {hammadde_code} için yeterli uzun vadeli rezerv yok!")
			)
	frappe.db.commit()
	frappe.msgprint(_("Satış siparişi için rezervler güncellendi."), indicator="green")


@frappe.whitelist()
def create_material_request_for_shortages(sales_order):
    """
    Bu Siparişe Ait Eksikler İçin Satınalma Talebi Oluştur butonu için:
    Sadece ilgili satış siparişi için eksik hammaddelerden satınalma talebi oluşturur.
    Aynı sipariş ve hammadde için açık bir talep varsa tekrar oluşturmaz.
    """
    if not sales_order:
        return {"success": False, "message": "Satış Siparişi bulunamadı."}
    try:
        # Satış siparişi için açık veya onaylanmış bir Material Request var mı? (ana belge seviyesinde kontrol)
        existing_mr = frappe.db.sql("""
            SELECT mr.name
            FROM `tabMaterial Request` mr
            INNER JOIN `tabMaterial Request Item` mri ON mri.parent = mr.name
            WHERE mri.sales_order = %s
              AND mr.material_request_type = 'Purchase'
              AND mr.docstatus IN (0, 1)
            LIMIT 1
        """, (sales_order,))
        if existing_mr:
            return {
                "success": False,
                "message": "Bu satış siparişi için zaten bir malzeme talebi var. Lütfen mevcut talebi kullanın.",
            }
        raw_materials = get_sales_order_raw_materials(sales_order)
        shortage_items = []
        for row in raw_materials:
            acik_miktar = get_real_qty(row.get("acik_miktar", 0))
            item_code = row.get("raw_material")
            if acik_miktar > 0:
                # Performanslı kontrol: Bu sipariş ve hammadde için açık bir talep var mı?
                existing = frappe.db.sql(
                    """
                    SELECT mri.name FROM `tabMaterial Request Item` mri
                    INNER JOIN `tabMaterial Request` mr ON mri.parent = mr.name
                    WHERE mri.item_code = %s
                      AND mri.sales_order = %s
                      AND mr.material_request_type = 'Purchase'
                      AND mr.docstatus != 1
                    LIMIT 1
                    """,
                    (item_code, sales_order),
                )
                if existing:
                    continue  # Zaten açık talep var, tekrar oluşturma
                shortage_items.append(
                    {
                        "item_code": item_code,
                        "qty": acik_miktar,
                        "schedule_date": frappe.utils.nowdate(),
                    }
                )
        if not shortage_items:
            return {
                "success": False,
                "message": "Bu siparişe ait eksik hammadde için zaten açık bir talep var veya eksik yok.",
            }
        mr = frappe.new_doc("Material Request")
        mr.material_request_type = "Purchase"
        mr.schedule_date = frappe.utils.nowdate()
        mr.company = frappe.db.get_value("Sales Order", sales_order, "company")
        mr.set("items", [])
        for item in shortage_items:
            mr.append(
                "items",
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "schedule_date": item["schedule_date"],
                    "warehouse": None,
                    "sales_order": sales_order,  # Satış siparişi ile ilişkilendir
                },
            )
        mr.insert(ignore_permissions=True)
        mr.submit()
        return {
            "success": True,
            "message": "Bu siparişe ait eksikler için satınalma talebi başarıyla oluşturuldu.",
            "mr_name": mr.name,
            "created_rows": shortage_items,
        }
    except Exception:
        frappe.log_error(
            "create_material_request_for_shortages HATA", frappe.get_traceback()
        )
        return {"success": False, "message": "Bir hata oluştu. Lütfen tekrar deneyin."}


# Cam ürünü tespit fonksiyonu (sade)
def is_glass_item(item_code, item_name, item_group=None):
    return (item_group or "").lower() == "camlar"


# ADMİN/CRON için otomatik rezerv temizlik utility
def cleanup_unused_reserves():
    """
    Sıfır ve negatif rezerve sahip tüm satırları temizler (admin/cron ile).
    """
    rows = frappe.get_all("Rezerved Raw Materials", fields=["name", "quantity"])
    deleted = 0
    for row in rows:
        try:
            if get_real_qty(row['quantity']) <= 0.0:
                frappe.delete_doc("Rezerved Raw Materials", row["name"], ignore_permissions=True)
                deleted += 1
        except Exception as e:
            frappe.log_error(f"Cleanup reserve error: {e}")
    frappe.logger().info(f"Rezerv Temizlik: {deleted} satır silindi.")
    return f"{deleted} rezerve satırı silindi."

@frappe.whitelist()
def create_material_request_for_all_shortages():
    """
    Tüm Siparişlere Ait Eksikler İçin Satınalma Talebi Oluştur butonu için:
    YÜKSEK PERFORMANSLI: Tüm satış siparişlerindeki eksik hammaddeleri topluca tespit edip,
    her bir hammadde için toplam açık miktar kadar tek bir satınalma talebi oluşturur.
    Cam ürünleri (item_group="Camlar") eklenmez, ama cam ürünlerinin BOM'undaki hammaddeler eklenir.
    """
    try:
        # 1. Tüm aktif satış siparişlerini tek sorguda al
        sales_orders = frappe.get_all(
            "Sales Order",
            filters={"docstatus": 1},
            fields=["name", "company"]
        )
        if not sales_orders:
            return {"success": False, "message": "Aktif satış siparişi yok."}

        # 2. Tüm satış siparişi item'larını tek sorguda al
        all_so_names = [so["name"] for so in sales_orders]
        so_items = frappe.get_all(
            "Sales Order Item",
            filters={"parent": ["in", all_so_names]},
            fields=["parent", "item_code", "qty"]
        )

        # 3. Tüm item'ları topla ve BOM'ları tek seferde al
        all_item_codes = set(item["item_code"] for item in so_items)
        
        # 4. Tüm BOM'ları tek sorguda al
        if not all_item_codes:
            return {
                "success": True,
                "message": "Hiç ürün bulunamadı veya BOM tanımlı değil.",
                "mr_name": None,
                "created_rows": {},
            }
        
        bom_data = frappe.db.sql("""
            SELECT bom.item, bom_item.item_code, bom_item.qty
            FROM `tabBOM` bom
            INNER JOIN `tabBOM Item` bom_item ON bom.name = bom_item.parent
            WHERE bom.item IN %s AND bom.is_active = 1 AND bom.is_default = 1
        """, (tuple(all_item_codes),), as_dict=True)

        # 5. BOM verilerini organize et
        bom_map = {}
        all_raw_materials = set()
        for bom_item in bom_data:
            item_code = bom_item["item"]
            raw_material = bom_item["item_code"]
            qty = bom_item["qty"]
            
            if item_code not in bom_map:
                bom_map[item_code] = []
            bom_map[item_code].append({"item_code": raw_material, "qty": qty})
            all_raw_materials.add(raw_material)

        # 6. Tüm item özelliklerini tek sorguda al
        all_items = list(all_item_codes | all_raw_materials)
        item_features = {}
        for item in frappe.get_all(
            "Item",
            filters={"item_code": ["in", all_items]},
            fields=["item_code", "item_name", "item_group", "is_stock_item", "is_purchase_item"]
        ):
            item_features[item["item_code"]] = item

        # 7. Tüm stok verilerini tek sorguda al
        if not all_raw_materials:
            return {
                "success": True,
                "message": "Hiç hammadde bulunamadı.",
                "mr_name": None,
                "created_rows": {},
            }
        
        stock_data = frappe.db.sql("""
            SELECT item_code, SUM(actual_qty) as total_stock
            FROM `tabBin`
            WHERE item_code IN %s
            GROUP BY item_code
        """, (tuple(all_raw_materials),), as_dict=True)
        
        stock_map = {row["item_code"]: get_real_qty(row["total_stock"]) for row in stock_data}

        # 8. Tüm rezerv verilerini tek sorguda al
        rezerv_data = frappe.db.sql("""
            SELECT item_code, SUM(quantity) as total_reserved
            FROM `tabRezerved Raw Materials`
            WHERE item_code IN %s
            GROUP BY item_code
        """, (tuple(all_raw_materials),), as_dict=True)
        
        rezerv_map = {row["item_code"]: get_real_qty(row["total_reserved"]) for row in rezerv_data}

        # 9. Yardımcı fonksiyonlar
        def is_glass(item_code):
            return (item_features.get(item_code, {}).get("item_group", "").lower() == "camlar")
        
        def is_real_raw(item_code):
            f = item_features.get(item_code, {})
            return f.get("is_stock_item") and f.get("is_purchase_item")

        # 10. Her satış siparişi için hammadde ihtiyaçlarını hesapla
        total_shortages = {}
        
        for so_item in so_items:
            sales_order = so_item["parent"]
            item_code = so_item["item_code"]
            qty = get_real_qty(so_item["qty"])
            
            # BOM'dan hammaddeleri al
            bom_items = bom_map.get(item_code, [])
            
            for bom_item in bom_items:
                raw_material = bom_item["item_code"]
                bom_qty = get_real_qty(bom_item["qty"])
                
                # Cam ürünü ise, BOM'undaki hammaddeleri ekle
                if is_glass(item_code):
                    if is_real_raw(raw_material):
                        total_needed = bom_qty * qty
                        total_shortages[raw_material] = total_shortages.get(raw_material, 0) + total_needed
                    continue
                
                # Sadece gerçek hammadde olanlar
                if not is_real_raw(raw_material):
                    continue
                
                if is_glass(raw_material):
                    continue
                
                # Toplam ihtiyaç hesapla
                total_needed = bom_qty * qty
                
                # Stok ve rezerv kontrolü
                available_stock = stock_map.get(raw_material, 0)
                total_reserved = rezerv_map.get(raw_material, 0)
                usable_stock = max(available_stock - total_reserved, 0)
                
                # Açık miktar hesapla
                shortage = max(total_needed - usable_stock, 0)
                
                if shortage > 0:
                    total_shortages[raw_material] = total_shortages.get(raw_material, 0) + shortage

        if not total_shortages:
            return {
                "success": True,
                "message": "Tüm siparişlere ait eksik hammadde yok, talep oluşturulmadı.",
                "mr_name": None,
                "created_rows": {},
            }

        # 11. Material Request oluştur
        mr = frappe.new_doc("Material Request")
        mr.material_request_type = "Purchase"
        mr.schedule_date = frappe.utils.nowdate()
        mr.company = sales_orders[0]["company"] if sales_orders else None
        mr.set("items", [])
        
        for item_code, qty in total_shortages.items():
            mr.append(
                "items",
                {
                    "item_code": item_code,
                    "qty": qty,
                    "schedule_date": frappe.utils.nowdate(),
                    "warehouse": None,
                },
            )
        
        mr.insert(ignore_permissions=True)
        mr.submit()
        
        return {
            "success": True,
            "message": f"Tüm siparişlere ait eksikler için satınalma talebi başarıyla oluşturuldu. {mr.name}",
            "mr_name": mr.name,
            "created_rows": total_shortages,
        }
    except Exception as e:
        frappe.log_error("create_material_request_for_all_shortages HATA", frappe.get_traceback())
        return {
            "success": False,
            "message": f"Bir hata oluştu: {str(e)}. Lütfen tekrar deneyin.",
            "mr_name": None,
            "created_rows": {},
        }


@frappe.whitelist()
def test_quantity_comparison():
	"""
	Test function to verify quantity comparison logic works correctly.
	"""
	test_cases = [
		(33.41, 33.4, "Should NOT be equal (different values)"),
		(33.4, 33.41, "Should NOT be equal (different values)"),
		(15.44, 15.44, "Should be exactly equal"),
		(15.0, 15.00, "Should be exactly equal (different precision)"),
		(10.05, 10.01, "Should NOT be equal (different values)"),
		(10.1, 10.05, "Should NOT be equal (different values)"),
	]

	results = []
	for qty1, qty2, description in test_cases:
		norm_qty1 = get_real_qty(qty1)
		norm_qty2 = get_real_qty(qty2)
		is_equal = qty_equals(norm_qty1, norm_qty2)
		is_greater_equal = qty_greater_or_equal(norm_qty1, norm_qty2)
		safe_compare = safe_qty_compare(norm_qty1, norm_qty2)

		results.append(
			{
				"description": description,
				"qty1": qty1,
				"qty2": qty2,
				"norm_qty1": norm_qty1,
				"norm_qty2": norm_qty2,
				"difference": abs(norm_qty1 - norm_qty2),
				"qty_equals": is_equal,
				"qty_greater_or_equal": is_greater_equal,
				"safe_qty_compare": safe_compare,
			}
		)

	return results


def remove_reservations_on_work_order_complete(doc, method):
    """
    İş emri tamamlandığında (stok hareketi oluşmuyorsa), ilgili satış siparişi ve hammaddeler için rezervleri azaltır veya siler.
    """
    if getattr(doc, "status", None) != "Completed":
        return
    sales_order = getattr(doc, "sales_order", None)
    if not sales_order:
        return
    for item in getattr(doc, "required_items", []):
        item_code = item.item_code
        qty_to_consume = abs(getattr(item, "required_qty", 0))
        reserved_rows = frappe.get_all(
            "Rezerved Raw Materials",
            filters={"sales_order": sales_order, "item_code": item_code},
            fields=["name", "quantity"],
            order_by="creation asc",
        )
        for row in reserved_rows:
            if qty_to_consume <= 0:
                break
            consume_qty = min(qty_to_consume, row["quantity"] or 0)
            update_or_delete_reserved_raw_material(row["name"], consume_qty)
            qty_to_consume -= consume_qty
    frappe.db.commit()
    frappe.msgprint(_("İş emri tamamlandı, rezervler güncellendi."), indicator="green")
