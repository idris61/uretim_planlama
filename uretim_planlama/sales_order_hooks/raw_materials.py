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
			"SELECT mri.parent, mri.qty FROM `tabMaterial Request Item` mri INNER JOIN `tabMaterial Request` mr ON mri.parent = mr.name WHERE mri.item_code = %s AND mri.docstatus = 1 AND mr.material_request_type = 'Purchase'",
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
			"used_from_long_term_reserve": data["used_from_long_term_reserve"]
		})
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

		# 1. Önce ilgili satış siparişi ve hammadde için rezerv kayıtlarını sırayla tüket
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

		# 2. Uzun vadeli rezerv kullanımı varsa, aynı şekilde tüket
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

@frappe.whitelist()
def create_material_request_for_shortages(sales_order, submit=0):
	"""
	Satış siparişi içindeki shortage > 0 hammaddeler için Material Request (Purchase) oluşturur.
	submit=1 ise belgeyi direkt onaylar.
	Ayrıca, uzun vadeli rezervten kullanılan miktar varsa, yenileme satırı ekler.
	"""
	raw_materials = get_sales_order_raw_materials(sales_order)
	shortage_items = [row for row in raw_materials if float(row.get("acik_miktar", 0)) > 0]
	if not shortage_items:
		return {"success": False, "message": "Açık miktarı olan hammadde yok."}

	shortage_items_to_request = []
	long_term_renewal_rows = []
	
	for item in shortage_items:
		# Normal eksik miktar için talep kontrolü
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
		
		# Uzun vadeli rezervden kullanılan miktarı bul
		used_from_long_term = frappe.db.get_value(
			"Long Term Reserve Usage",
			{"sales_order": sales_order, "item_code": item["raw_material"]},
			"used_qty"
		) or 0
		
		if float(used_from_long_term) > 0:
			# Uzun vadeli rezerv yenileme için talep kontrolü
			existing_renewal = frappe.db.exists(
				"Material Request Item",
				{
					"item_code": item["raw_material"],
					"sales_order": sales_order,
					"description": ["like", "%Uzun vadeli rezervten kullanılan%"],
					"docstatus": ["<", 2]
				}
			)
			
			if not existing_renewal:
				long_term_renewal_rows.append({
					"item_code": item["raw_material"],
					"item_name": item["item_name"],
					"qty": used_from_long_term,
					"warehouse": None,
					"sales_order": sales_order,
					"schedule_date": frappe.utils.add_days(frappe.utils.nowdate(), 3),
					"description": f"Uzun vadeli rezervten kullanılan {used_from_long_term} adet {item['item_name']} yerine yenileme."
				})

	if not shortage_items_to_request and not long_term_renewal_rows:
		return {"success": False, "message": "Tüm eksikler ve rezerv yenilemeleri için zaten talep oluşturulmuş."}

	mr = frappe.new_doc("Material Request")
	mr.material_request_type = "Purchase"
	mr.schedule_date = frappe.utils.add_days(frappe.utils.nowdate(), 3)
	mr.set("sales_order", sales_order)
	created_rows = []
	
	# Normal eksik miktarlar için satırlar
	for item in shortage_items_to_request:
		mr.append("items", {
			"item_code": item["raw_material"],
			"item_name": item["item_name"],
			"qty": item["acik_miktar"],
			"warehouse": None,
			"sales_order": sales_order,
			"schedule_date": mr.schedule_date
		})
		created_rows.append({
			"item_code": item["raw_material"],
			"qty": item["acik_miktar"],
			"type": "shortage"
		})
	
	# Uzun vadeli rezerv yenileme satırlarını ekle
	for row in long_term_renewal_rows:
		mr.append("items", row)
		created_rows.append({
			"item_code": row["item_code"],
			"qty": row["qty"],
			"description": row["description"],
			"type": "renewal"
		})
	
	mr.save(ignore_permissions=True)
	if int(submit):
		mr.submit()
	
	return {
		"success": True,
		"mr_name": mr.name,
		"created_rows": created_rows,
		"message": f"Material Request oluşturuldu: {len(shortage_items_to_request)} eksik miktar, {len(long_term_renewal_rows)} rezerv yenileme satırı"
	}

# Satış Siparişi submit edilirken stok kontrolü

def check_raw_material_stock_on_submit(doc, method=None):
	# Sales Order henüz kaydedilmediği için doc objesini kullan
	# BOM'ları manuel olarak hesapla
	uyarilar = []
	
	for item in doc.items:
		# BOM bul, raw materials ve stok miktarlarını çek
		bom = frappe.db.get_value("BOM", {"item": item.item_code, "is_active": 1, "is_default": 1}, "name")
		if bom:
			bom_doc = frappe.get_doc("BOM", bom)
			for rm in bom_doc.items:
				# Stok kontrolü
				bin_row = frappe.db.get_value("Bin", {"item_code": rm.item_code, "warehouse": item.warehouse}, ["actual_qty"], as_dict=True) or {"actual_qty": 0}
				stok = float(bin_row["actual_qty"] or 0)
				
				# Rezerve miktarı
				reserved_qty = frappe.db.sql(
					"""
					SELECT SUM(quantity) FROM `tabRezerved Raw Materials` WHERE item_code = %s
					""", (rm.item_code,), as_list=True
				)
				reserved_qty = reserved_qty[0][0] if reserved_qty and reserved_qty[0][0] else 0
				
				# Toplam ihtiyaç
				toplam_ihtiyac = rm.qty * item.qty
				
				if (toplam_ihtiyac + reserved_qty) > stok:
					uyarilar.append(f"{rm.item_code} için toplam ihtiyaç ({toplam_ihtiyac}) + rezerve ({reserved_qty}) > stok ({stok})!")
	
	if uyarilar:
		frappe.msgprint(_("Stok Yetersiz!\n\n" + "\n".join(uyarilar)))
		frappe.msgprint(
			_("<span style='color:#fff;background:#d32f2f;padding:8px 16px;border-radius:8px;display:inline-block;font-weight:bold;'>Dikkat! Toplam Stok Miktarına göre, Uzun Vadeli Sipariş Rezervlerini kullansanız dahi bu siparişe yetecek kadar hammaddeniz fiziken yok!</span>"),
			indicator="red"
		)

@frappe.whitelist()
def use_long_term_reserve(sales_order, item_code, qty, description=None):
	# Uzun vadeli rezervten miktar aktar ve logla
	doc = frappe.get_doc({
		"doctype": "Long Term Reserve Usage",
		"sales_order": sales_order,
		"item_code": item_code,
		"used_qty": qty,
		"usage_date": frappe.utils.nowdate(),
		"description": description or _(f"Uzun vadeli rezervten aktarıldı.")
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc.name

@frappe.whitelist()
def restore_long_term_reserve(sales_order, item_code, qty):
	"""
	Satınalma talebi karşılandığında uzun vadeli rezerve geri ekler.
	Kullanım kaydını günceller veya siler.
	"""
	usage = frappe.get_all("Long Term Reserve Usage", filters={"sales_order": sales_order, "item_code": item_code}, order_by="creation desc")
	if not usage:
		return
	usage_doc = frappe.get_doc("Long Term Reserve Usage", usage[0].name)
	if usage_doc.used_qty > qty:
		usage_doc.used_qty -= qty
		usage_doc.save(ignore_permissions=True)
	else:
		usage_doc.delete(ignore_permissions=True)
	frappe.db.commit()
	return True

def restore_long_term_reserve_on_purchase_receipt(doc, method=None):
	"""
	Satınalma fişi girildiğinde, açıklamada 'Uzun vadeli rezervten kullanılan' geçen satırlar için ilgili miktarı uzun vadeli rezerve geri ekler.
	"""
	for item in doc.items:
		if item.description and "Uzun vadeli rezervten kullanılan" in item.description:
			used_qty = item.qty
			item_code = item.item_code
			sales_order = getattr(item, 'sales_order', None)
			if sales_order and item_code and used_qty:
				restore_long_term_reserve(sales_order, item_code, used_qty)

@frappe.whitelist()
def check_long_term_reserve_availability(sales_order):
	"""
	Uzun vadeli rezervden kullanılabilir miktarları kontrol eder ve öneriler sunar
	Sadece ilgili satış siparişinin kendi ihtiyaç miktarı kadar öneri sunar.
	"""
	raw_materials = get_sales_order_raw_materials(sales_order)
	recommendations = []
	for item in raw_materials:
		acik_miktar = float(item.get("acik_miktar", 0))
		if acik_miktar < 0:
			acik_miktar = 0
		uzun_vadeli_rezerv = float(item.get("long_term_reserve_qty", 0))
		kullanilan_rezerv = float(item.get("used_from_long_term_reserve", 0))
		ihtiyac_miktari = float(item.get("qty", 0))
		if acik_miktar > 0 and uzun_vadeli_rezerv > kullanilan_rezerv:
			kullanilabilir_uzun_vadeli = uzun_vadeli_rezerv - kullanilan_rezerv
			onerilen_kullanim = min(ihtiyac_miktari, kullanilabilir_uzun_vadeli)
			recommendations.append({
				"item_code": item["raw_material"],
				"item_name": item["item_name"],
				"acik_miktar": acik_miktar,
				"uzun_vadeli_rezerv": uzun_vadeli_rezerv,
				"kullanilan_rezerv": kullanilan_rezerv,
				"kullanilabilir_uzun_vadeli": kullanilabilir_uzun_vadeli,
				"onerilen_kullanim": onerilen_kullanim
			})
	return recommendations

@frappe.whitelist()
def use_long_term_reserve_bulk(sales_order, usage_data):
	"""
	Toplu uzun vadeli rezerv kullanımı
	usage_data: [{"item_code": "ITEM-001", "qty": 10}, ...]
	Aynı satış siparişi ve hammadde için tekrar kullanım engellenir.
	Submit edilmiş siparişlerde kullanım engellenir.
	"""
	try:
		# Sipariş submit edilmiş mi kontrol et
		so_doc = frappe.get_doc("Sales Order", sales_order)
		if so_doc.docstatus == 1:
			return {
				"success": False,
				"message": "Onaylanmış (submit edilmiş) satış siparişlerinde uzun vadeli rezerv kullanılamaz."
			}
		usage_data = frappe.parse_json(usage_data)
		created_records = []
		errors = []
		for usage in usage_data:
			item_code = usage.get("item_code")
			qty = float(usage.get("qty", 0))
			if qty > 0:
				# Daha önce aktif kullanım var mı kontrol et
				existing_usage = frappe.db.get_value(
					"Long Term Reserve Usage",
					{"sales_order": sales_order, "item_code": item_code},
					["name", "used_qty"],
				)
				if existing_usage and float(existing_usage[1] or 0) > 0:
					errors.append(f"{item_code} için zaten uzun vadeli rezerv kullanılmış. Tekrar kullanılamaz.")
					continue
				# Item name'i al
				item_name = frappe.db.get_value("Item", item_code, "item_name") or ""
				# Yeni kayıt oluştur
				usage_doc = frappe.get_doc({
					"doctype": "Long Term Reserve Usage",
					"sales_order": sales_order,
					"item_code": item_code,
					"item_name": item_name,
					"used_qty": qty,
					"usage_date": frappe.utils.nowdate(),
					"description": f"Uzun vadeli rezervten {qty} adet kullanıldı."
				})
				usage_doc.insert(ignore_permissions=True)
				created_records.append({
					"item_code": item_code,
					"qty": qty,
					"record_name": usage_doc.name
				})
		frappe.db.commit()
		if errors and not created_records:
			return {
				"success": False,
				"message": "\n".join(errors)
			}
		elif errors:
			return {
				"success": True,
				"message": f"Bazı hammaddeler için işlem yapılamadı:\n" + "\n".join(errors) + f"\nDiğerleri için kayıt oluşturuldu.",
				"records": created_records
			}
		else:
			return {
				"success": True,
				"message": f"{len(created_records)} hammadde için uzun vadeli rezerv kullanımı kaydedildi.",
				"records": created_records
			}
	except Exception as e:
		frappe.log_error(f"Uzun vadeli rezerv kullanımı hatası: {str(e)}")
		return {
			"success": False,
			"message": f"Hata oluştu: {str(e)}"
		}

# --- Sales Order iptalinde uzun vadeli rezerv kayıtlarını sil ---
def delete_long_term_reserve_usage_on_cancel(doc, method=None):
	try:
		records = frappe.get_all(
			"Long Term Reserve Usage",
			filters={"sales_order": doc.name},
			fields=["name"]
		)
		for row in records:
			frappe.delete_doc("Long Term Reserve Usage", row["name"], ignore_permissions=True)
		frappe.db.commit()
		frappe.msgprint(_(f"{doc.name} için uzun vadeli rezerv kayıtları silindi."), alert=True, indicator="orange")
	except Exception:
		frappe.log_error("Sales Order cancel - Long Term Reserve Usage silme HATA", frappe.get_traceback())

def release_reservations_on_job_card_complete(doc, method):
	frappe.log_error("[URETIM PLANLAMA TEST] Job Card fonksiyonu BAŞLANGIÇ", f"Job Card: {getattr(doc, 'name', None)}")
	msg_list = []
	print("[URETIM PLANLAMA] İş kartı submit edildi, rezerv güncelleme başlıyor...")
	frappe.log_error("[URETIM PLANLAMA] İş kartı submit edildi", f"Job Card: {doc.name}")
	msg_list.append(f"İş kartı submit edildi: {doc.name}")
	work_order = getattr(doc, "work_order", None)
	if not work_order:
		msg = "[URETIM PLANLAMA] HATA: İş kartında work_order yok!"
		print(msg)
		frappe.log_error("Job Card Reservation Update", "No work_order found on Job Card")
		frappe.msgprint(msg, indicator="red")
		return

	wo_doc = frappe.get_doc("Work Order", work_order)
	sales_order = getattr(wo_doc, "sales_order", None)
	if not sales_order:
		msg = f"[URETIM PLANLAMA] HATA: Work Order {work_order} içinde sales_order yok!"
		print(msg)
		frappe.log_error("Job Card Reservation Update", f"No sales_order found on Work Order {work_order}")
		frappe.msgprint(msg, indicator="red")
		return

	msg_list.append(f"İş kartı: {doc.name}, Work Order: {work_order}, Sales Order: {sales_order}")
	print(msg_list[-1])
	# Öncelik: Stock Entry üzerinden rezerv güncelle (hem job_card hem work_order ile arama)
	stock_entries = frappe.get_all(
		"Stock Entry",
		filters={
			"docstatus": 1,
			"purpose": ["in", ["Material Transfer for Manufacture", "Manufacture"]],
			"work_order": work_order
		},
		fields=["name"]
	)
	stock_entry_found = False
	for se in stock_entries:
		se_doc = frappe.get_doc("Stock Entry", se.name)
		for item in se_doc.items:
			item_code = item.item_code
			used_qty = abs(item.qty)
			msg = f"[URETIM PLANLAMA] StockEntry: {se.name}, Item: {item_code}, Kullanılan Miktar: {used_qty}"
			print(msg)
			msg_list.append(msg)
			# Rezerv kaydını güncelle
			reserved = frappe.get_all(
				"Rezerved Raw Materials",
				filters={"sales_order": sales_order, "item_code": item_code},
				fields=["name", "quantity"]
			)
			for row in reserved:
				rm_doc = frappe.get_doc("Rezerved Raw Materials", row.name)
				new_qty = max(0, (rm_doc.quantity or 0) - used_qty)
				if new_qty == 0:
					msg = f"[URETIM PLANLAMA] Rezerv SIFIRLANDI ve SİLİNDİ: {row.name} ({item_code})"
					print(msg)
					msg_list.append(msg)
					rm_doc.delete(ignore_permissions=True)
					frappe.log_error("Reservation Deleted", f"Rezerved Raw Materials {row.name} deleted for item {item_code} (Job Card: {doc.name})")
				else:
					msg = f"[URETIM PLANLAMA] Rezerv GÜNCELLENDİ: {row.name} ({item_code}) -> {new_qty}"
					print(msg)
					msg_list.append(msg)
					rm_doc.quantity = new_qty
					rm_doc.save(ignore_permissions=True)
					frappe.log_error("Reservation Updated", f"Rezerved Raw Materials {row.name} updated to {new_qty} for item {item_code} (Job Card: {doc.name})")
			# Uzun vadeli rezervden kullanılan miktarı da güncelle
			long_term_usage = frappe.get_all(
				"Long Term Reserve Usage",
				filters={"sales_order": sales_order, "item_code": item_code},
				fields=["name", "used_qty"]
			)
			for usage in long_term_usage:
				usage_doc = frappe.get_doc("Long Term Reserve Usage", usage.name)
				if usage_doc.used_qty > used_qty:
					usage_doc.used_qty -= used_qty
					usage_doc.save(ignore_permissions=True)
					msg = f"[URETIM PLANLAMA] Uzun Vadeli Rezerv GÜNCELLENDİ: {usage.name} ({item_code}) -> {usage_doc.used_qty}"
					print(msg)
					msg_list.append(msg)
					frappe.log_error("Long Term Reserve Updated", f"Long Term Reserve Usage {usage.name} updated to {usage_doc.used_qty} for item {item_code} (Job Card: {doc.name})")
				else:
					msg = f"[URETIM PLANLAMA] Uzun Vadeli Rezerv SIFIRLANDI ve SİLİNDİ: {usage.name} ({item_code})"
					print(msg)
					msg_list.append(msg)
					usage_doc.delete(ignore_permissions=True)
					frappe.log_error("Long Term Reserve Deleted", f"Long Term Reserve Usage {usage.name} deleted for item {item_code} (Job Card: {doc.name})")
		stock_entry_found = True
	# Eğer hiç Stock Entry yoksa, eski yöntemi kullan (Job Card items tablosu)
	if not stock_entry_found:
		for item in getattr(doc, "items", []):
			item_code = item.item_code
			used_qty = item.consumed_qty or item.completed_qty or item.qty or 0
			msg = f"[URETIM PLANLAMA] JobCardItem: {item_code}, Kullanılan Miktar: {used_qty}"
			print(msg)
			msg_list.append(msg)
			reserved = frappe.get_all(
				"Rezerved Raw Materials",
				filters={"sales_order": sales_order, "item_code": item_code},
				fields=["name", "quantity"]
			)
			for row in reserved:
				rm_doc = frappe.get_doc("Rezerved Raw Materials", row.name)
				new_qty = max(0, (rm_doc.quantity or 0) - used_qty)
				if new_qty == 0:
					msg = f"[URETIM PLANLAMA] Rezerv SIFIRLANDI ve SİLİNDİ: {row.name} ({item_code})"
					print(msg)
					msg_list.append(msg)
					rm_doc.delete(ignore_permissions=True)
					frappe.log_error("Reservation Deleted (Fallback)", f"Rezerved Raw Materials {row.name} deleted for item {item_code} (Job Card: {doc.name})")
				else:
					msg = f"[URETIM PLANLAMA] Rezerv GÜNCELLENDİ: {row.name} ({item_code}) -> {new_qty}"
					print(msg)
					msg_list.append(msg)
					rm_doc.quantity = new_qty
					rm_doc.save(ignore_permissions=True)
					frappe.log_error("Reservation Updated (Fallback)", f"Rezerved Raw Materials {row.name} updated to {new_qty} for item {item_code} (Job Card: {doc.name})")
			# Uzun vadeli rezervden kullanılan miktarı da güncelle
			long_term_usage = frappe.get_all(
				"Long Term Reserve Usage",
				filters={"sales_order": sales_order, "item_code": item_code},
				fields=["name", "used_qty"]
			)
			for usage in long_term_usage:
				usage_doc = frappe.get_doc("Long Term Reserve Usage", usage.name)
				if usage_doc.used_qty > used_qty:
					usage_doc.used_qty -= used_qty
					usage_doc.save(ignore_permissions=True)
					msg = f"[URETIM PLANLAMA] Uzun Vadeli Rezerv GÜNCELLENDİ: {usage.name} ({item_code}) -> {usage_doc.used_qty}"
					print(msg)
					msg_list.append(msg)
					frappe.log_error("Long Term Reserve Updated (Fallback)", f"Long Term Reserve Usage {usage.name} updated to {usage_doc.used_qty} for item {item_code} (Job Card: {doc.name})")
				else:
					msg = f"[URETIM PLANLAMA] Uzun Vadeli Rezerv SIFIRLANDI ve SİLİNDİ: {usage.name} ({item_code})"
					print(msg)
					msg_list.append(msg)
					usage_doc.delete(ignore_permissions=True)
					frappe.log_error("Long Term Reserve Deleted (Fallback)", f"Long Term Reserve Usage {usage.name} deleted for item {item_code} (Job Card: {doc.name})")
	msg = "[URETIM PLANLAMA] Rezerv güncelleme işlemi tamamlandı!"
	print(msg)
	msg_list.append(msg)
	frappe.log_error("[URETIM PLANLAMA] Rezerv güncelleme tamamlandı", f"Job Card: {doc.name}")
	frappe.db.commit()
	# Kullanıcıya toplu mesaj göster
	frappe.msgprint("<br>".join(msg_list), indicator="green")
	frappe.log_error("[URETIM PLANLAMA TEST] Job Card fonksiyonu SON", f"Job Card: {getattr(doc, 'name', None)}")

@frappe.whitelist()
def test_reservation_log_and_popup():
	"""
	Sunucu logu ve kullanıcı popup'ı test fonksiyonu.
	Hem frappe.msgprint ile popup, hem frappe.log_error ile log bırakır.
	"""
	msg = "[URETIM PLANLAMA TEST] Popup ve log testi başarılı!"
	frappe.msgprint(msg, indicator="green")
	frappe.log_error("[URETIM PLANLAMA TEST]", msg)
	print(msg)
	return {"success": True, "message": msg}

def restore_reservations_on_work_order_cancel(doc, method):
	# İlgili satış siparişi ve hammaddeleri bul
	sales_order = getattr(doc, "sales_order", None)
	if not sales_order:
		return
	for item in getattr(doc, "required_items", []):
		item_code = item.item_code
		qty = item.required_qty
		# Rezerv kaydı var mı kontrol et
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
 