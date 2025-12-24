# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
Calendar API Functions
Takvim ile ilgili API fonksiyonları
"""

import frappe


@frappe.whitelist()
def get_holidays_for_calendar(start: str, end: str) -> dict[str, str]:
    """
    Belirtilen tarih aralığındaki tatilleri döndürür.
    
    Args:
        start: Başlangıç tarihi (YYYY-MM-DD formatında)
        end: Bitiş tarihi (YYYY-MM-DD formatında)
        
    Returns:
        Tarih ve açıklama eşleştirmesi: {"2025-01-01": "Yılbaşı", ...}
    """
    # Default company'yi al
    company = frappe.defaults.get_defaults().get("company")
    if not company:
        companies = frappe.get_all("Company", limit=1, pluck="name")
        company = companies[0] if companies else None
    
    if not company:
        return {}
    
    # Company'nin default holiday list'ini al
    holiday_list = frappe.get_cached_value("Company", company, "default_holiday_list")
    
    if not holiday_list:
        return {}
    
    # Belirtilen tarih aralığındaki tatilleri getir
    holidays = frappe.get_all(
        "Holiday",
        filters={
            "parent": holiday_list,
            "holiday_date": ["between", [start, end]]
        },
        fields=["holiday_date", "description"],
        order_by="holiday_date"
    )
    
    # Dictionary formatına çevir: {date: description}
    holidays_dict = {}
    for holiday in holidays:
        date_str = str(holiday.holiday_date)
        # HTML tag'lerini temizle
        description = frappe.utils.strip_html(holiday.description or "").strip()
        holidays_dict[date_str] = description or "Tatil"
    
    return holidays_dict


@frappe.whitelist()
def get_work_orders_for_calendar(start: str, end: str, include_draft: bool = False) -> list[dict]:
    """
    Belirtilen tarih aralığındaki iş emirlerini takvim için döndürür.
    
    Args:
        start: Başlangıç tarihi (YYYY-MM-DD formatında veya ISO format)
        end: Bitiş tarihi (YYYY-MM-DD formatında veya ISO format)
        include_draft: Taslak iş emirlerini dahil et (varsayılan: False)
        
    Returns:
        İş emirleri listesi, her biri takvim event formatında
    """
    from frappe.utils import getdate
    from datetime import date, datetime
    
    # Tarih stringlerini temizle (ISO formatından sadece tarih kısmını al)
    start_date = start.split('T')[0] if 'T' in start else start
    end_date = end.split('T')[0] if 'T' in end else end
    
    # Durum filtreleme
    status_list = ["Not Started", "In Process", "Completed"]
    if include_draft:
        status_list.append("Draft")
    
    # SQL sorgusu ile overlap mantığı kullanarak filtreleme
    # Bir iş emri, eğer planned_start_date <= end VE planned_end_date >= start ise aralıkta
    # veya tarihi olmayan taslak iş emirleri
    placeholders = ','.join(['%s'] * len(status_list))
    sql_query = f"""
        SELECT 
            wo.name,
            wo.status,
            wo.production_item,
            wo.sales_order,
            wo.planned_start_date,
            wo.planned_end_date,
            wo.qty,
            wo.produced_qty
        FROM `tabWork Order` wo
        WHERE wo.status IN ({placeholders})
        AND (
            (wo.planned_start_date IS NOT NULL 
             AND DATE(wo.planned_start_date) <= %s
             AND (wo.planned_end_date IS NULL OR DATE(wo.planned_end_date) >= %s))
            OR (wo.planned_end_date IS NOT NULL 
                AND DATE(wo.planned_end_date) >= %s
                AND (wo.planned_start_date IS NULL OR DATE(wo.planned_start_date) <= %s))
            OR (wo.status = 'Draft' AND wo.planned_start_date IS NULL AND wo.planned_end_date IS NULL)
        )
        ORDER BY wo.planned_start_date ASC
    """
    
    work_orders = frappe.db.sql(
        sql_query,
        status_list + [end_date, start_date, start_date, end_date],
        as_dict=True
    )
    
    # Sales Order bilgilerini toplu olarak al
    sales_orders = {}
    if work_orders:
        so_names = list(set([wo.sales_order for wo in work_orders if wo.sales_order]))
        if so_names:
            sales_order_data = frappe.get_all(
                "Sales Order",
                filters={"name": ["in", so_names]},
                fields=["name", "customer", "custom_end_customer"]
            )
            sales_orders = {so.name: so for so in sales_order_data}
    
    # Takvim formatına çevir
    calendar_events = []
    today = date.today()
    
    for wo in work_orders:
        # Tarihleri al ve formatla
        start_date = wo.planned_start_date
        end_date = wo.planned_end_date
        
        # Tarih yoksa ve taslak değilse atla
        if not start_date and not end_date:
            if wo.status != "Draft":
                continue
            # Taslak için bugünün tarihini kullan
            start_date = datetime.combine(today, datetime.min.time())
            end_date = datetime.combine(today, datetime.min.time())
        
        # Başlangıç ve bitiş tarihlerini ayarla
        if not start_date:
            start_date = end_date
        if not end_date:
            end_date = start_date
        
        # Datetime ise sadece tarih kısmını al (YYYY-MM-DD formatı)
        if isinstance(start_date, datetime):
            start_str = start_date.date().isoformat()
        elif isinstance(start_date, date):
            start_str = start_date.isoformat()
        else:
            start_str = str(start_date).split()[0]  # İlk kısmı al (tarih)
        
        if isinstance(end_date, datetime):
            end_str = end_date.date().isoformat()
        elif isinstance(end_date, date):
            end_str = end_date.isoformat()
        else:
            end_str = str(end_date).split()[0]  # İlk kısmı al (tarih)
        
        if not start_str or not end_str:
            continue
        
        # Sales Order bilgilerini al
        so_info = sales_orders.get(wo.sales_order, {}) if wo.sales_order else {}
        customer = so_info.get("customer", "")
        custom_end_customer = so_info.get("custom_end_customer", "")
        
        # Başlık oluştur - Production Item veya Work Order adı
        title = wo.production_item or wo.name
        
        calendar_events.append({
            "id": wo.name,
            "title": title,
            "start": start_str,
            "end": end_str,
            "status": wo.status or "",
            "sales_order": wo.sales_order or "",
            "customer": customer,
            "custom_end_customer": custom_end_customer,
            "production_item": wo.production_item or "",
            "qty": wo.qty or 0,
            "produced_qty": wo.produced_qty or 0
        })
    
    return calendar_events


@frappe.whitelist()
def get_work_order_detail(work_order_id: str) -> dict:
    """
    İş emri detaylarını getirir (operasyonlar dahil).
    
    Args:
        work_order_id: İş emri adı
        
    Returns:
        İş emri detayları ve operasyonlarını içeren dict
    """
    try:
        # Work Order'ı getir
        wo = frappe.get_doc("Work Order", work_order_id)
        
        # Temel bilgileri hazırla
        detail = {
            "name": wo.name,
            "status": wo.status,
            "production_item": wo.production_item,
            "sales_order": wo.sales_order,
            "bom_no": wo.bom_no,
            "production_plan": wo.production_plan if hasattr(wo, 'production_plan') else None,
            "qty": wo.qty,
            "produced_qty": wo.produced_qty,
            "planned_start_date": str(wo.planned_start_date) if wo.planned_start_date else None,
            "planned_end_date": str(wo.planned_end_date) if wo.planned_end_date else None,
            "actual_start_date": str(wo.actual_start_date) if wo.actual_start_date else None,
            "actual_end_date": str(wo.actual_end_date) if wo.actual_end_date else None,
        }
        
        # Toplam fiili süreyi hesapla (Job Card'lardan)
        total_time = 0
        job_cards = frappe.get_all(
            "Job Card",
            filters={"work_order": work_order_id},
            fields=["total_time_in_mins"]
        )
        for jc in job_cards:
            if jc.total_time_in_mins:
                total_time += float(jc.total_time_in_mins or 0)
        detail["total_time_in_mins"] = total_time if total_time > 0 else None
        
        # Operasyonları getir
        operations = []
        work_order_operations = frappe.get_all(
            "Work Order Operation",
            filters={"parent": work_order_id},
            fields=[
                "name",
                "operation",
                "status",
                "completed_qty",
                "planned_start_time",
                "planned_end_time",
                "actual_start_time",
                "actual_end_time",
                "workstation"
            ],
            order_by="idx"
        )
        
        for op in work_order_operations:
            operations.append({
                "name": op.name,
                "operation": op.operation,
                "status": op.status,
                "completed_qty": op.completed_qty,
                "planned_start_time": str(op.planned_start_time) if op.planned_start_time else None,
                "planned_end_time": str(op.planned_end_time) if op.planned_end_time else None,
                "actual_start_time": str(op.actual_start_time) if op.actual_start_time else None,
                "actual_end_time": str(op.actual_end_time) if op.actual_end_time else None,
                "workstation": op.workstation
            })
        
        detail["operations"] = operations
        
        return detail
        
    except frappe.DoesNotExistError:
        frappe.throw(f"İş Emri bulunamadı: {work_order_id}")
    except Exception as e:
        frappe.log_error(f"get_work_order_detail hatası: {str(e)}", "Calendar API")
        frappe.throw(f"İş emri detayları getirilirken hata oluştu: {str(e)}")

