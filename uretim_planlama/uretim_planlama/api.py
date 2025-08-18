"""
Üretim Planlama API Modülü

Bu modül üretim planlama sistemi için gerekli tüm API fonksiyonlarını içerir.

Fonksiyon Grupları:
1. Üretim Planlama (Production Planning)
2. Haftalık Üretim Takvimi (Weekly Production Schedule)
3. İş Emirleri (Work Orders)
4. Stok Yönetimi (Stock Management)
5. Kesim Planı (Cutting Plan)
6. Takvim Entegrasyonu (Calendar Integration)
7. BOM Yönetimi (BOM Management)
8. Yardımcı Fonksiyonlar (Utility Functions)

Geliştirici: Uretim Planlama Takımı
Versiyon: 1.0
Son Güncelleme: 2024
"""

from calendar import monthrange
from datetime import timedelta

import frappe
import pandas as pd
from frappe import _
from frappe.utils import add_days, get_datetime, getdate

day_name_tr = {
	"Monday": "Pazartesi",
	"Tuesday": "Salı",
	"Wednesday": "Çarşamba",
	"Thursday": "Perşembe",
	"Friday": "Cuma",
	"Saturday": "Cumartesi",
	"Sunday": "Pazar",
}

status_map = {
	"In Process": "Devam ediyor",
	"Completed": "Tamamlandı",
	"Not Started": "Açık",
	"Açık": "Açık",
	"Devam ediyor": "Devam ediyor",
	"Tamamlandı": "Tamamlandı",
	"İptal Edildi": "İptal Edildi",
}


# ============================================================================
# 1. HAFTALIK ÜRETİM TAKVİMİ (WEEKLY PRODUCTION SCHEDULE)
# ============================================================================

@frappe.whitelist()
def get_weekly_production_schedule(
	year=None, month=None, week_start=None, week_end=None, workstation=None, status=None
):
	if year and month:
		start_date = getdate(f"{year}-{month}-01")
		last_day = monthrange(int(year), int(month))[1]
		end_date = getdate(f"{year}-{month}-{last_day}")
	elif week_start and week_end:
		start_date = getdate(week_start)
		end_date = getdate(week_end)
	else:
		start_date = getdate()
		end_date = add_days(start_date, 6)

	while start_date.weekday() != 0:
		start_date -= timedelta(days=1)

	workstation_filters = {"name": workstation} if workstation else {}
	workstations = frappe.get_all(
		"Workstation", filters=workstation_filters, fields=["name", "holiday_list"]
	)

	# Tüm operasyonları topluca çek
	operation_filters = {
		"planned_start_time": ["between", [str(start_date), f"{end_date!s} 23:59:59"]]
	}
	if workstation:
		operation_filters["workstation"] = workstation
	if status:
		operation_filters["status"] = status
	all_operations = frappe.get_all(
		"Work Order Operation",
		filters=operation_filters,
		fields=[
			"name",
			"parent as work_order",
			"operation",
			"workstation",
			"planned_start_time",
			"planned_end_time",
			"status",
			"actual_start_time",
			"actual_end_time",
			"time_in_mins",
			"completed_qty",
		],
	)
	# Tüm work order isimlerini topla
	work_order_names = list(set([op["work_order"] for op in all_operations]))
	# Tüm work order'ları topluca çek
	work_orders = {
		wo.name: wo
		for wo in frappe.get_all(
			"Work Order",
			filters={"name": ["in", work_order_names]},
			fields=[
				"name",
				"item_name",
				"production_item",
				"bom_no",
				"sales_order",
				"produced_qty",
			],
		)
	}
	# Tüm sales order isimlerini topla
	sales_order_names = list(
		set([wo.sales_order for wo in work_orders.values() if wo.sales_order])
	)
	# Tüm sales order'ları topluca çek (customer ve custom_end_customer ile)
	sales_orders = {}
	if sales_order_names:
		for so in frappe.get_all(
			"Sales Order",
			filters={"name": ["in", sales_order_names]},
			fields=["name", "customer", "custom_end_customer"],
		):
			sales_orders[so.name] = so
	# Tüm job card'ları topluca çek
	job_cards = frappe.get_all(
		"Job Card",
		filters={"work_order": ["in", work_order_names]},
		fields=[
			"name",
			"work_order",
			"operation",
			"for_quantity",
			"status",
			"total_completed_qty",
		],
	)
	job_card_map = {}
	for jc in job_cards:
		key = (jc["work_order"], jc["operation"])
		job_card_map[key] = jc

	schedule = []
	for ws in workstations:
		ws_ops = [op for op in all_operations if op["workstation"] == ws.name]
		# Çalışma saatlerini child table'dan çek
		ws_doc = frappe.get_doc("Workstation", ws.name)
		work_hours = []
		for row in getattr(ws_doc, "working_hours", []):
			if getattr(row, "enabled", 1):
				work_hours.append(
					{"start_time": row.start_time, "end_time": row.end_time}
				)
		daily_work_minutes = {}
		from datetime import datetime

		for i in range(7):
			total = 0
			for wh in work_hours:
				s = datetime.strptime(str(wh["start_time"]), "%H:%M:%S")
				e = datetime.strptime(str(wh["end_time"]), "%H:%M:%S")
				diff = (e - s).seconds // 60
				total += diff
			daily_work_minutes[i] = total
		day_schedule = {}
		ops_in_this_week = set()
		total_hours = 0
		total_operations = 0
		daily_summary = {}
		if work_hours:
			for i in range(7):
				total = 0
				for wh in work_hours:
					start = wh["start_time"]
					end = wh["end_time"]
					s = (
						datetime.strptime(str(start), "%H:%M:%S")
						if ":" in str(start)
						else datetime.strptime(str(start), "%H:%M")
					)
					e = (
						datetime.strptime(str(end), "%H:%M:%S")
						if ":" in str(end)
						else datetime.strptime(str(end), "%H:%M")
					)
					diff = (e - s).seconds // 60
					total += diff
				daily_work_minutes[i] = total
		else:
			for i in range(7):
				daily_work_minutes[i] = 0
		for op in ws_ops:
			ops_in_this_week.add(op["operation"])
			work_order = work_orders.get(op["work_order"], {})
			job_card = job_card_map.get((op["work_order"], op["operation"]))
			op_status = ""
			if job_card and job_card.get("status"):
				op_status = job_card["status"]
			elif op["completed_qty"] > 0:
				op_status = "Devam Ediyor"
			elif op["actual_start_time"]:
				op_status = "Başladı"
			start_dt = get_datetime(op["planned_start_time"])
			end_dt = get_datetime(op["planned_end_time"])
			time_in_mins = (
				int((end_dt - start_dt).total_seconds() // 60)
				if start_dt and end_dt
				else 0
			)
			total_hours += time_in_mins / 60
			total_operations += 1
			daily_summary.setdefault(
				day_name_tr[start_dt.strftime("%A")], {"planned_minutes": 0, "jobs": 0}
			)
			daily_summary[day_name_tr[start_dt.strftime("%A")]]["planned_minutes"] += (
				time_in_mins
			)
			daily_summary[day_name_tr[start_dt.strftime("%A")]]["jobs"] += 1
			# İlgili sales order'dan bayi ve müşteri bilgisini çek
			so = (
				sales_orders.get(work_order.get("sales_order"))
				if work_order.get("sales_order")
				else None
			)
			customer = so["customer"] if so and so.get("customer") else ""
			custom_end_customer = (
				so["custom_end_customer"] if so and so.get("custom_end_customer") else ""
			)
			day_schedule.setdefault(day_name_tr[start_dt.strftime("%A")], []).append(
				{
					"name": job_card["name"] if job_card else "",
					"status": job_card["status"]
					if job_card and job_card.get("status")
					else status_map.get(op["status"] or "", "Tanımsız"),
					"qty_to_manufacture": job_card["for_quantity"] if job_card else 0,
					"total_completed_qty": work_order.get("produced_qty", 0),
					"item_name": work_order.get("item_name", ""),
					"production_item": work_order.get("production_item", ""),
					"bom_no": work_order.get("bom_no", ""),
					"sales_order": work_order.get("sales_order", ""),
					"customer": customer,
					"custom_end_customer": custom_end_customer,
					"work_order": op["work_order"],
					"operation": op["operation"] or "Operasyon Yok",
					"color": get_color_for_sales_order(work_order.get("sales_order", "")),
					"start_time": start_dt.strftime("%Y-%m-%d %H:%M"),
					"end_time": end_dt.strftime("%Y-%m-%d %H:%M"),
					"expected_start_date": op["planned_start_time"],
					"expected_end_date": op["planned_end_time"],
					"actual_start_date": op["actual_start_time"],
					"actual_end_date": op["actual_end_time"],
					"total_time_in_mins": int((end_dt - start_dt).total_seconds() // 60),
					"time": f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}",
					"employee": "",
					"duration": time_in_mins,
					"op_status": op_status,
				}
			)
		daily_info = {}
		for i, day in enumerate(
			["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
		):
			planned = daily_summary.get(day, {}).get("planned_minutes", 0)
			jobs = daily_summary.get(day, {}).get("jobs", 0)
			work_min = daily_work_minutes.get(i, 0)
			doluluk = int((planned / work_min) * 100) if work_min > 0 else 0
			daily_info[day] = {
				"work_minutes": work_min,
				"planned_minutes": planned,
				"jobs": jobs,
				"doluluk": doluluk,
			}
		if day_schedule:
			schedule.append(
				{
					"name": ws.name,
					"schedule": day_schedule,
					"operations": sorted(list(ops_in_this_week)),
					"total_hours": round(total_hours, 1),
					"total_operations": total_operations,
					"work_hours": work_hours,
					"daily_info": daily_info,
				}
			)
	week_dates = get_week_dates(start_date)
	# Sadece ilgili istasyonların holiday_list'leri ile holiday sorgusu
	holiday_lists = list(
		set([ws["holiday_list"] for ws in workstations if ws.get("holiday_list")])
	)
	holidays = []
	for hl in holiday_lists:
		for h in frappe.get_all(
			"Holiday",
			filters={"parent": hl, "holiday_date": ["between", [start_date, end_date]]},
			fields=["holiday_date", "description"],
		):
			holidays.append(
				{"date": str(h.holiday_date), "reason": h.description or "Tatil"}
			)
	holiday_map = {h["date"]: h["reason"] for h in holidays}
	days = []
	for d in week_dates:
		iso = d.strftime("%Y-%m-%d")
		weekday = day_name_tr[d.strftime("%A")]
		is_weekend = d.weekday() >= 5
		is_holiday = iso in holiday_map
		days.append(
			{
				"date": d,
				"iso": iso,
				"weekday": weekday,
				"isWeekend": is_weekend,
				"isHoliday": is_holiday,
				"holidayReason": holiday_map[iso] if is_holiday else "",
			}
		)
	return {
		"workstations": schedule,
		"holidays": holidays,
		"start_date": start_date.strftime("%d-%m-%Y"),
		"end_date": end_date.strftime("%d-%m-%Y"),
		"days": days,
	}


# ============================================================================
# 2. YARDIMCI FONKSİYONLAR (UTILITY FUNCTIONS)
# ============================================================================

def get_color_for_sales_order(sales_order):
	if not sales_order:
		return "#cdeffe"
	color_palette = [
		"#FFA726",
		"#66BB6A",
		"#29B6F6",
		"#AB47BC",
		"#EF5350",
		"#FF7043",
		"#26C6DA",
		"#D4E157",
	]
	return color_palette[sum(ord(c) for c in sales_order) % len(color_palette)]


def get_week_dates(start_date):
	# Pazartesi'den başlat
	monday = start_date - timedelta(days=start_date.weekday())
	# Haftanın günlerini oluştur
	return [monday + timedelta(days=i) for i in range(7)]


# ============================================================================
# 3. İŞ EMİRLERİ VE OPERASYONLAR (WORK ORDERS & OPERATIONS)
# ============================================================================

@frappe.whitelist()
def reschedule_operation(work_order, operation, new_date):
	try:
		work_order_op = frappe.get_list(
			"Work Order Operation",
			filters={"parent": work_order, "operation": operation},
			fields=["name", "planned_start_time", "planned_end_time"],
		)
		if not work_order_op:
			frappe.throw("Operasyon bulunamadı")

		op = frappe.get_doc("Work Order Operation", work_order_op[0].name)
		current_start = get_datetime(op.planned_start_time)
		duration = get_datetime(op.planned_end_time) - current_start

		new_start = get_datetime(f"{new_date} {current_start.strftime('%H:%M:%S')}")
		new_end = new_start + duration

		op.planned_start_time = new_start
		op.planned_end_time = new_end
		op.save()
		frappe.db.commit()
		return True

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Operasyon Yeniden Planlama Hatası")
		frappe.throw(str(e))


# ============================================================================
# 4. DIŞA AKTARMA VE RAPORLAMA (EXPORT & REPORTING)
# ============================================================================

@frappe.whitelist()
def export_schedule(start_date, end_date, workstation=None, status=None):
	try:
		data = get_weekly_production_schedule(
			week_start=start_date,
			week_end=end_date,
			workstation=workstation,
			status=status,
		)

		rows = []
		for ws in data["workstations"]:
			for day, operations in ws["schedule"].items():
				for op in operations:
					rows.append(
						{
							"İş İstasyonu": ws["name"],
							"Gün": day,
							"Operasyon": op["operation"],
							"İş Emri": op["work_order"],
							"Ürün": op["item_name"],
							"Miktar": op["qty_to_manufacture"],
							"Durum": op["status"],
							"Başlangıç": op["start_time"],
							"Bitiş": op["end_time"],
							"Çalışan": op.get("employee", ""),
							"Süre (dk)": op.get("duration", 0),
						}
					)

		if not rows:
			frappe.throw("Dışa aktarılacak veri bulunamadı")

		df = pd.DataFrame(rows)
		file_name = f"uretim_planlama_{start_date}_{end_date}.xlsx"
		file_path = frappe.get_site_path("private", "files", file_name)

		with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
			df.to_excel(writer, index=False, sheet_name="Üretim Planı")
			worksheet = writer.sheets["Üretim Planı"]
			for i, col in enumerate(df.columns):
				max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
				worksheet.set_column(i, i, max_length)

		return f"/private/files/{file_name}"

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Üretim Planı Dışa Aktarma Hatası")
		frappe.throw(str(e))


@frappe.whitelist()
def get_weekly_work_orders(
	week_start=None, week_end=None, workstation=None, sales_order=None, status=None
):
	from datetime import timedelta

	from frappe.utils import getdate

	if week_start and week_end:
		start_date = getdate(week_start)
		end_date = getdate(week_end)
	else:
		start_date = getdate()
		end_date = start_date + timedelta(days=6)
	# Pazartesi'ye çek
	while start_date.weekday() != 0:
		start_date -= timedelta(days=1)
	filters = {
		"planned_start_date": ["<=", end_date],
		"planned_end_date": [">=", start_date],
	}
	if workstation:
		filters["workstation"] = workstation
	if sales_order:
		filters["sales_order"] = sales_order
	if status:
		filters["status"] = status
	work_orders = frappe.get_all(
		"Work Order",
		filters=filters,
		fields=[
			"name",
			"sales_order",
			"status",
			"planned_start_date",
			"planned_end_date",
			"bom_no",
			"production_plan",
			"produced_qty",
		],
	)
	# Satış siparişine göre gruplama
	sales_order_map = {}
	for wo in work_orders:
		so = wo.sales_order or "Diğer"
		if so not in sales_order_map:
			sales_order_map[so] = []
		# Operasyon bilgisi (ilk operation child'ı)
		op_info = ""
		op_child = frappe.get_all(
			"Work Order Operation",
			filters={"parent": wo.name},
			fields=["operation"],
			limit=1,
		)
		if op_child:
			op_info = op_child[0].operation
		wo["operation_info"] = op_info
		sales_order_map[so].append(wo)
	# Haftanın günleri
	week_dates = get_week_dates(start_date)
	days = []
	for d in week_dates:
		iso = d.strftime("%Y-%m-%d")
		weekday = day_name_tr[d.strftime("%A")]
		is_weekend = d.weekday() >= 5
		days.append({"date": d, "iso": iso, "weekday": weekday, "isWeekend": is_weekend})
	return {
		"sales_orders": sales_order_map,
		"days": days,
		"start_date": start_date.strftime("%Y-%m-%d"),
		"end_date": end_date.strftime("%Y-%m-%d"),
	}


# ============================================================================
# 5. İŞ KARTLARI VE İŞ EMİRİ DETAYLARI (JOB CARDS & WORK ORDER DETAILS)
# ============================================================================

@frappe.whitelist()
def get_job_card_detail(job_card_id):
	job_card = frappe.get_doc("Job Card", job_card_id)
	return {
		"name": getattr(job_card, "name", ""),
		"status": getattr(job_card, "status", ""),
		"work_order": getattr(job_card, "work_order", ""),
		"sales_order": getattr(job_card, "sales_order", ""),
		"item_name": getattr(job_card, "item_name", ""),
		"production_item": getattr(job_card, "production_item", ""),
		"bom_no": getattr(job_card, "bom_no", ""),
		"for_quantity": getattr(job_card, "for_quantity", getattr(job_card, "qty", "")),
		"total_completed_qty": getattr(
			job_card, "total_completed_qty", getattr(job_card, "completed_qty", "")
		),
		"operation": getattr(job_card, "operation", ""),
		"expected_start_date": getattr(
			job_card,
			"expected_start_date",
			getattr(job_card, "from_time", getattr(job_card, "planned_start_time", "")),
		),
		"expected_end_date": getattr(
			job_card,
			"expected_end_date",
			getattr(job_card, "to_time", getattr(job_card, "planned_end_time", "")),
		),
		"actual_start_date": getattr(
			job_card, "actual_start_date", getattr(job_card, "actual_start_time", "")
		),
		"actual_end_date": getattr(
			job_card, "actual_end_date", getattr(job_card, "actual_end_time", "")
		),
		"total_time_in_mins": getattr(
			job_card, "total_time_in_mins", getattr(job_card, "time_in_mins", "")
		),
		"time_required": getattr(
			job_card, "time_required", getattr(job_card, "planned_operating_time", "")
		),
	}


@frappe.whitelist()
def get_work_order_detail(work_order_id):
	wo = frappe.get_doc("Work Order", work_order_id)
	operations = []
	# Operasyonlar child tablosu
	op_children = frappe.get_all(
		"Work Order Operation",
		filters={"parent": work_order_id},
		fields=[
			"operation",
			"workstation",
			"status",
			"completed_qty",
			"planned_start_time",
			"planned_end_time",
			"actual_start_time",
			"actual_end_time",
			"time_in_mins",
		],
		order_by="planned_start_time asc",
	)
	# İlgili iş kartlarını çek (doğru alanlarla)
	job_cards = frappe.get_all(
		"Job Card",
		filters={"work_order": work_order_id},
		fields=["operation", "status", "actual_start_date", "actual_end_date"],
	)
	job_card_map = {jc["operation"]: jc for jc in job_cards}
	for op in op_children:
		jc = job_card_map.get(op["operation"])
		status = jc["status"] if jc and jc.get("status") else op.get("status", "")
		actual_start = (
			jc["actual_start_date"]
			if jc and jc.get("actual_start_date")
			else op.get("actual_start_time", "")
		)
		actual_end = (
			jc["actual_end_date"]
			if jc and jc.get("actual_end_date")
			else op.get("actual_end_time", "")
		)
		planned_start = op.get("planned_start_time")
		planned_end = op.get("planned_end_time")
		time_str = ""
		if planned_start and planned_end:
			try:
				from frappe.utils import get_datetime

				s = get_datetime(planned_start)
				e = get_datetime(planned_end)
				time_str = f"{s.strftime('%H:%M')}-{e.strftime('%H:%M')}"
			except:
				time_str = ""
		operations.append(
			{
				"operation": op.get("operation", ""),
				"workstation": op.get("workstation", ""),
				"status": status,
				"completed_qty": op.get("completed_qty", ""),
				"planned_start_time": planned_start,
				"planned_end_time": planned_end,
				"time": time_str,
				"actual_start_time": actual_start,
				"actual_end_time": actual_end,
				"duration": op.get("time_in_mins", ""),
			}
		)
	return {
		"name": getattr(wo, "name", ""),
		"status": getattr(wo, "status", ""),
		"sales_order": getattr(wo, "sales_order", ""),
		"bom_no": getattr(wo, "bom_no", ""),
		"production_plan": getattr(wo, "production_plan", ""),
		"qty": getattr(wo, "qty", ""),
		"produced_qty": getattr(wo, "produced_qty", ""),
		"planned_start_date": getattr(
			wo, "planned_start_date", getattr(wo, "from_time", "")
		),
		"planned_end_date": getattr(wo, "planned_end_date", getattr(wo, "to_time", "")),
		"total_time_in_mins": getattr(
			wo, "total_time_in_mins", getattr(wo, "time_in_mins", "")
		),
		"operations": operations,
	}


# ============================================================================
# 6. SATIŞ SİPARİŞLERİ VE İŞ EMİRLERİ (SALES ORDERS & WORK ORDERS)
# ============================================================================

@frappe.whitelist()
def get_sales_order_work_orders(sales_order):
	"""
	Bir sipariş için tüm iş emirlerini ve operasyon detaylarını getir
	"""
	# Sipariş için tüm iş emirlerini çek
	work_orders = frappe.get_all(
		"Work Order",
		filters={"sales_order": sales_order, "docstatus": 1},
		fields=[
			"name",
			"status",
			"qty",
			"produced_qty",
			"planned_start_date",
			"planned_end_date",
			"bom_no",
			"production_plan"
		],
		order_by="planned_start_date asc"
	)
	
	work_order_details = []
	
	for wo in work_orders:
		# Her iş emri için operasyonları çek
		operations = frappe.get_all(
			"Work Order Operation",
			filters={"parent": wo.name},
			fields=[
				"operation",
				"workstation",
				"status",
				"completed_qty",
				"planned_start_time",
				"planned_end_time",
				"actual_start_time",
				"actual_end_time",
				"time_in_mins",
			],
			order_by="planned_start_time asc"
		)
		
		# İş kartlarını çek
		job_cards = frappe.get_all(
			"Job Card",
			filters={"work_order": wo.name},
			fields=["operation", "status", "actual_start_date", "actual_end_date"],
		)
		job_card_map = {jc["operation"]: jc for jc in job_cards}
		
		# Operasyonları işle
		processed_operations = []
		for op in operations:
			jc = job_card_map.get(op["operation"])
			status = jc["status"] if jc and jc.get("status") else op.get("status", "")
			actual_start = (
				jc["actual_start_date"]
				if jc and jc.get("actual_start_date")
				else op.get("actual_start_time", "")
			)
			actual_end = (
				jc["actual_end_date"]
				if jc and jc.get("actual_end_date")
				else op.get("actual_end_time", "")
			)
			
			processed_operations.append({
				"operation": op.get("operation", ""),
				"workstation": op.get("workstation", ""),
				"status": status,
				"completed_qty": op.get("completed_qty", ""),
				"planned_start_time": op.get("planned_start_time"),
				"planned_end_time": op.get("planned_end_time"),
				"actual_start_time": actual_start,
				"actual_end_time": actual_end,
				"duration": op.get("time_in_mins", ""),
			})
		
		work_order_details.append({
			"name": wo.name,
			"status": wo.status,
			"qty": wo.qty,
			"produced_qty": wo.produced_qty,
			"planned_start_date": wo.planned_start_date,
			"planned_end_date": wo.planned_end_date,
			"bom_no": wo.bom_no,
			"production_plan": wo.production_plan,
			"operations": processed_operations
		})
	
	return work_order_details


# ============================================================================
# 7. TAKVİM ENTEGRASYONU (CALENDAR INTEGRATION)
# ============================================================================

@frappe.whitelist()
def get_work_orders_for_calendar(start, end, include_draft=False):
	"""
	Frappe Calendar için iş emirlerini döndürür.
	start ve end parametreleri takvimde gösterilecek aralığı belirtir.
	include_draft parametresi taslak iş emirlerinin dahil edilip edilmeyeceğini belirtir.
	"""
	import datetime

	# Onaylanmış iş emirleri (tarih filtresi ile)
	approved_wos = frappe.get_all(
		"Work Order",
		fields=[
			"name",
			"planned_start_date",
			"planned_end_date",
			"status",
			"sales_order",
			"docstatus",
		],
		filters={
			"docstatus": 1,
			"planned_start_date": ["<=", end],
			"planned_end_date": [">=", start],
		},
	)
	# Taslak iş emirleri (tarih filtresi olmadan)
	draft_wos = []
	if include_draft:
		draft_wos = frappe.get_all(
			"Work Order",
			fields=[
				"name",
				"planned_start_date",
				"planned_end_date",
				"status",
				"sales_order",
				"docstatus",
			],
			filters={"docstatus": 0},
		)
	work_orders = approved_wos + draft_wos

	# Sales Order bilgilerini topluca çek
	sales_order_names = list(
		set([wo.sales_order for wo in work_orders if wo.sales_order])
	)
	sales_orders = {}
	if sales_order_names:
		for so in frappe.get_all(
			"Sales Order",
			filters={"name": ["in", sales_order_names]},
			fields=["name", "customer", "custom_end_customer"],
		):
			sales_orders[so.name] = so

	today_str = datetime.date.today().strftime("%Y-%m-%d")
	events = []
	for wo in work_orders:
		customer = None
		custom_end_customer = None
		if wo.sales_order and wo.sales_order in sales_orders:
			customer = sales_orders[wo.sales_order].customer
			custom_end_customer = sales_orders[wo.sales_order].custom_end_customer
		# Status yönetimi:
		status = "Draft" if wo.docstatus == 0 else (wo.status or "Not Started")
		# Taslak iş emirlerinde tarih yoksa bugünün tarihini ata
		start_date = wo.planned_start_date or (today_str if wo.docstatus == 0 else None)
		end_date = wo.planned_end_date or (today_str if wo.docstatus == 0 else None)
		# Saatleri ayarla
		if wo.docstatus == 1 and start_date:
			try:
				# ISO 8601 formatını işle
				if "T" in str(start_date):
					dt = datetime.datetime.fromisoformat(
						str(start_date).replace("Z", "+00:00")
					)
				else:
					# Eski format için
					dt = datetime.datetime.strptime(
						str(start_date),
						"%Y-%m-%d" if len(str(start_date)) == 10 else "%Y-%m-%d %H:%M:%S",
					)
				start_date = dt.replace(hour=8, minute=0, second=0).strftime(
					"%Y-%m-%d %H:%M:%S"
				)
				end_date = (dt.replace(hour=9, minute=0, second=0)).strftime(
					"%Y-%m-%d %H:%M:%S"
				)
			except ValueError:
				# Hata durumunda varsayılan değerleri kullan
				start_date = None
				end_date = None
		elif wo.docstatus == 0 and start_date:
			try:
				# ISO 8601 formatını işle
				if "T" in str(start_date):
					dt = datetime.datetime.fromisoformat(
						str(start_date).replace("Z", "+00:00")
					)
				else:
					# Eski format için
					dt = datetime.datetime.strptime(
						str(start_date),
						"%Y-%m-%d" if len(str(start_date)) == 10 else "%Y-%m-%d %H:%M:%S",
					)
				start_date = dt.replace(hour=8, minute=0, second=0).strftime(
					"%Y-%m-%d %H:%M:%S"
				)
				end_date = start_date
			except ValueError:
				# Hata durumunda varsayılan değerleri kullan
				start_date = None
				end_date = None
		# Eğer onaylanmış iş emrinde tarih yoksa, event ekleme
		if wo.docstatus == 1 and (not start_date or not end_date):
			continue
		events.append(
			{
				"id": wo.name,
				"title": wo.name,
				"start": start_date,
				"end": end_date,
				"status": status,
				"sales_order": wo.sales_order,
				"customer": customer,
				"custom_end_customer": custom_end_customer,
				"is_draft": wo.docstatus == 0,
			}
		)
	return events


@frappe.whitelist()
def get_holidays_for_calendar(start, end):
	holidays = {}
	for hl in frappe.get_all("Holiday List", fields=["name"]):
		for h in frappe.get_all(
			"Holiday",
			filters={"parent": hl.name, "holiday_date": ["between", [start, end]]},
			fields=["holiday_date", "description"],
		):
			holidays[str(h.holiday_date)] = h.description or "Tatil"
	return holidays


@frappe.whitelist()
def update_work_order_date(work_order_id, new_start):
	try:
		from datetime import datetime, timedelta

		def to_8am(dt_str):
			return datetime.strptime(dt_str, "%Y-%m-%d").replace(
				hour=8, minute=0, second=0
			)

		work_order = frappe.get_doc("Work Order", work_order_id)
		old_start = work_order.planned_start_date
		old_end = work_order.planned_end_date
		# Eğer eski tarihlerden biri yoksa duration=0 kabul et
		if old_start and old_end:
			duration = (old_end - old_start).days
		else:
			duration = 0
		work_order.planned_start_date = to_8am(new_start)
		if duration > 0:
			new_end = to_8am(new_start) + timedelta(days=duration)
			work_order.planned_end_date = new_end
		else:
			work_order.planned_end_date = to_8am(new_start)
		work_order.save()
		# Operasyonları da yeni tarihe göre güncelle
		for op in work_order.operations:
			op.planned_start_time = work_order.planned_start_date
			if duration > 0:
				op.planned_end_time = work_order.planned_end_date
			else:
				op.planned_end_time = work_order.planned_start_date
		work_order.save()
		return {"success": True}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Work Order Date Update Error")
		return {"success": False, "error": str(e)}


# ============================================================================
# 8. ÜRETİM PLANI VE CHART VERİLERİ (PRODUCTION PLAN & CHART DATA)
# ============================================================================

@frappe.whitelist()
def get_production_plan_chart_data(production_plan):
	"""
	Üretim planı için chart verisi döndürür.
	Bu fonksiyon geliştirilmeye ihtiyaç duymaktadır.
	"""
	if not production_plan:
		return None

	try:
		# Get production plan details
		plan = frappe.get_doc("Production Plan", production_plan)

		# Chart data structure
		chart_data = {
			"labels": [],
			"datasets": [
				{"name": "Planlanan Miktar", "values": []},
				{"name": "Tamamlanan Miktar", "values": []},
			],
		}

		# Get items from production plan
		for item in plan.po_items:
			chart_data["labels"].append(item.item_code)
			chart_data["datasets"][0]["values"].append(item.planned_qty)
			chart_data["datasets"][1]["values"].append(item.completed_qty or 0)

		return chart_data
		
	except Exception as e:
		frappe.log_error(f"Chart data hatası: {str(e)}")
		return None


@frappe.whitelist()
def get_daily_cutting_matrix(from_date, to_date):
	"""
	Belirtilen tarih aralığındaki kesim planlarını getirir.
	"""
	try:
		# API çağrısı başladı
		# Tarihleri kontrol et ve formatla
		if not from_date or not to_date:
			frappe.logger().error("[API] Tarih parametreleri eksik")
			return []
		# Tarihleri YYYY-MM-DD formatına çevir
		try:
			from_date = frappe.utils.getdate(from_date).strftime("%Y-%m-%d")
			to_date = frappe.utils.getdate(to_date).strftime("%Y-%m-%d")
		except Exception as e:
			frappe.logger().error(f"[API] Tarih formatı hatası: {e!s}")
			return []
		# Tarihler formatlandı ve SQL sorgusu başlatılıyor
		# SQL sorgusundan docstatus filtresi kaldırıldı
		result = frappe.db.sql(
			"""
            SELECT
                DATE(planning_date) AS date,
                workstation,
                SUM(total_mtul) AS total_mtul,
                SUM(total_quantity) AS total_quantity
            FROM `tabCutting Machine Plan`
            WHERE DATE(planning_date) BETWEEN %s AND %s
            GROUP BY DATE(planning_date), workstation
            ORDER BY DATE(planning_date), workstation
        """,
			(from_date, to_date),
			as_dict=True,
		)
		# SQL sorgusu tamamlandı
		if not result:
			# Veri yoksa örnek veri oluştur
			# Sorgudan veri gelmedi, örnek veri oluşturuluyor
			current_date = frappe.utils.getdate(from_date)
			end_date = frappe.utils.getdate(to_date)
			result = []
			while current_date <= end_date:
				result.append(
					{
						"date": current_date.strftime("%Y-%m-%d"),
						"workstation": "Kesim 1",
						"total_mtul": 0,
						"total_quantity": 0,
					}
				)
				current_date = frappe.utils.add_days(current_date, 1)
			# Örnek veri oluşturuldu
		return result
	except Exception as e:
		frappe.logger().error(f"[API] get_daily_cutting_matrix hatası: {e!s}")
		frappe.logger().error(frappe.get_traceback())
		return []


# ============================================================================
# 9. KESİM PLANI (CUTTING PLAN)
# ============================================================================

@frappe.whitelist()
def generate_cutting_plan(docname):
	"""
	Verilen Production Plan belgesine bağlı po_items verilerine göre;
	- Aynı planlama tarihi ve iş istasyonu varsa o Cutting Machine Plan belgesine ekleme yapılır.
	- Yoksa yeni belge oluşturulur.
	- Her satır sadece bir kez eklenir.
	"""
	doc = frappe.get_doc("Production Plan", docname)

	plan_map = {}  # key: date::workstation → Cutting Machine Plan nesnesi

	for row in doc.po_items:
		# Gerekli alanları al
		workstation_name = row.custom_workstation
		date_obj = row.planned_start_date
		mtul = row.custom_mtul_per_piece
		qty = row.planned_qty

		# Tarih objesini stringe çevir
		date = frappe.utils.getdate(date_obj).isoformat()

		# Zorunlu alan kontrolü
		if not (workstation_name and date and mtul and qty):
			continue

		key = f"{date}::{workstation_name}"

		# plan_map'te yoksa Cutting Plan bul/oluştur
		if key not in plan_map:
			existing_plan = frappe.db.get_value(
				"Cutting Machine Plan",
				filters={"planning_date": date, "workstation": workstation_name},
				fieldname="name",
			)

			if existing_plan:
				plan_doc = frappe.get_doc("Cutting Machine Plan", existing_plan)
			else:
				plan_doc = frappe.new_doc("Cutting Machine Plan")
				plan_doc.planning_date = date
				plan_doc.workstation = workstation_name
				plan_doc.insert(ignore_permissions=True)

			plan_map[key] = plan_doc
		else:
			plan_doc = plan_map[key]

		# Aynı üretim planı + satırı zaten varsa tekrar ekleme
		is_duplicate = any(
			d.production_plan == doc.name and d.production_plan_item == row.name
			for d in plan_doc.plan_details
		)
		if is_duplicate:
			continue

		# Yeni satırı ekle
		plan_doc.append(
			"plan_details",
			{
				"item_code": row.item_code,
				"mtul_per_piece": mtul,
				"quantity": qty,
				"total_mtul": float(mtul) * float(qty),
				"production_plan": doc.name,
				"production_plan_item": row.name,
			},
		)

	# Belgeleri kaydet
	for plan_doc in plan_map.values():
		plan_doc.total_quantity = sum(d.quantity for d in plan_doc.plan_details)
		plan_doc.total_mtul = sum(d.total_mtul for d in plan_doc.plan_details)
		plan_doc.save(ignore_permissions=True)

	return {"success": True, "message": "Kesim Planı Başarıyla Oluşturuldu."}


@frappe.whitelist()
def delete_cutting_plans(docname):
	"""
	Production Plan iptal edildiğinde ilgili kesim planlarını siler.
	"""
	try:
		cutting_plans = frappe.get_all("Cutting Machine Plan", fields=["name"])
		for plan in cutting_plans:
			doc_plan = frappe.get_doc("Cutting Machine Plan", plan.name)
			original_len = len(doc_plan.plan_details)
			updated_rows = [
				d for d in doc_plan.plan_details if d.production_plan != docname
			]

			if len(updated_rows) != original_len:
				doc_plan.set("plan_details", updated_rows)
				if updated_rows:
					doc_plan.total_quantity = sum(d.quantity for d in updated_rows)
					doc_plan.total_mtul = sum(d.total_mtul for d in updated_rows)
					doc_plan.save(ignore_permissions=True)
				else:
					frappe.delete_doc("Cutting Machine Plan", doc_plan.name, force=True)

		return {"success": True, "message": "Kesim Planları Otomatik Olarak Silindi"}

	except Exception as e:
		return {"success": False, "message": f"Kesim Planı Silinemedi: {e!s}"}


# ============================================================================
# 10. STOK YÖNETİMİ (STOCK MANAGEMENT)
# ============================================================================

@frappe.whitelist()
def get_profile_stock_panel(profil=None, depo=None, boy=None, scrap=None):
	"""
	Profil stok paneli için tablo bazında veri seti döner.
	- depo_stoklari: ERPNext anlık stok (mtül), rezerv, kullanılabilir (mtül)
	- boy_bazinda_stok: Boy bazında stok (adet, mtül, rezerv)
	- scrap_profiller: Parça profil kayıtları (açıklama, tarih, vs)
	- hammadde_rezervleri: Rezerve hammaddeler (profil ve depo bazında, ana depo ise alt depolar dahil)
	Filtreler: profil, depo, boy, scrap (opsiyonel)
	"""
	depo_stoklari = []
	boy_bazinda_stok = []
	scrap_profiller = []
	hammadde_rezervleri = []

	# "Sadece Parça" seçiliyse, sadece parça verilerini çek
	if scrap:
		scrap_profiller = get_scrap_profile_entries(profile_code=profil)
	else:
		# "Sadece Parça" seçili değilse, tüm ilgili verileri çek
		depo_stoklari = get_total_stock_summary(profil=profil, depo=depo)
		boy_bazinda_stok = get_profile_stock_by_length(profil=profil, boy=boy, scrap=0)
		scrap_profiller = get_scrap_profile_entries(profile_code=profil)
	# Hammadde rezervleri ürün ve depo filtresine göre gelsin
	hammadde_rezervleri = get_reserved_raw_materials_for_profile(profil=profil, depo=depo) or []

	return {
		"depo_stoklari": depo_stoklari,
		"boy_bazinda_stok": boy_bazinda_stok,
		"scrap_profiller": scrap_profiller,
		"hammadde_rezervleri": hammadde_rezervleri,
	}


@frappe.whitelist()
def create_delivery_package(data):
	"""
	Verilen bilgilerle Accessory Delivery Package oluşturur (malzeme listesi, opti_no, teslim alan, notlar, vb).
	"""
	import json

	try:
		if isinstance(data, str):
			data = json.loads(data)
		
		doc = frappe.new_doc("Accessory Delivery Package")
		doc.opti_no = data.get("opti_no")  # Sadece gerçek OpTi No
		doc.production_plan = data.get("production_plan")  # Üretim planı name'i
		doc.sales_order = data.get("sales_order")
		doc.delivered_to = data.get("delivered_to")
		doc.delivered_by = frappe.session.user
		doc.delivery_date = frappe.utils.now_datetime()
		doc.notes = data.get("notes")
		
		for item in data.get("item_list", []):
			doc.append(
				"item_list",
				{
					"item_code": item.get("item_code"),
					"item_name": item.get("item_name"),
					"qty": item.get("qty"),
					"uom": item.get("uom"),
				},
			)
		
		doc.save()
		frappe.db.commit()
		return {"name": doc.name}
		
	except Exception as e:
		frappe.log_error(f"Delivery package oluşturma hatası: {str(e)}")
		frappe.throw(_("Teslimat paketi oluşturulamadı: {0}").format(str(e)))


# ============================================================================
# 11. STOK ÖZETİ VE MALZEME YÖNETİMİ (STOCK SUMMARY & MATERIAL MANAGEMENT)
# ============================================================================

@frappe.whitelist()
def get_total_stock_summary(profil=None, depo=None):
	"""
	ERPNext Bin tablosundan toplam stok (mtül) bilgisini depo ve ürün bazında döndürür.
	Ayrıca, Rezerved Raw Materials doctype'ından toplam rezerv (mtül) ve kullanılabilir (mtül) değerlerini de ekler.
	"""
	filters = {}
	if profil:
		filters["item_code"] = profil
	if depo:
		filters["warehouse"] = depo
	bins = frappe.get_all(
		"Bin", filters=filters, fields=["item_code", "warehouse", "actual_qty"]
	)
	# item_name ekle
	item_names = {}
	if bins:
		item_codes = list(set([b["item_code"] for b in bins]))
		for item in frappe.get_all(
			"Item",
			filters={"item_code": ["in", item_codes]},
			fields=["item_code", "item_name"],
		):
			item_names[item["item_code"]] = item["item_name"]
	# Rezervleri çek (mtül bazında)
	rezervler = frappe.get_all(
		"Rezerved Raw Materials",
		fields=["item_code", "quantity"],
		filters={"item_code": ["in", [b["item_code"] for b in bins]]} if bins else {},
	)
	rezerv_map = {}
	for r in rezervler:
		rezerv_map.setdefault(r["item_code"], 0)
		rezerv_map[r["item_code"]] += float(r["quantity"] or 0)
	result = []
	for b in bins:
		rezerv_mtul = rezerv_map.get(b["item_code"], 0)
		kullanilabilir_mtul = float(b["actual_qty"] or 0) - rezerv_mtul
		result.append(
			{
				"profil": b["item_code"],
				"profil_adi": item_names.get(b["item_code"], ""),
				"depo": b["warehouse"],
				"toplam_stok_mtul": b["actual_qty"],
				"rezerv_mtul": rezerv_mtul,
				"kullanilabilir_mtul": kullanilabilir_mtul,
			}
		)
	return result


@frappe.whitelist()
def get_materials_by_opti(opti_no):
	"""
	Production Plan için malzeme bilgilerini döndürür.
	MLY entegrasyonu için geliştirilmeye ihtiyaç duymaktadır.
	"""
	try:
		plan = frappe.get_doc("Production Plan", opti_no)
		if not plan:
			frappe.throw(_("Production Plan not found for OpTi No: {0}").format(opti_no))
		
		# Child table'dan sales_orders listesini çek
		sales_orders = [row.sales_order for row in plan.sales_orders if row.sales_order]
		
		# TODO: MLY entegrasyonu için geliştirilecek
		materials = []
		
		return {
			"production_plan": plan.name,
			"sales_orders": sales_orders,
			"materials": materials,
		}
		
	except Exception as e:
		frappe.log_error(f"Materials by opti hatası: {str(e)}")
		frappe.throw(_("Malzeme bilgileri alınamadı: {0}").format(str(e)))


# ============================================================================
# 12. AKSESUAR TESLİMAT PAKETİ (ACCESSORY DELIVERY PACKAGE)
# ============================================================================

@frappe.whitelist()
def get_sales_order_details(order_no):
	try:
		sales_order = frappe.get_doc("Sales Order", order_no)
	except Exception as e:
		frappe.logger().error(f"Sales Order getirme hatası: {e}")
		frappe.throw(_("Sales Order not found."))

	return sales_order


@frappe.whitelist()
def get_materials(opti_no, sales_order):
	values = {"opti_no": opti_no, "sales_order": sales_order}

	# AND (
	#        i.item_group LIKE '%%Aksesuar%%' OR
	#        i.item_group LIKE '%%Montaj ve Izolasyon%%' OR
	#        ig.parent_item_group LIKE '%%Aksesuar%%' OR
	#        ig.parent_item_group LIKE '%%Montaj ve Izolasyon%%'
	#    )

	materials = frappe.db.sql(
		"""
	    SELECT
	        bi.item_code,
			bi.item_name,
	        SUM((bi.qty / bom.quantity) * ppi.planned_qty) AS qty,
	        i.item_group,
	        ig.parent_item_group,
	        i.stock_uom AS uom
	    FROM `tabProduction Plan Item` ppi
	    INNER JOIN `tabProduction Plan` pp ON ppi.parent = pp.name
	    INNER JOIN `tabBOM` bom ON ppi.bom_no = bom.name
	    INNER JOIN `tabBOM Item` bi ON bi.parent = bom.name
	    INNER JOIN `tabItem` i ON i.item_code = bi.item_code
	    INNER JOIN `tabItem Group` ig ON i.item_group = ig.name
	    WHERE pp.custom_opti_no = %(opti_no)s
	    AND ppi.sales_order = %(sales_order)s
	    AND (
	        i.item_group LIKE '%%Aksesuar%%' OR
	        i.item_group LIKE '%%Izolasyon%%' OR
	        ig.parent_item_group LIKE '%%Aksesuar%%' OR
	        ig.parent_item_group LIKE '%%Izolasyon%%'
	    )
	    GROUP BY bi.item_code, i.item_group, ig.parent_item_group, i.stock_uom
	    ORDER BY i.item_group, bi.item_code
		""",
		values=values,
		as_dict=1,
	)

	ppi_items = frappe.db.sql(
		"""
        SELECT ppi.*
        FROM `tabProduction Plan Item` ppi
        INNER JOIN `tabProduction Plan` pp ON ppi.parent = pp.name
        WHERE pp.custom_opti_no = %(opti_no)s
        AND ppi.sales_order = %(sales_order)s
        """,
		values=values,
		as_dict=1,
	)

	result = {"ppi_items": ppi_items, "materials": materials}

	return result


# ============================================================================
# 13. OPTİ VE BOM MALZEMELERİ (OPTI & BOM MATERIALS)
# ============================================================================

@frappe.whitelist()
def get_sales_orders_by_opti(opti):
	try:
		opti_doc = frappe.get_doc("Opti", opti)
	except frappe.DoesNotExistError:
		frappe.throw(frappe._("Opti [{0}] not found").format(opti))
	except Exception as e:
		frappe.logger().error(f"Opti getirme hatası: {e!s}")
		frappe.throw(frappe._("An error occured"))

	return [so.sales_order for so in opti_doc.sales_orders if not so.delivered]


@frappe.whitelist()
def get_bom_materials_by_sales_order(sales_order=None, **kwargs):
	# Parametre dict olarak gelirse düzelt
	if isinstance(sales_order, dict):
		sales_order = sales_order.get("sales_order")
	"""
    Verilen satış siparişine (sales_order) ait Work Order'lardan veya doğrudan Sales Order/BOM'dan ilgili BOM item'larını döndürür.
    Zincir:
    1. Onaylı Work Order → BOM → BOM Item
    2. Onaysız Work Order → BOM → BOM Item
    3. Production Plan üzerinden BOM bul (varsa)
    """
	import frappe

	items = []
	# 1. Onaylı Work Order
	work_orders = frappe.get_all(
		"Work Order",
		filters={"sales_order": sales_order, "docstatus": 1},
		fields=["name", "bom_no", "qty"],
	)
	if not work_orders:
		# 2. Onaysız Work Order
		work_orders = frappe.get_all(
			"Work Order",
			filters={"sales_order": sales_order},
			fields=["name", "bom_no", "qty"],
		)
	else:
		pass
	for wo in work_orders:
		if not wo.bom_no:
			continue
		bom_items = frappe.get_all(
			"BOM Item",
			filters={"parent": wo.bom_no},
			fields=["item_code", "item_name", "qty", "uom"],
		)
		for item in bom_items:
			real_item_name = (
				frappe.db.get_value("Item", item.item_code, "item_name") or item.item_code
			)
			items.append(
				{
					"item_code": item.item_code,
					"item_name": real_item_name,
					"qty": item.qty,
					"uom": item.uom,
				}
			)
	if items:
		return items
	# 3. Production Plan üzerinden BOM bul (varsa)
	plan_name = None
	if sales_order:
		plan_name = frappe.db.get_value(
			"Production Plan Sales Order", {"sales_order": sales_order}, "parent"
		)
	if plan_name:
		plan = frappe.get_doc("Production Plan", plan_name)
		for row in getattr(plan, "po_items", []):
			if getattr(row, "sales_order", None) == sales_order and getattr(
				row, "bom_no", None
			):
				bom_items = frappe.get_all(
					"BOM Item",
					filters={"parent": row.bom_no},
					fields=["item_code", "item_name", "qty", "uom"],
				)
				for item in bom_items:
					real_item_name = (
						frappe.db.get_value("Item", item.item_code, "item_name")
						or item.item_code
					)
					items.append(
						{
							"item_code": item.item_code,
							"item_name": real_item_name,
							"qty": item.qty,
							"uom": item.uom,
						}
					)
		if items:
			return items
	return items


# ============================================================================
# 14. PROFİL STOK YÖNETİMİ (PROFILE STOCK MANAGEMENT)
# ============================================================================

@frappe.whitelist()
def get_reserved_raw_materials_for_profile(profil=None, depo=None):
	"""
	Profil (ürün/mamul veya hammadde) filtresine göre rezerve hammaddeleri döndürür.
	Rezerved Raw Materials doctype'ında depo bilgisi olmadığı için depo filtresi dikkate alınmaz.
	"""
	filters = {}
	if profil:
		filters["item_code"] = profil
	reserved = frappe.get_all(
		"Rezerved Raw Materials",
		filters=filters,
		fields=["item_code", "item_name", "quantity", "sales_order"],
	)
	return reserved


@frappe.whitelist()
def get_profile_stock_by_length(profil=None, boy=None, scrap=None):
	"""
	Profile Stock Ledger'dan boy bazında stokları döndürür.
	Ayrıca Rezerved Raw Materials doctype'ından toplam rezerv (mtül) değerini ekler.
	"""
	filters = {}
	if profil:
		filters["profile_type"] = profil
	if boy:
		try:
			filters["length"] = float(boy)
		except:
			filters["length"] = boy
	if scrap is not None:
		filters["is_scrap_piece"] = int(scrap)
	ledgers = frappe.get_all(
		"Profile Stock Ledger",
		filters=filters,
		fields=[
			"profile_type",
			"length",
			"qty",
			"total_length",
			"is_scrap_piece",
			"modified",
		],
	)
	# item_name ekle
	item_names = {}
	if ledgers:
		item_codes = list(set([l["profile_type"] for l in ledgers]))
		for item in frappe.get_all(
			"Item",
			filters={"item_code": ["in", item_codes]},
			fields=["item_code", "item_name"],
		):
			item_names[item["item_code"]] = item["item_name"]
	# Rezervleri çek (mtül bazında)
	rezervler = frappe.get_all("Rezerved Raw Materials", fields=["item_code", "quantity"])
	rezerv_map = {}
	for r in rezervler:
		rezerv_map.setdefault(r["item_code"], 0)
		rezerv_map[r["item_code"]] += float(r["quantity"] or 0)
	result = []
	for l in ledgers:
		rezerv = rezerv_map.get(l["profile_type"], 0)
		result.append(
			{
				"profil": l["profile_type"],
				"profil_adi": item_names.get(l["profile_type"], ""),
				"boy": l["length"],
				"adet": l["qty"],
				"mtul": l["total_length"],
				"rezerv": rezerv,
				"guncelleme": l["modified"],
			}
		)
	return result


@frappe.whitelist()
def get_scrap_profile_entries(profile_code=None):
    """
    Scrap Profile Entry kayıtlarını döndürür (sadece seçilen profile_code için).
    """
    filters = {}
    if profile_code:
        filters["profile_code"] = profile_code
    entries = frappe.get_all(
        "Scrap Profile Entry",
        filters=filters,
        fields=["name", "profile_code", "length", "qty", "total_length", "description", "entry_date", "modified"]
    )
    # item_name ekle
    item_names = {}
    if entries:
        item_codes = list(set([e["profile_code"] for e in entries]))
        for item in frappe.get_all("Item", filters={"item_code": ["in", item_codes]}, fields=["item_code", "item_name"]):
            item_names[item["item_code"]] = item["item_name"]
    result = []
    for e in entries:
        result.append({
            "profil": e["profile_code"],
            "profil_adi": item_names.get(e["profile_code"], ""),
            "boy": e["length"],
            "adet": e["qty"],
            "mtul": e["total_length"],
            "aciklama": e["description"],
            "tarih": e["entry_date"],
            "guncelleme": e["modified"]
        })
    return result


# ============================================================================
# 15. MONTAJ AKSESUARLARI (ASSEMBLY ACCESSORIES)
# ============================================================================

import json
import frappe

@frappe.whitelist()
def get_assembly_accessory_materials(sales_orders):
    """
    Verilen bir veya birden fazla Sales Order için, ilgili Fiyat2 List ve Fiyat2 Item kayıtlarından
    Stock Code, Stock Name, qty, uom alanlarını döndürür.
    """
    try:
        sales_orders = json.loads(sales_orders)
    except Exception:
        return []
    result = []
    for so in sales_orders:
        fiyat2 = frappe.get_all("Fiyat2 List", filters={"order_no": so}, fields=["name"])
        if not fiyat2:
            continue
        fiyat2_items = frappe.get_all(
            "Fiyat2 Item",
            filters={"parent": fiyat2[0].name},
            fields=["stock_code", "stock_name", "qty", "uom"]
        )
        for item in fiyat2_items:
            result.append({
                "sales_order": so,
                "stock_code": item["stock_code"],
                "stock_name": item["stock_name"],
                "qty": item["qty"],
                "uom": item.get("uom", "")
            })
    return result

@frappe.whitelist()
def get_production_planning_data(filters=None):
	"""
	Üretim planlama paneli için veri getirir
	- Planlanan üretim planları ve satış siparişleri
	- Planlanmamış satış siparişleri
	"""
	try:
		if filters:
			filters = json.loads(filters) if isinstance(filters, str) else filters
		else:
			filters = {}

		# API başladı
		
		# Planlanan üretim planları
		planned_data = get_planned_production_data(filters)
		
		# Planlanmamış satış siparişleri
		unplanned_data = get_unplanned_sales_orders(filters)
		
		# Özet verileri hesapla
		summary = calculate_summary_data(planned_data, unplanned_data)
		
		result = {
			"planned": planned_data,
			"unplanned": unplanned_data,
			"summary": summary
		}
		
		# API tamamlandı
		return result
		
	except Exception as e:
		import traceback
		error_msg = f"Üretim planlama verisi getirme hatası: {str(e)}\n{traceback.format_exc()}"
		frappe.log_error(error_msg)
		frappe.logger().error(f"API HATASI: {error_msg}")
		return {"error": str(e)}

def get_planned_production_data(filters):
	"""
	Planlanan üretim planları ve satış siparişlerini getirir
	"""
	try:
		# Production Plan'ları getir
		production_plans = frappe.get_all(
			"Production Plan",
			fields=[
				"name",
				"from_date",
				"to_date",
				"status",
				"company"
			],
			filters={
				"docstatus": 1,  # Onaylanmış planlar
				"status": ["!=", "Closed"]
			}
		)
		
		# Production Plan'lar işleniyor
		
		planned_data = []
		
		for pp in production_plans:
			# Production Plan işleniyor
			# Bu plana ait satış siparişlerini getir
			sales_orders = get_sales_orders_for_production_plan(pp.name)
			
			for so in sales_orders:
				try:
					# Hafta hesapla
					week_number = get_week_number(so.get("transaction_date"))
					
					# Acil durumu kontrol et
					is_urgent = check_urgent_status(so)
					
					planned_data.append({
						"hafta": week_number,
						"uretim_plani": pp.name,
						"siparis_no": so.get("name"),
						"bayi": so.get("customer"),
						"musteri": so.get("custom_end_customer", ""),
						"siparis_tarihi": so.get("transaction_date"),
						"adet": so.get("qty", 0),
						"mtul": calculate_mtul(so),
						"tip": get_item_type(so.get("item_code")),
						"renk": get_item_color(so.get("item_code")),
						"aciklamalar": so.get("description", ""),
						"acil_durum": "ACİL" if is_urgent else "NORMAL",
						"tahmini_bitis": so.get("delivery_date"),
						"durum": get_turkish_status(pp.get("status")),
						"acil": is_urgent
					})
				except Exception as e:
					frappe.logger().error(f"SO işleme hatası: {so.get('name')} - {str(e)}")
					continue
		
		return planned_data
		
	except Exception as e:
		frappe.logger().error(f"get_planned_production_data hatası: {str(e)}")
		return []

def get_unplanned_sales_orders(filters):
	"""
	Planlanmamış satış siparişlerini getirir
	"""
	try:
		# Production Plan'a dahil edilmemiş satış siparişleri
		planned_so_list = frappe.get_all(
			"Production Plan Item",
			fields=["sales_order"],
			filters={"sales_order": ["is", "set"]}
		)
		
		planned_so_names = [item.sales_order for item in planned_so_list if item.sales_order]
		
		# Planlanmamış siparişleri getir
		unplanned_orders = frappe.get_all(
			"Sales Order",
			fields=[
				"name",
				"customer",
				"custom_end_customer",
				"transaction_date",
				"delivery_date",
				"status"
			],
			filters={
				"docstatus": 1,
				"status": ["not in", ["Stopped", "Closed"]],
				"name": ["not in", planned_so_names] if planned_so_names else []
			}
		)
		
		unplanned_data = []
		
		for so in unplanned_orders:
			try:
				# Bu siparişin detaylarını getir
				so_items = frappe.get_all(
					"Sales Order Item",
					fields=["item_code", "qty", "description"],
					filters={"parent": so.name}
				)
				
				for item in so_items:
					try:
						week_number = get_week_number(so.get("transaction_date"))
						is_urgent = check_urgent_status(so)
						
						unplanned_data.append({
							"hafta": week_number,
							"siparis_no": so.get("name"),
							"bayi": so.get("customer"),
							"musteri": so.get("custom_end_customer", ""),
							"siparis_tarihi": so.get("transaction_date"),
							"adet": item.get("qty", 0),
							"mtul": calculate_mtul({"item_code": item.get("item_code"), "qty": item.get("qty")}),
							"tip": get_item_type(item.get("item_code")),
							"renk": get_item_color(item.get("item_code")),
							"aciklamalar": item.get("description", ""),
							"acil_durum": "ACİL" if is_urgent else "NORMAL",
							"tahmini_bitis": so.get("delivery_date"),
							"durum": "PLANLANMAMIŞ",
							"acil": is_urgent
						})
					except Exception as e:
						frappe.logger().error(f"Item işleme hatası: {item.get('item_code')} - {str(e)}")
						continue
						
			except Exception as e:
				frappe.logger().error(f"SO detay hatası: {so.get('name')} - {str(e)}")
				continue
		
		return unplanned_data
		
	except Exception as e:
		frappe.logger().error(f"get_unplanned_sales_orders hatası: {str(e)}")
		return []

def get_sales_orders_for_production_plan(production_plan):
	"""
	Bir üretim planına ait satış siparişlerini getirir
	"""
	try:
		so_items = frappe.get_all(
			"Production Plan Item",
			fields=["sales_order", "sales_order_item", "item_code", "planned_qty"],
			filters={"parent": production_plan}
		)
		
		sales_orders = []
		
		for item in so_items:
			if item.sales_order:
				try:
					so = frappe.get_doc("Sales Order", item.sales_order)
					so_item = frappe.get_doc("Sales Order Item", item.sales_order_item) if item.sales_order_item else None
					
					sales_orders.append({
						"name": so.name,
						"customer": so.customer,
						"custom_end_customer": so.get("custom_end_customer", ""),
						"transaction_date": so.transaction_date,
						"delivery_date": so_item.delivery_date if so_item else None,
						"item_code": item.item_code,
						"qty": item.planned_qty,
						"description": so_item.description if so_item else ""
					})
				except Exception as e:
					frappe.logger().error(f"SO doc hatası: {item.sales_order} - {str(e)}")
					continue
		
		return sales_orders
		
	except Exception as e:
		frappe.logger().error(f"get_sales_orders_for_production_plan hatası: {str(e)}")
		return []

def get_week_number(date_str):
	"""
	Tarihten hafta numarasını hesaplar
	"""
	if not date_str:
		return 0
	
	try:
		date = frappe.utils.getdate(date_str)
		return date.isocalendar()[1]
	except:
		return 0

def check_urgent_status(sales_order):
	"""
	Acil durumu kontrol eder
	"""
	try:
		# Burada acil durumu belirleyen kriterleri ekleyebilirsiniz
		# Örnek: Teslim tarihi yakın, özel not, vs.
		
		# Şimdilik basit bir kontrol
		if sales_order.get("delivery_date"):
			delivery_date = frappe.utils.getdate(sales_order.get("delivery_date"))
			today = frappe.utils.today()
			days_diff = (delivery_date - frappe.utils.getdate(today)).days
			
			return days_diff <= 7  # 7 gün içinde teslim edilecekse acil
		
		return False
		
	except Exception as e:
		frappe.logger().error(f"check_urgent_status hatası: {str(e)}")
		return False

def calculate_mtul(sales_order):
	"""
	MTÜL hesaplar (şimdilik basit)
	"""
	try:
		# Burada gerçek MTÜL hesaplaması yapılabilir
		return sales_order.get("qty", 0) * 10  # Örnek hesaplama
	except:
		return 0

def get_item_type(item_code):
	"""
	Ürün tipini getirir
	"""
	if not item_code:
		return ""
	
	try:
		item = frappe.get_doc("Item", item_code)
		return item.get("custom_item_type", "") or item.get("item_group", "")
	except:
		return ""

def get_item_color(item_code):
	"""
	Ürün rengini getirir
	"""
	if not item_code:
		return ""
	
	try:
		item = frappe.get_doc("Item", item_code)
		return item.get("custom_color", "") or ""
	except:
		return ""

def get_turkish_status(status):
	"""
	Durumu Türkçe'ye çevirir
	"""
	status_map = {
		"Draft": "Taslak",
		"Submitted": "Onaylandı",
		"Not Started": "Başlamadı",
		"In Progress": "Devam Ediyor",
		"Completed": "Tamamlandı",
		"Stopped": "Durduruldu",
		"Closed": "Kapatıldı"
	}
	
	return status_map.get(status, status)

def calculate_summary_data(planned_data, unplanned_data):
	"""
	Özet verileri hesaplar
	"""
	try:
		planned_count = len(planned_data)
		unplanned_count = len(unplanned_data)
		total_count = planned_count + unplanned_count
		urgent_count = len([item for item in planned_data + unplanned_data if item.get("acil")])
		
		return {
			"planlanan": planned_count,
			"planlanmamis": unplanned_count,
			"toplam": total_count,
			"acil": urgent_count
		}
	except Exception as e:
		frappe.logger().error(f"calculate_summary_data hatası: {str(e)}")
		return {
			"planlanan": 0,
			"planlanmamis": 0,
			"toplam": 0,
			"acil": 0
		}

@frappe.whitelist()
def get_bom_count_and_status():
	"""
	Tüm BOM'ların sayısını ve statülerini döndürür.
	"""
	try:
		# BOM'ları statü bazında grupla
		bom_stats = frappe.db.sql("""
			SELECT 
				docstatus,
				is_active,
				is_default,
				COUNT(*) as count
			FROM `tabBOM`
			GROUP BY docstatus, is_active, is_default
		""", as_dict=True)
		
		# Sonuçları düzenle
		result = {
			"total_boms": 0,
			"active_boms": 0,
			"inactive_boms": 0,
			"submitted_boms": 0,
			"draft_boms": 0,
			"cancelled_boms": 0,
			"default_boms": 0,
			"non_default_boms": 0,
			"status_breakdown": []
		}
		
		for stat in bom_stats:
			count = stat.count
			result["total_boms"] += count
			
			# Aktif/Pasif durumu
			if stat.is_active:
				result["active_boms"] += count
			else:
				result["inactive_boms"] += count
			
			# Docstatus durumu
			if stat.docstatus == 0:
				result["draft_boms"] += count
			elif stat.docstatus == 1:
				result["submitted_boms"] += count
			elif stat.docstatus == 2:
				result["cancelled_boms"] += count
			
			# Default durumu
			if stat.is_default:
				result["default_boms"] += count
			else:
				result["non_default_boms"] += count
			
			# Detaylı statü breakdown
			status_key = f"docstatus_{stat.docstatus}_active_{stat.is_active}_default_{stat.is_default}"
			result["status_breakdown"].append({
				"docstatus": stat.docstatus,
				"is_active": stat.is_active,
				"is_default": stat.is_default,
				"count": count,
				"status_description": get_bom_status_description(stat.docstatus, stat.is_active, stat.is_default)
			})
		
		# En çok kullanılan BOM'ları da ekle
		most_used_boms = frappe.db.sql("""
			SELECT 
				bom.name,
				bom.item,
				bom.item_name,
				bom.docstatus,
				bom.is_active,
				bom.is_default,
				COUNT(wo.name) as usage_count
			FROM `tabBOM` bom
			LEFT JOIN `tabWork Order` wo ON bom.name = wo.bom_no
			GROUP BY bom.name
			ORDER BY usage_count DESC
			LIMIT 10
		""", as_dict=True)
		
		result["most_used_boms"] = most_used_boms
		
		return result
		
	except Exception as e:
		frappe.log_error(f"BOM count and status error: {str(e)}")
		return {
			"error": str(e),
			"total_boms": 0,
			"active_boms": 0,
			"inactive_boms": 0,
			"submitted_boms": 0,
			"draft_boms": 0,
			"cancelled_boms": 0,
			"default_boms": 0,
			"non_default_boms": 0,
			"status_breakdown": [],
			"most_used_boms": []
		}

def get_bom_status_description(docstatus, is_active, is_default):
	"""
	BOM statü açıklamasını döndürür
	"""
	status_parts = []
	
	if docstatus == 0:
		status_parts.append("Taslak")
	elif docstatus == 1:
		status_parts.append("Onaylı")
	elif docstatus == 2:
		status_parts.append("İptal")
	
	if is_active:
		status_parts.append("Aktif")
	else:
		status_parts.append("Pasif")
	
	if is_default:
		status_parts.append("Varsayılan")
	
	return " - ".join(status_parts)

@frappe.whitelist()
def get_bom_details_by_item(item_code=None):
	"""
	Belirli bir item için BOM detaylarını döndürür
	"""
	try:
		filters = {}
		if item_code:
			filters["item"] = item_code
		
		boms = frappe.get_all(
			"BOM",
			filters=filters,
			fields=[
				"name",
				"item",
				"item_name", 
				"docstatus",
				"is_active",
				"is_default",
				"quantity",
				"uom",
				"creation",
				"modified"
			],
			order_by="creation desc"
		)
		
		for bom in boms:
			# BOM item sayısını ekle
			bom_item_count = frappe.db.count("BOM Item", {"parent": bom.name})
			bom["item_count"] = bom_item_count
			
			# Kullanım sayısını ekle
			usage_count = frappe.db.count("Work Order", {"bom_no": bom.name})
			bom["usage_count"] = usage_count
			
			# Statü açıklamasını ekle
			bom["status_description"] = get_bom_status_description(
				bom.docstatus, bom.is_active, bom.is_default
			)
		
		return {
			"boms": boms,
			"total_count": len(boms)
		}
		
	except Exception as e:
		frappe.log_error(f"BOM details error: {str(e)}")
		return {
			"error": str(e),
			"boms": [],
			"total_count": 0
		}