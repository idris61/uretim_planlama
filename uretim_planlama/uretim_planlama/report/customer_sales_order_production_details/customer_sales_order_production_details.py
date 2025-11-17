import frappe
from frappe import _  # Kod yorumları: Türkçe
from typing import List, Dict, Any, Optional, Set


def execute(filters: Optional[Dict[str, Any]] = None):
	"""
	Script Report entrypoint
	"""
	filters = filters or {}

	# Permission check
	if not frappe.has_permission("Sales Order", ptype="read"):
		frappe.throw(_("Not permitted to read Sales Order"))

	# Müşteri seçildi ama sipariş seçilmediyse veri getirmeyelim (UI rehberi)
	customer = (filters.get("customer") or "").strip()
	sales_order = (filters.get("sales_order") or "").strip()

	if not customer or not sales_order:
		return get_columns(show_wo_fields=False), []

	# Work Order var mı? (boş WO kolonlarını saklamak için)
	has_work_orders = frappe.get_all(
		"Work Order",
		filters={"sales_order": sales_order, "docstatus": ["in", [0, 1]]},
		limit=1,
	)

	columns = get_columns(show_wo_fields=bool(has_work_orders))

	# Input validation
	validate_inputs(customer, sales_order)

	# Dinamik ve doğru durum için sunucu tarafında her seferinde taze veri
	data = get_data(customer=customer, sales_order=sales_order)

	return columns, data


def validate_inputs(customer: str, sales_order: str) -> None:
	"""
	Geçerli müşteri ve satış siparişi kontrolü
	"""
	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("Customer not found"))
	if not frappe.db.exists("Sales Order", sales_order):
		frappe.throw(_("Sales Order not found"))

	so_customer = frappe.db.get_value("Sales Order", sales_order, "customer")
	if so_customer != customer:
		frappe.throw(_("Selected Sales Order does not belong to the selected Customer"))


def get_columns(show_wo_fields: bool = True) -> List[Dict[str, Any]]:
	"""
	Rapor sütunları (örnek SQL'e uygun)
	"""
	cols = [
		{"label": _("Customer"), "fieldname": "customer_html", "fieldtype": "HTML", "width": 120},
		{"label": _("End Customer"), "fieldname": "end_customer_html", "fieldtype": "HTML", "width": 140},
		{"label": _("Sales Order"), "fieldname": "sales_order_html", "fieldtype": "HTML", "width": 120},
		{"label": _("Sales Order Status"), "fieldname": "sales_order_status_html", "fieldtype": "HTML", "width": 140},
		{"label": _("Plan Status"), "fieldname": "planning_status", "fieldtype": "HTML", "width": 120},
		{"label": _("Serial No"), "fieldname": "serial_no", "fieldtype": "Data", "width": 110},
		{"label": _("Color"), "fieldname": "color", "fieldtype": "Data", "width": 110},
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 110},
		{"label": _("Planned Qty"), "fieldname": "planned_qty", "fieldtype": "Float", "width": 90},
		{"label": _("Produced Qty"), "fieldname": "produced_qty", "fieldtype": "Float", "width": 100},
	]
	if show_wo_fields:
		cols.extend([
			{"label": _("WO Status"), "fieldname": "wo_status_html", "fieldtype": "HTML", "width": 130},
			{"label": _("SO Delivery Date"), "fieldname": "so_delivery_date", "fieldtype": "Date", "width": 120},
			{"label": _("Planned Start"), "fieldname": "planned_start_date", "fieldtype": "Datetime", "width": 140},
			{"label": _("Planned End"), "fieldname": "planned_end_date", "fieldtype": "Datetime", "width": 140},
			{"label": _("Actual Start"), "fieldname": "actual_start_date", "fieldtype": "Datetime", "width": 140},
			{"label": _("Actual End"), "fieldname": "actual_end_date", "fieldtype": "Datetime", "width": 140},
		])
	cols = cols + [
		{"label": _("Completed Operations"), "fieldname": "completed_operations_html", "fieldtype": "HTML", "width": 320},
		{"label": _("Pending Operations"), "fieldname": "pending_operations_html", "fieldtype": "HTML", "width": 320},
	]
	return cols


def get_data(customer: str, sales_order: str) -> List[Dict[str, Any]]:
	"""
	Veri kaynağı
	- Frappe ORM kullan
	- Doğru ve dinamik durumlar için Work Order ve Job Card ile Stock Entry üzerinden canlı hesaplama
	"""
	def get_first_existing_value(doctype: str, name: str, columns: List[str]) -> Optional[str]:
		# Yalnızca tabloda VAR olan ilk kolonu güvenli şekilde döner
		for col in columns:
			try:
				if frappe.db.has_column(doctype, col):
					val = frappe.db.get_value(doctype, name, col)
					if val:
						return val
			except Exception:
				continue
		return None

	def translate_sales_order_status(status: str) -> str:
		# Satış siparişi durumlarını Türkçe + inline-style HTML
		status = (status or "").strip()
		mapper = {
			"Draft": ("Taslak", "saddlebrown"),
			"To Deliver and Bill": ("Teslim ve Faturalandırılacak", "orange"),
			"To Deliver": ("Teslim Edilecek", "orange"),
			"To Bill": ("Faturalandırılacak", "orange"),
			"Completed": ("Tamamlandı", "seagreen"),
			"Closed": ("Kapalı", "blue"),
			"Cancelled": ("İptal Edildi", "crimson"),
			# Türkçe değerler de aynen geçsin
			"Taslak": ("Taslak", "saddlebrown"),
			"Teslim ve Faturalandırılacak": ("Teslim ve Faturalandırılacak", "orange"),
			"Teslim Edilecek": ("Teslim Edilecek", "orange"),
			"Faturalandırılacak": ("Faturalandırılacak", "orange"),
			"Tamamlandı": ("Tamamlandı", "seagreen"),
			"Kapalı": ("Kapalı", "blue"),
			"İptal": ("İptal Edildi", "crimson"),
			"Onaylandı": ("Onaylandı", "seagreen"),
		}
		label, color = mapper.get(status, (status or "-", "gray"))
		return f'<span style="color:{color};font-weight:bold;">{frappe.safe_decode(label)}</span>'

	def translate_work_order_status(status: str) -> str:
		# İş emri durumlarını Türkçe + inline-style HTML
		status = (status or "").strip()
		mapper = {
			"Draft": ("Taslak", "saddlebrown"),
			"Not Started": ("Başlamadı", "deeppink"),
			"In Process": ("Devam Ediyor", "orange"),
			"In Progress": ("Devam Ediyor", "orange"),
			"Stopped": ("Durduruldu", "red"),
			"Completed": ("Tamamlandı", "green"),
			"Cancelled": ("İptal", "red"),
			# Türkçe değerler
			"Başlamadı": ("Başlamadı", "deeppink"),
			"Devam Ediyor": ("Devam Ediyor", "orange"),
			"Durduruldu": ("Durduruldu", "red"),
			"Tamamlandı": ("Tamamlandı", "green"),
			"İptal": ("İptal", "red"),
			"Taslak": ("Taslak", "saddlebrown"),
		}
		label, color = mapper.get(status, (status or "-", "gray"))
		return f'<span style="color:{color};font-weight:bold;">{frappe.safe_decode(label)}</span>'

	def planning_status_html(is_planned: bool) -> str:
		# Plan durumu rozet
		if is_planned:
			return '<span style="background:#d4edda;color:#155724;padding:2px 6px;margin:2px;border-radius:4px;display:inline-block;">Planlandı</span>'
		return '<span style="background:#fff3cd;color:#856404;padding:2px 6px;margin:2px;border-radius:4px;display:inline-block;">Planlanmadı</span>'
	# İlgili Sales Order Item kayıtlarını çek (fallback için)
	so_items = frappe.get_all(
		"Sales Order Item",
		filters={"parent": sales_order},
		fields=["name"],
	)
	so_item_names = [it.name for it in so_items] if so_items else []

	# İlgili Work Order'ları iki kanaldan getir (sales_order ve sales_order_item)
	wo_fields = [
		"name",
		"production_item",
		"qty",
		"produced_qty",
		"status",
		"sales_order_item",
	]

	wo_by_so = frappe.get_all(
		"Work Order",
		filters={"sales_order": sales_order, "docstatus": ["in", [0, 1]]},
		fields=wo_fields,
		order_by="creation asc",
	)

	wo_by_so_item = []
	if so_item_names:
		wo_by_so_item = frappe.get_all(
			"Work Order",
			filters={"sales_order_item": ["in", so_item_names], "docstatus": ["in", [0, 1]]},
			fields=wo_fields,
			order_by="creation asc",
		)

	# Birleştir ve benzersizleştir
	work_orders_map: Dict[str, Any] = {}
	for wo in wo_by_so + wo_by_so_item:
		work_orders_map[wo.name] = wo
	work_orders = list(work_orders_map.values())

	if not work_orders:
		# Plan yapılmamış; SO Item'ları göster
		so_items = frappe.get_all(
			"Sales Order Item",
			filters={"parent": sales_order},
			fields=["name", "item_code", "item_name", "qty"],
			order_by="idx asc",
		)
		# Üst bilgiler
		so_doc = frappe.get_doc("Sales Order", sales_order)
		customer = so_doc.customer
		end_customer = so_doc.get("custom_end_customer")
		sales_order_status = so_doc.get("status")
		# İlk satır HTML'leri
		customer_html = f'<span style="color:black;font-weight:bold;">{frappe.safe_decode(customer)}</span>'
		end_customer_html = f'<span style="color:gray;">{frappe.safe_decode(end_customer or "")}</span>' if end_customer else ""
		sales_order_html = f'<span style="color:black;font-weight:bold;">{frappe.safe_decode(sales_order)}</span>'
		# Item custom alanlarını topla
		item_codes = [x.item_code for x in so_items if x.item_code]
		item_map = {}
		if item_codes:
			items = frappe.get_all(
				"Item",
				filters={"name": ["in", item_codes]},
				fields=["name", "custom_serial", "custom_color"],
			)
			item_map = {x.name: x for x in items}

		rows = []
		for idx, si in enumerate(so_items):
			item_info = item_map.get(si.item_code or "", {})
			serial_no = item_info.get("custom_serial") or ""
			color = item_info.get("custom_color") or ""
			rows.append({
				"customer_html": customer_html if idx == 0 else "",
				"end_customer_html": end_customer_html if idx == 0 else "",
				"sales_order_html": sales_order_html if idx == 0 else "",
				"sales_order_status_html": translate_sales_order_status(sales_order_status),
				"planning_status": planning_status_html(False),
				"serial_no": serial_no,
				"color": color,
				"item_code": si.item_code,
				"planned_qty": float(si.qty or 0),
				"produced_qty": 0.0,
				"wo_status_html": "",
				"so_delivery_date": None,
				"planned_start_date": None,
				"planned_end_date": None,
				"actual_start_date": None,
				"actual_end_date": None,
				"completed_operations_html": "",
				"pending_operations_html": "",
			})
		return rows

	wo_names = [wo.name for wo in work_orders]
	item_codes = list({wo.production_item for wo in work_orders if wo.production_item})

	# Item isimlerini toplu çek
	item_name_by_code: Dict[str, str] = {}
	if item_codes:
		items = frappe.get_all(
			"Item",
			filters={"name": ["in", item_codes]},
			fields=["name", "item_name"],
		)
		item_name_by_code = {it.name: it.item_name for it in items}

	# Operasyon ilerleme ve son işlem için Job Card'lardan özet çıkar
	job_cards = []
	if wo_names:
		job_cards = frappe.get_all(
			"Job Card",
			filters={"work_order": ["in", wo_names], "docstatus": 1},
			fields=[
				"work_order",
				"operation",
				"modified",
			],
			order_by="modified desc",
		)

	# Stock Entry (Manufacture) sayısı
	stock_entries = []
	if wo_names:
		stock_entries = frappe.get_all(
			"Stock Entry",
			filters={
				"work_order": ["in", wo_names],
				"docstatus": 1,
				"stock_entry_type": "Manufacture",
			},
			fields=["name", "work_order"],
		)

	# Job Card ve Stock Entry verilerini WO bazında grupla
	wo_to_job_cards: Dict[str, List[Dict[str, Any]]] = {}
	for jc in job_cards:
		wo_to_job_cards.setdefault(jc.work_order, []).append(jc)

	wo_to_se_count: Dict[str, int] = {}
	for se in stock_entries:
		wo_to_se_count[se.work_order] = wo_to_se_count.get(se.work_order, 0) + 1

	data: List[Dict[str, Any]] = []

	# Sales Order üst bilgileri toplu
	so_names = list({frappe.get_value("Work Order", w.name, "sales_order") for w in work_orders if frappe.get_value("Work Order", w.name, "sales_order")})
	so_map: Dict[str, Dict[str, Any]] = {}
	if so_names:
		sos = frappe.get_all(
			"Sales Order",
			filters={"name": ["in", so_names]},
			fields=["name", "customer", "custom_end_customer", "status", "docstatus", "transaction_date"],
		)
		so_map = {x.name: x for x in sos}

	# Item bilgileri: custom_serial ve custom_color
	item_codes = list({wo.production_item for wo in work_orders if wo.production_item})
	item_map: Dict[str, Dict[str, Any]] = {}
	if item_codes:
		items = frappe.get_all(
			"Item",
			filters={"name": ["in", item_codes]},
			fields=["name", "custom_serial", "custom_color"],
		)
		item_map = {x.name: x for x in items}

	# Tekrarlanan alanları boş göstermek için son değerleri tut
	last_customer = None
	last_end_customer = None
	last_sales_order = None

	for wo in sorted(work_orders, key=lambda r: r.get("planned_start_date") or "", reverse=True):
		so_name = frappe.get_value("Work Order", wo.name, "sales_order")
		so_info = so_map.get(so_name or "", {})
		customer = so_info.get("customer") if so_info else None
		end_customer = so_info.get("custom_end_customer") if so_info else None
		sales_order_status = so_info.get("status") if so_info else None
		planned_qty = float(wo.qty or 0)
		produced_qty = float(wo.produced_qty or 0)
		pending_qty = max(planned_qty - produced_qty, 0.0)

		# Operasyon ilerleme yüzdesi: Job Card'lardaki tamamlanan/planlanan üzerinden basit oran
		operations_progress = 0.0
		last_job_card_date = None
		last_operation = None
		jc_list = wo_to_job_cards.get(wo.name, [])
		if jc_list:
			for jc in jc_list:
				if not last_job_card_date or jc.modified > last_job_card_date:
					last_job_card_date = jc.modified
					last_operation = jc.operation

		# İlerleme yüzdesi: produced_qty / planned_qty
		if planned_qty > 0:
			ratio = produced_qty / planned_qty
			operations_progress = round(min(max(ratio, 0), 1) * 100.0, 1)
		else:
			operations_progress = 0.0

		# Work Order detay tarihleri ve operasyon durumları
		wo_doc = frappe.get_doc("Work Order", wo.name)
		planned_start_date = wo_doc.get("planned_start_date")
		planned_end_date = wo_doc.get("planned_end_date")
		actual_start_date = wo_doc.get("actual_start_date")
		actual_end_date = wo_doc.get("actual_end_date")

		# Operasyon listeleri (Work Order Operation child)
		completed_ops: List[str] = []
		pending_ops: List[str] = []
		try:
			for op in wo_doc.get("operations") or []:
				op_name = op.operation
				op_status = (op.status or "").lower()
				if op_status == "completed":
					completed_ops.append(op_name)
				else:
					pending_ops.append(op_name)
		except Exception:
					# child tablo yoksa sessiz geç
					pass

		# Sales Order Item teslim tarihi
		so_delivery_date = None
		soi_serial = None
		soi_color = None
		if wo.get("sales_order_item"):
			try:
				soi_name = wo.get("sales_order_item")
				soi = frappe.get_doc("Sales Order Item", soi_name)
				so_delivery_date = soi.get("delivery_date")
				# Seri ve renk için çoklu aday alan isimleri
				def _pick(doc: Any, candidates: List[str]) -> Optional[str]:
					for fn in candidates:
						val = doc.get(fn)
						if val:
							return val
					return None
				soi_serial = _pick(soi, [
					"custom_order_serial",
					"serial_no",
					"custom_serial_no",
					"order_serial",
					"custom_serial",
				])
				soi_color = _pick(soi, [
					"custom_order_color",
					"color",
					"custom_color",
					"order_color",
				])
			except Exception:
				so_delivery_date = None
				soi_serial = None
				soi_color = None

		# Ek fallback: Work Order üzerindeki muhtemel custom alanlar
		if not soi_serial:
			soi_serial = get_first_existing_value("Work Order", wo.name, ["custom_order_serial", "custom_serial_no"])
		if not soi_color:
			soi_color = get_first_existing_value("Work Order", wo.name, ["custom_order_color", "custom_color"])

		# Ek fallback: Sales Order üzerindeki muhtemel custom alanlar
		if not soi_serial:
			soi_serial = get_first_existing_value("Sales Order", sales_order, ["custom_order_serial", "custom_serial_no"])
		if not soi_color:
			soi_color = get_first_existing_value("Sales Order", sales_order, ["custom_order_color", "custom_color"])

		# Renk hâlâ boşsa, stok kartı varyantından “Renk/Color” attribute'unu dene
		if not soi_color and wo.production_item:
			try:
				attr = frappe.get_all(
					"Item Variant Attribute",
					filters={
						"parent": wo.production_item,
						"attribute": ["in", ["Renk", "Color"]],
					},
					fields=["attribute_value"],
					limit=1,
				)
				if attr:
					soi_color = attr[0].get("attribute_value")
			except Exception:
				pass

		# Item custom alanları ve seri/renk nihai değerleri
		item_info = item_map.get(wo.production_item or "", {})
		serial_no = item_info.get("custom_serial") or soi_serial or ""
		color = item_info.get("custom_color") or soi_color or ""

		# Tekrarlanan alanları ilk satırda göster
		customer_html = ""
		end_customer_html = ""
		sales_order_html = ""
		if customer and customer != last_customer:
			customer_html = f'<span style="color:black;font-weight:bold;">{frappe.safe_decode(customer)}</span>'
			last_customer = customer
		if end_customer and end_customer != last_end_customer:
			end_customer_html = f'<span style="color:gray;">{frappe.safe_decode(end_customer)}</span>'
			last_end_customer = end_customer
		if so_name and so_name != last_sales_order:
			sales_order_html = f'<span style="color:black;font-weight:bold;">{frappe.safe_decode(so_name)}</span>'
			last_sales_order = so_name

		# Operasyon rozet HTML (tamamlanan yeşil, bekleyen kırmızı)
		def tag_list_html(items: List[str], bg: str, fg: str) -> str:
			if not items:
				return ""
			return " ".join(
				[f'<span style="background:{bg};color:{fg};padding:2px 6px;margin:2px;border-radius:4px;display:inline-block;">{frappe.safe_decode(op)}</span>' for op in items]
			)
		completed_ops_display = tag_list_html(completed_ops, "#d4edda", "#155724")
		pending_ops_display = tag_list_html(pending_ops, "#f8d7da", "#721c24")

		data.append(
			{
				"customer_html": customer_html,
				"end_customer_html": end_customer_html,
				"sales_order_html": sales_order_html,
				"sales_order_status_html": translate_sales_order_status(sales_order_status),
				"planning_status": planning_status_html(True),
				"serial_no": serial_no or "",
				"color": soi_color or color,
				"item_code": wo.production_item,
				"planned_qty": planned_qty,
				"produced_qty": produced_qty,
				"wo_status_html": translate_work_order_status(wo.status),
				"so_delivery_date": so_delivery_date,
				"planned_start_date": planned_start_date,
				"planned_end_date": planned_end_date,
				"actual_start_date": actual_start_date,
				"actual_end_date": actual_end_date,
				"completed_operations_html": completed_ops_display,
				"pending_operations_html": pending_ops_display,
			}
		)

	# Nihai müşteri ve müşteri tekrarlarını HTML ile çözdük (ilk satır dolu, diğerleri boş)

	return data


