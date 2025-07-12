import json
from datetime import datetime, timedelta

import frappe
from frappe import _


# --- Miktar normalize fonksiyonu ---
def normalize_qty(qty, ndigits=2):
	"""
	Tüm miktar işlemlerinde kullanılacak normalize fonksiyonu. EPSILON yok, sadece round.
	Decimal precision için varsayılan 2 hane kullanılır.
	"""
	try:
		result = round(float(qty or 0), ndigits)
		# Çok küçük sayıları sıfır olarak kabul et
		if abs(result) < 0.001:
			return 0.0
		return result
	except Exception:
		return 0.0


def qty_equals(qty1, qty2, tolerance=0.05):
	"""
	İki miktar değerini tolerans ile karşılaştırır. Floating point hassasiyet sorunları için.
	0.02 toleransı 2 ondalık basamağa uygun.
	"""
	return abs(float(qty1 or 0) - float(qty2 or 0)) <= tolerance


def qty_greater_or_equal(qty1, qty2, tolerance=0.05):
	"""
	qty1 >= qty2 karşılaştırması tolerans ile yapar. Floating point hassasiyet sorunları için.
	0.02 toleransı 2 ondalık basamağa uygun.
	"""
	return float(qty1 or 0) >= float(qty2 or 0) - tolerance


def safe_qty_compare(qty1, qty2):
	"""
	İki miktarı güvenli şekilde karşılaştırır. Normalize edilmiş değerlerle tolerans kullanır.
	"""
	norm_qty1 = normalize_qty(qty1)
	norm_qty2 = normalize_qty(qty2)
	return qty_greater_or_equal(norm_qty1, norm_qty2)


def get_rezerv_map(item_codes):
	"""
	Verilen item_codes için tüm sales_order ve item_code kombinasyonlarında toplam rezerv miktarını döndürür.
	"""
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
		rezerv_map[(row.sales_order, row.item_code)] = normalize_qty(row.quantity)
	return rezerv_map


def get_usage_map(item_codes):
	"""
	Verilen item_codes için tüm sales_order ve item_code kombinasyonlarında toplam kullanılan uzun vadeli rezerv miktarını döndürür.
	"""
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
		usage_map[(row.sales_order, row.item_code)] = normalize_qty(row.used_qty)
		if row.parent_sales_order:
			usage_map[(row.parent_sales_order, row.item_code)] = usage_map.get(
				(row.parent_sales_order, row.item_code), 0
			) + normalize_qty(row.used_qty)
		# Bağımsız usage kayıtları için (None, item_code) anahtarları da ekle
		if not row.sales_order:
			usage_map[(None, row.item_code)] = usage_map.get(
				(None, row.item_code), 0
			) + normalize_qty(row.used_qty)
	return usage_map


def get_stock_maps(item_codes):
	"""
	Verilen item_codes için toplam stok ve depo bazında stok miktarlarını döndürür.
	"""
	bin_rows = frappe.db.get_all(
		"Bin",
		filters={"item_code": ["in", item_codes]},
		fields=["item_code", "warehouse", "actual_qty"],
	)
	stock_map = {}
	stock_by_warehouse_map = {}
	for row in bin_rows:
		stock_map[row.item_code] = normalize_qty(row.actual_qty)
		stock_by_warehouse_map.setdefault(row.item_code, {})[row.warehouse] = (
			normalize_qty(row.actual_qty)
		)
	return stock_map, stock_by_warehouse_map


def get_item_names(item_codes):
	"""
	Verilen item_codes için ürün isimlerini döndürür.
	"""
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
	reserve_warehouse_stock_map = {}
	if reserve_warehouse:
		reserve_bin_rows = frappe.db.get_all(
			"Bin",
			filters={"item_code": ["in", item_codes], "warehouse": reserve_warehouse},
			fields=["item_code", "actual_qty"],
		)
		for row in reserve_bin_rows:
			reserve_warehouse_stock_map[row.item_code] = normalize_qty(row.actual_qty)
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
			all_item_codes.add(rm.item_code)
			item_bom_map.setdefault(rm.item_code, []).append((item, rm))
	all_item_codes = list(all_item_codes)

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
		row.item_code: normalize_qty(row.total_quantity) for row in total_rezerv_rows
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
		row.item_code: normalize_qty(row.total_used) for row in total_usage_rows
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
		row.item_code: normalize_qty(row.total_long_term) for row in total_long_term_rows
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
				"long_term_reserve_qty": float(long_term_reserve_qty),
				"used_from_long_term_reserve": float(used_from_long_term_reserve),
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
		toplam_stok = float(data["stock"] or 0)
		toplam_rezerv = float(
			data["total_reserved_qty"] or 0
		)  # sistemdeki tüm rezervlerin toplamı
		if is_long_term_child and parent_sales_order:
			acik_miktar = float(data["qty"] or 0)
			kullanilabilir_stok = 0
		else:
			kullanilabilir_stok = toplam_stok - toplam_rezerv
			acik_miktar = max(float(data["qty"] or 0) - kullanilabilir_stok, 0)
		mr_items = frappe.db.sql(
			"SELECT mri.parent, mri.qty, mr.transaction_date FROM `tabMaterial Request Item` mri INNER JOIN `tabMaterial Request` mr ON mri.parent = mr.name WHERE mri.item_code = %s AND mri.docstatus = 1 AND mr.material_request_type = 'Purchase'",
			(data["raw_material"],),
			as_dict=True,
		)
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
			"SELECT poi.parent, poi.qty, poi.schedule_date FROM `tabPurchase Order Item` poi INNER JOIN `tabPurchase Order` po ON poi.parent = po.name WHERE poi.item_code = %s AND poi.docstatus = 1 AND po.docstatus = 1 AND (poi.qty > IFNULL(poi.received_qty, 0))",
			(data["raw_material"],),
			as_dict=True,
		)
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
	return sorted(result, key=lambda x: float(x.get("acik_miktar", 0)), reverse=True)


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
	return normalize_qty(qty)


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
	Rezerved Raw Materials kaydını verilen miktar kadar azaltır, sıfırlanırsa siler.
	"""
	consume_qty = normalize_qty(consume_qty)
	rm_doc = frappe.get_doc("Rezerved Raw Materials", row_name)
	rm_doc.quantity = normalize_qty(rm_doc.quantity - consume_qty)
	if normalize_qty(rm_doc.quantity) <= 0:
		rm_doc.delete(ignore_permissions=True)
	else:
		rm_doc.save(ignore_permissions=True)


def update_or_delete_long_term_reserve_usage(usage_name, consume_qty):
	"""
	Long Term Reserve Usage kaydını verilen miktar kadar azaltır, sıfırlanırsa siler.
	"""
	consume_qty = normalize_qty(consume_qty)
	usage_doc = frappe.get_doc("Long Term Reserve Usage", usage_name)
	usage_doc.used_qty = normalize_qty(usage_doc.used_qty - consume_qty)
	if normalize_qty(usage_doc.used_qty) <= 0:
		usage_doc.delete(ignore_permissions=True)
	else:
		usage_doc.save(ignore_permissions=True)


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
	qty = normalize_qty(qty)
	existing = frappe.db.exists(
		"Rezerved Raw Materials", {"sales_order": sales_order, "item_code": item_code}
	)
	if existing:
		rm_doc = frappe.get_doc("Rezerved Raw Materials", existing)
		rm_doc.quantity = qty
		rm_doc.item_name = item_name
		rm_doc.customer = customer
		rm_doc.end_customer = end_customer
		rm_doc.save(ignore_permissions=True)
	else:
		rm_doc = frappe.new_doc("Rezerved Raw Materials")
		rm_doc.sales_order = sales_order
		rm_doc.item_code = item_code
		rm_doc.quantity = qty
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
			print(
				f"[DEBUG] Child sipariş iptalinde rezerve hammaddeler silinmeyecek: {getattr(doc, 'name', None)}"
			)
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
		acik_miktar = float(row.get("acik_miktar", 0) or 0)
		item_code = row.get("raw_material")
		if is_long_term_child and parent_sales_order:
			parent_so = parent_sales_order
			parent_rezerv = normalize_qty(
				frappe.db.get_value(
					"Rezerved Raw Materials",
					{"sales_order": parent_so, "item_code": item_code},
					"quantity",
				)
			)
			total_usage = normalize_qty(
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

			total_usage = normalize_qty(
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
					"acik_miktar": float(acik_miktar or 0),
					"uzun_vadeli_rezerv": float(parent_rezerv or 0),
					"kullanilan_rezerv": float(total_usage or 0),
					"kullanilabilir_uzun_vadeli": float(kalan_kullanilabilir or 0),
					"onerilen_kullanim": float(onerilen_kullanim or 0),
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
					reserve_doc.quantity = normalize_qty(
						reserve_doc.quantity + float(row["used_qty"])
					)
					reserve_doc.save(ignore_permissions=True)
				else:
					upsert_reserved_raw_material(
						sales_order=parent_sales_order,
						item_code=row["item_code"],
						qty=normalize_qty(float(row["used_qty"])),
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
	qty = normalize_qty(qty)
	existing = frappe.get_all(
		"Long Term Reserve Usage",
		filters={"sales_order": sales_order, "item_code": item_code},
		fields=["name"],
	)
	if existing:
		usage_doc = frappe.get_doc("Long Term Reserve Usage", existing[0]["name"])
		usage_doc.used_qty = qty  # <-- Birikmeli değil, yeni miktarı yaz
		usage_doc.usage_date = frappe.utils.nowdate()
		if is_long_term_child and parent_sales_order:
			usage_doc.parent_sales_order = parent_sales_order
		usage_doc.save(ignore_permissions=True)
	else:
		usage_doc = frappe.new_doc("Long Term Reserve Usage")
		usage_doc.sales_order = sales_order
		usage_doc.item_code = item_code
		usage_doc.used_qty = qty
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
			qty = float(usage.get("qty", 0))
			if not item_code or qty <= 0:
				continue
			# Parent'ı belirle
			if is_long_term_child and parent_sales_order:
				parent_so = parent_sales_order
				parent_rezerv = normalize_qty(
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
				total_usage = normalize_qty(
					frappe.db.sql(
						"""
                    SELECT SUM(used_qty) FROM `tabLong Term Reserve Usage`
                    WHERE (sales_order = %s OR parent_sales_order = %s) AND item_code = %s
                """,
						(parent_so, parent_so, item_code),
					)[0][0]
				)
			else:
				total_usage = normalize_qty(
					frappe.db.sql(
						"""
                    SELECT SUM(used_qty) FROM `tabLong Term Reserve Usage`
                    WHERE item_code = %s
                """,
						(item_code,),
					)[0][0]
				)
			kalan_kullanilabilir = max(parent_rezerv - total_usage, 0)
			frappe.logger().info(
				f"[DEBUG] item_code={item_code}, qty={qty}, parent_rezerv={parent_rezerv}, total_usage={total_usage}, kalan_kullanilabilir={kalan_kullanilabilir}"
			)
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
					if normalize_qty(reserve_doc.quantity) <= 0:
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
	print(
		f"[DEBUG] handle_child_sales_order_reserves ÇAĞRILDI: {getattr(doc, 'name', None)} is_long_term_child={getattr(doc, 'is_long_term_child', None)} parent_sales_order={getattr(doc, 'parent_sales_order', None)}"
	)
	if not getattr(doc, "is_long_term_child", 0) or not getattr(
		doc, "parent_sales_order", None
	):
		print(
			f"[DEBUG] Child kontrolü geçilemedi: is_long_term_child={getattr(doc, 'is_long_term_child', None)}, parent_sales_order={getattr(doc, 'parent_sales_order', None)}"
		)
		return

	parent_so = doc.parent_sales_order
	# 1. Child'ın tüm item'ları için BOM'dan çıkan hammaddeleri ve miktarlarını topla
	toplam_ihtiyac = {}
	for item in doc.items:
		bom = frappe.db.get_value(
			"BOM", {"item": item.item_code, "is_active": 1, "is_default": 1}, "name"
		)
		if not bom:
			print(f"[DEBUG] Item'ın BOM'u yok: item_code={item.item_code}")
			continue
		bom_doc = frappe.get_doc("BOM", bom)
		for rm in bom_doc.items:
			hammadde_code = str(rm.item_code).strip()
			ihtiyac = normalize_qty(float(rm.qty) * float(item.qty))
			toplam_ihtiyac[hammadde_code] = toplam_ihtiyac.get(hammadde_code, 0) + ihtiyac
	# 2. Her hammadde için parent rezervde yeterli miktar var mı kontrol et
	for hammadde_code, ihtiyac_raw in toplam_ihtiyac.items():
		ihtiyac = normalize_qty(ihtiyac_raw)
		parent_reserve = frappe.get_all(
			"Rezerved Raw Materials",
			filters={"sales_order": parent_so, "item_code": hammadde_code},
			fields=["name", "quantity"],
		)
		if parent_reserve:
			mevcut_rezerv = normalize_qty(float(parent_reserve[0]["quantity"]))
			print("\n[DEBUG] Miktar karşılaştırması:")
			print(f"  Raw mevcut_rezerv: {float(parent_reserve[0]['quantity'])}")
			print(f"  Normalized mevcut_rezerv: {mevcut_rezerv}")
			print(f"  Raw ihtiyac: {ihtiyac_raw}")
			print(f"  Normalized ihtiyac: {ihtiyac}")
			print(f"  Difference: {abs(mevcut_rezerv - ihtiyac)}")
			print(f"  Tolerance check: {qty_greater_or_equal(mevcut_rezerv, ihtiyac)}")
			print(
				f"[DEBUG] Hammadde toplu kontrol: hammadde_code={hammadde_code}, parent_rezerv={mevcut_rezerv}, toplam_ihtiyac={ihtiyac}"
			)
			if safe_qty_compare(mevcut_rezerv, ihtiyac):
				# 3. Usage ve düşüm işlemini tek seferde yap
				reserve_doc = frappe.get_doc(
					"Rezerved Raw Materials", parent_reserve[0]["name"]
				)
				reserve_doc.quantity = normalize_qty(reserve_doc.quantity - ihtiyac)
				if normalize_qty(reserve_doc.quantity) <= 0:
					reserve_doc.delete(ignore_permissions=True)
				else:
					reserve_doc.save(ignore_permissions=True)
				print(
					f"[DEBUG] Parent rezerv güncellendi: {parent_reserve[0]['name']}, kalan={reserve_doc.quantity}"
				)
				print(
					f"[DEBUG] USAGE KAYDI OLUŞTURULUYOR: child_so={doc.name}, hammadde_code={hammadde_code}, qty={ihtiyac}, parent_so={parent_so}"
				)
				upsert_long_term_reserve_usage(
					sales_order=doc.name,
					item_code=hammadde_code,
					qty=ihtiyac,
					is_long_term_child=True,
					parent_sales_order=parent_so,
				)
			else:
				print(
					f"[DEBUG] Yetersiz rezerv: parent_so={parent_so}, hammadde_code={hammadde_code}, mevcut_rezerv={mevcut_rezerv}, toplam_ihtiyac={ihtiyac}"
				)
				frappe.throw(
					_(
						f"Ana siparişte {hammadde_code} için yeterli uzun vadeli rezerv yok! (Gereken: {ihtiyac}, Mevcut: {mevcut_rezerv}, Fark: {abs(mevcut_rezerv - ihtiyac):.4f})"
					)
				)
		else:
			print(
				f"[DEBUG] Yetersiz rezerv: parent_so={parent_so}, hammadde_code={hammadde_code}, mevcut_rezerv=YOK"
			)
			frappe.throw(
				_(f"Ana siparişte {hammadde_code} için yeterli uzun vadeli rezerv yok!")
			)
	frappe.db.commit()
	print(
		f"[DEBUG] handle_child_sales_order_reserves TAMAMLANDI: {getattr(doc, 'name', None)}"
	)
	frappe.msgprint(_("Satış siparişi için rezervler güncellendi."), indicator="green")


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
				shortage_items.append(
					{
						"item_code": row.get("raw_material"),
						"qty": acik_miktar,
						"schedule_date": frappe.utils.nowdate(),
					}
				)
		if not shortage_items:
			return {
				"success": False,
				"message": "Eksik hammadde yok, talep oluşturulmadı.",
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
				},
			)
		mr.insert(ignore_permissions=True)
		mr.submit()
		return {
			"success": True,
			"message": "Satınalma Talebi başarıyla oluşturuldu.",
			"mr_name": mr.name,
			"created_rows": shortage_items,
		}
	except Exception:
		frappe.log_error(
			"create_material_request_for_shortages HATA", frappe.get_traceback()
		)
		return {"success": False, "message": "Bir hata oluştu. Lütfen tekrar deneyin."}


@frappe.whitelist()
def test_quantity_comparison():
	"""
	Test function to verify quantity comparison logic works correctly.
	"""
	test_cases = [
		(33.41, 33.4, "Should be equal with tolerance"),
		(33.4, 33.41, "Should be equal with tolerance (reverse)"),
		(15.44, 15.44, "Should be exactly equal"),
		(15.0, 15.00, "Should be exactly equal (different precision)"),
		(10.05, 10.01, "Should be equal with tolerance"),
		(10.1, 10.05, "Should NOT be equal (outside tolerance)"),
	]

	results = []
	for qty1, qty2, description in test_cases:
		norm_qty1 = normalize_qty(qty1)
		norm_qty2 = normalize_qty(qty2)
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
