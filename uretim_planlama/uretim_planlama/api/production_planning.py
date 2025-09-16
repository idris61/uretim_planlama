# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
Üretim Planlama API Modülü
Production Planning API Module

Sadece gerçekten kullanılan fonksiyonları içerir.
"""

from calendar import monthrange
from datetime import timedelta

import frappe
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


@frappe.whitelist()
def get_weekly_production_schedule(
    year=None, month=None, week_start=None, week_end=None, workstation=None, status=None
):
    """Haftalık üretim takvimi verisi döner"""
    try:
        print(f"DEBUG: get_weekly_production_schedule çağrıldı - week_start: {week_start}, week_end: {week_end}")
        
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

        print(f"DEBUG: Tarih aralığı - start_date: {start_date}, end_date: {end_date}")

        workstation_filters = {"name": workstation} if workstation else {}
        workstations = frappe.get_all(
            "Workstation", filters=workstation_filters, fields=["name", "holiday_list"]
        )
        
        print(f"DEBUG: Workstations bulundu: {len(workstations)} adet")

        # Çalışma saatlerini toplu çek ve hazırla (N+1 azaltma)
        ws_names = [ws["name"] for ws in workstations]
        ws_work_hours_map = {}
        if ws_names:
            ws_work_hours_rows = []
            # DocType isimleri sürüme göre değişebildiği için iki olası adı dene; yoksa fallback
            try:
                ws_work_hours_rows = frappe.get_all(
                    "Workstation Working Hour",
                    filters={"parent": ["in", ws_names], "enabled": 1},
                    fields=["parent", "start_time", "end_time"],
                )
            except Exception:
                try:
                    ws_work_hours_rows = frappe.get_all(
                        "Workstation Working Hours",
                        filters={"parent": ["in", ws_names], "enabled": 1},
                        fields=["parent", "start_time", "end_time"],
                    )
                except Exception:
                    ws_work_hours_rows = []
            if ws_work_hours_rows:
                for row in ws_work_hours_rows:
                    ws_work_hours_map.setdefault(row["parent"], []).append(
                        {"start_time": row["start_time"], "end_time": row["end_time"]}
                    )
            else:
                # Fallback: DocType bulunamazsa Workstation doc üzerinden child tabloyu oku
                for ws in workstations:
                    try:
                        ws_doc = frappe.get_doc("Workstation", ws.name)
                        for row in getattr(ws_doc, "working_hours", []):
                            if getattr(row, "enabled", 1):
                                ws_work_hours_map.setdefault(ws.name, []).append(
                                    {"start_time": row.start_time, "end_time": row.end_time}
                                )
                    except Exception:
                        continue

        # Tüm operasyonları topluca çek - tarih aralığına çakışma (overlap) mantığı
        # (planned_start_time <= end_date) AND (planned_end_time >= start_date)
        # Eğer planned_end_time yoksa start_time aralığına göre değerlendir
        overlapping_ops = frappe.get_all(
            "Work Order Operation",
            filters={
                "planned_start_time": ["<=", f"{end_date!s} 23:59:59"],
                "planned_end_time": [">=", str(start_date)],
                **({"workstation": workstation} if workstation else {}),
                **({"status": status} if status else {}),
            },
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

        # Ek olarak, planned_end_time boş olan fakat start_time aralığa düşenleri de dahil et
        start_range_ops = frappe.get_all(
            "Work Order Operation",
            filters={
                "planned_end_time": ["in", [None, ""]],
                "planned_start_time": [
                    "between",
                    [str(start_date), f"{end_date!s} 23:59:59"],
                ],
                **({"workstation": workstation} if workstation else {}),
                **({"status": status} if status else {}),
            },
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

        all_operations = overlapping_ops + [
            op for op in start_range_ops if op["name"] not in {o["name"] for o in overlapping_ops}
        ]
        
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
                    "production_plan",
                ],
            )
        }
        
        # Tüm production plan isimlerini topla
        production_plan_names = list(
            set([wo.production_plan for wo in work_orders.values() if wo.production_plan])
        )
        # Tüm production plan'ları topluca çek (workstation bilgisi için)
        production_plans = {}
        if production_plan_names:
            try:
                for pp in frappe.get_all(
                    "Production Plan",
                    filters={"name": ["in", production_plan_names]},
                    fields=["name", "workstation"],
                ):
                    production_plans[pp.name] = pp
            except Exception:
                # Bazı kurulumlarda 'workstation' alanı yok; yalnızca name çek
                for pp in frappe.get_all(
                    "Production Plan",
                    filters={"name": ["in", production_plan_names]},
                    fields=["name"],
                ):
                    production_plans[pp.name] = pp
        
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

        # Operasyonları istasyona göre grupla (workstation boşsa Production Plan'dan türet)
        ops_by_ws = {}
        for op in all_operations:
            wsn = op.get("workstation")
            if not wsn:
                wo = work_orders.get(op["work_order"], {})
                pp_name = wo.get("production_plan") if wo else None
                if pp_name:
                    pp = production_plans.get(pp_name)
                    if pp and pp.get("workstation"):
                        wsn = pp.get("workstation")
            if not wsn:
                # İstasyon yine yoksa bu operasyonu şimdilik atla (kapasite hesaplanamaz)
                continue
            ops_by_ws.setdefault(wsn, []).append(op)

        schedule = []
        for ws in workstations:
            ws_ops = ops_by_ws.get(ws.name, [])
            # Çalışma saatleri map'ten al
            work_hours = ws_work_hours_map.get(ws.name, [])
            daily_work_minutes = {}
            from datetime import datetime

            if work_hours:
                for i in range(7):
                    total = 0
                    for wh in work_hours:
                        s = (
                            datetime.strptime(str(wh["start_time"]), "%H:%M:%S")
                            if ":" in str(wh["start_time"]) else datetime.strptime(str(wh["start_time"]), "%H:%M")
                        )
                        e = (
                            datetime.strptime(str(wh["end_time"]), "%H:%M:%S")
                            if ":" in str(wh["end_time"]) else datetime.strptime(str(wh["end_time"]), "%H:%M")
                        )
                        diff = (e - s).seconds // 60
                        total += diff
                    daily_work_minutes[i] = total
            else:
                for i in range(7):
                    daily_work_minutes[i] = 0
        
            day_schedule = {}
            ops_in_this_week = set()
            total_hours = 0
            total_operations = 0
            daily_summary = {}
            
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
                
                start_dt = get_datetime(op["planned_start_time"]) if op["planned_start_time"] else None
                end_dt = get_datetime(op["planned_end_time"]) if op["planned_end_time"] else None
                time_in_mins = int(op.get("time_in_mins") or 0)
                if time_in_mins == 0 and start_dt and end_dt:
                    time_in_mins = int((end_dt - start_dt).total_seconds() // 60)
                
                total_hours += time_in_mins / 60
                total_operations += 1
                
                if start_dt:
                    weekday_name = day_name_tr[start_dt.strftime("%A")]
                    daily_summary.setdefault(
                        weekday_name, {"planned_minutes": 0, "jobs": 0}
                    )
                    daily_summary[weekday_name]["planned_minutes"] += time_in_mins
                    daily_summary[weekday_name]["jobs"] += 1
                
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
                        "start_time": start_dt.strftime("%Y-%m-%d %H:%M") if start_dt else "",
                        "end_time": end_dt.strftime("%Y-%m-%d %H:%M") if end_dt else "",
                        "expected_start_date": op["planned_start_time"],
                        "expected_end_date": op["planned_end_time"],
                        "actual_start_date": op["actual_start_time"],
                        "actual_end_date": op["actual_end_time"],
                        "total_time_in_mins": time_in_mins,
                        "time": f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}" if (start_dt and end_dt) else "",
                        "employee": "",
                        "duration": time_in_mins,
                        "op_status": op_status,
                    }
                )
        
            # Günlük özetler
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
        
    except Exception as e:
        print(f"DEBUG: get_weekly_production_schedule hatası: {str(e)}")
        frappe.log_error(f"get_weekly_production_schedule hatası: {str(e)}")
        return {
            "workstations": [],
            "holidays": [],
            "start_date": "",
            "end_date": "",
            "days": [],
        }


def get_color_for_sales_order(sales_order):
    """Sales order için renk döner"""
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
    """Hafta tarihlerini döner"""
    # Pazartesi'den başlat
    monday = start_date - timedelta(days=start_date.weekday())
    # Haftanın günlerini oluştur
    return [monday + timedelta(days=i) for i in range(7)]


@frappe.whitelist()
def debug_ops_summary(week_start=None, week_end=None):
    """Belirtilen aralıkta operasyon ve job card özetini döner (teşhis amaçlı)."""
    try:
        if not week_start or not week_end:
            return {"error": "week_start ve week_end zorunlu"}

        start_date = getdate(week_start)
        end_date = getdate(week_end)

        # 1) planned_start_time BETWEEN
        ops_between = frappe.get_all(
            "Work Order Operation",
            filters={
                "planned_start_time": [
                    "between",
                    [str(start_date), f"{end_date!s} 23:59:59"],
                ]
            },
            fields=["name", "parent as work_order", "operation", "workstation", "planned_start_time", "planned_end_time"],
            limit_page_length=5,
        )

        # 2) Overlap filtresi
        ops_overlap = frappe.get_all(
            "Work Order Operation",
            filters={
                "planned_start_time": ["<=", f"{end_date!s} 23:59:59"],
                "planned_end_time": [">=", str(start_date)],
            },
            fields=["name"],
        )

        # 3) planned_end_time boş ve start BETWEEN
        ops_no_end = frappe.get_all(
            "Work Order Operation",
            filters={
                "planned_end_time": ["in", [None, ""]],
                "planned_start_time": [
                    "between",
                    [str(start_date), f"{end_date!s} 23:59:59"],
                ],
            },
            fields=["name"],
        )

        # 4) Job Card sayısı (work_order/planned alanları yoksa tarih filtrelemesi zayıf olabilir)
        job_cards = frappe.get_all(
            "Job Card",
            filters={
                "creation": ["between", [str(start_date), f"{end_date!s} 23:59:59"]],
            },
            fields=["name", "work_order", "operation", "status"],
            limit_page_length=5,
        )

        return {
            "ops_between_count": frappe.db.count(
                "Work Order Operation",
                {"planned_start_time": ["between", [str(start_date), f"{end_date!s} 23:59:59"]]},
            ),
            "ops_overlap_count": len(ops_overlap),
            "ops_no_end_count": len(ops_no_end),
            "ops_between_samples": ops_between,
            "job_card_samples": job_cards,
        }
    except Exception as e:
        frappe.log_error(f"debug_ops_summary hatası: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_production_planning_data(filters=None):
    """Üretim planlama paneli için veri getirir"""
    try:
        if filters:
            filters = json.loads(filters) if isinstance(filters, str) else filters
        else:
            filters = {}

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
        
        return result
        
    except Exception as e:
        import traceback
        error_msg = f"Üretim planlama verisi getirme hatası: {str(e)}\n{traceback.format_exc()}"
        frappe.log_error(error_msg)
        frappe.logger().error(f"API HATASI: {error_msg}")
        return {"error": str(e)}


def get_planned_production_data(filters):
    """Planlanan üretim planları ve satış siparişlerini getirir"""
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
        
        planned_data = []
        
        for pp in production_plans:
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
    """Planlanmamış satış siparişlerini getirir"""
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
    """Bir üretim planına ait satış siparişlerini getirir"""
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
    """Tarihten hafta numarasını hesaplar"""
    if not date_str:
        return 0
    
    try:
        date = frappe.utils.getdate(date_str)
        return date.isocalendar()[1]
    except:
        return 0


def check_urgent_status(sales_order):
    """Acil durumu kontrol eder"""
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
    """MTÜL hesaplar (şimdilik basit)"""
    try:
        # Burada gerçek MTÜL hesaplaması yapılabilir
        return sales_order.get("qty", 0) * 10  # Örnek hesaplama
    except:
        return 0


def get_item_type(item_code):
    """Ürün tipini getirir"""
    if not item_code:
        return ""
    
    try:
        item = frappe.get_doc("Item", item_code)
        return item.get("custom_item_type", "") or item.get("item_group", "")
    except:
        return ""


def get_item_color(item_code):
    """Ürün rengini getirir"""
    if not item_code:
        return ""
    
    try:
        item = frappe.get_doc("Item", item_code)
        return item.get("custom_color", "") or ""
    except:
        return ""


def get_turkish_status(status):
    """Durumu Türkçe'ye çevirir"""
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
    """Özet verileri hesaplar"""
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
