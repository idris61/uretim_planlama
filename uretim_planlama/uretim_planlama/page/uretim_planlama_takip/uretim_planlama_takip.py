# -*- coding: utf-8 -*-
# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
Üretim Planlama Takip Paneli - Backend API
ERPNext v15 + Frappe

Bu dosya üretim planlama takip panelinin backend API fonksiyonlarını içerir.
Tamamen bağımsız çalışır, api.py ile karışmaz.
OPTIMIZE EDİLMİŞ VERSİYON - Modern Python patterns + Enhanced Performance
"""

# Standard library imports
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

# Frappe imports
import frappe
from frappe import _
from frappe.utils import get_datetime, getdate, add_days


# Constants - Performance ve consistency için
CONSTANTS = {
    'STATUS_MAP': {
        "In Process": "Devam ediyor",
        "Completed": "Tamamlandı", 
        "Not Started": "Açık",
        "Açık": "Açık",
        "Devam ediyor": "Devam ediyor",
        "Tamamlandı": "Tamamlandı",
        "İptal Edildi": "İptal Edildi",
        "Stopped": "Durduruldu",
        "Closed": "Kapatıldı"
    },
    'DEFAULT_LIMIT': 0,  # 0 = sınırsız
    'CACHE_DURATION': 30000,  # 30 saniye
    'MAX_RETRIES': 3,
    'DEFAULT_MTUL_CAM': 1.745,
    'DEFAULT_MTUL_PVC': 11.35,
    'MAX_QUERY_LIMIT': 0  # 0 = sınırsız
}

def validate_filters(filters: Dict) -> Dict:
    """Filter validation ve sanitization - Enhanced version"""
    validated = {}
    if filters.get("limit"):
        validated["limit"] = int(filters["limit"]) if int(filters["limit"]) > 0 else 0
    else:
        validated["limit"] = CONSTANTS['DEFAULT_LIMIT']
    
    # String filtreleri sanitize et - Enhanced filter list
    string_filters = ['opti_no', 'siparis_no', 'bayi', 'musteri', 'seri', 'renk', 'tip', 'durum']
    for filter_name in string_filters:
        if filters.get(filter_name):
            validated[filter_name] = str(filters[filter_name]).strip()
    
    # Boolean filtreleri
    if 'showCompleted' in filters:
        validated['showCompleted'] = bool(filters['showCompleted'])
    else:
        validated['showCompleted'] = True
    
    return validated

def apply_common_filters(where_conditions: List[str], params: List, filters: Dict, table_prefix: str = "so") -> None:
    """Ortak filter logic'i - DRY prensibi - Enhanced version"""
    
    if filters.get("opti_no"):
        where_conditions.append("pp.custom_opti_no LIKE %s")
        params.append(f"%{filters['opti_no']}%")
    
    if filters.get("siparis_no"):
        where_conditions.append(f"{table_prefix}.name LIKE %s")
        params.append(f"%{filters['siparis_no']}%")
    
    if filters.get("bayi"):
        where_conditions.append(f"{table_prefix}.customer LIKE %s")
        params.append(f"%{filters['bayi']}%")
    
    if filters.get("musteri"):
        where_conditions.append(f"{table_prefix}.custom_end_customer LIKE %s")
        params.append(f"%{filters['musteri']}%")
    
    if filters.get("seri"):
        where_conditions.append("i.custom_serial LIKE %s")
        params.append(f"%{filters['seri']}%")
    
    if filters.get("renk"):
        where_conditions.append("i.custom_color LIKE %s")
        params.append(f"%{filters['renk']}%")

def apply_tip_filter(where_conditions: List[str], filters: Dict) -> None:
    """PLANLANAN ÜRETİMLER için Cam/PVC/Karışık filtresi - Enhanced version"""
    tip_filter = filters.get("tip")
    if not tip_filter or tip_filter == "tumu":
        return
        
    if tip_filter == "pvc":
        where_conditions.append("(i.item_group = 'PVC' OR i.custom_stok_türü = 'PVC')")
    elif tip_filter == "cam":
        where_conditions.append("(i.item_group = 'Camlar' OR i.custom_stok_türü = 'Camlar')")
    elif tip_filter == "karisik":
        where_conditions.append("""
            pp.name IN (
                SELECT DISTINCT ppi1.parent
                FROM `tabProduction Plan Item` ppi1
                INNER JOIN `tabItem` i1 ON ppi1.item_code = i1.name
                WHERE (i1.item_group = 'PVC' OR i1.custom_stok_türü = 'PVC')
            )
            AND pp.name IN (
                SELECT DISTINCT ppi2.parent
                FROM `tabProduction Plan Item` ppi2
                INNER JOIN `tabItem` i2 ON ppi2.item_code = i2.name
                WHERE (i2.item_group = 'Camlar' OR i2.custom_stok_türü = 'Camlar')
            )
        """)

@frappe.whitelist()
def get_production_planning_data(filters: Optional[Union[str, Dict]] = None) -> Dict[str, Any]:
    """
    Üretim planlama verilerini getirir.
    Sadece planlanan siparişler için optimize edilmiş.
    Modern validation ve error handling ile.
    """
    try:
        # Modern parameter handling
        filters = json.loads(filters) if isinstance(filters, str) else (filters or {})
        filters = validate_filters(filters)
        
        # Optimize edilmiş veri çekme
        planned_data = get_optimized_planned_data(filters)
        
        return {
            "success": True,
            "planned": planned_data,
            "total_planned": len(planned_data),
            "filters": filters
        }
        
    except Exception as e:
        frappe.log_error(f"Üretim Takip Paneli Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return {
            "success": False,
            "planned": [],
            "error": str(e),
            "total_planned": 0
        }

def get_optimized_planned_data(filters: Dict) -> List[Dict]:
    """
    Optimize edilmiş planlanan veri çekme fonksiyonu - Enhanced version
    """
    try:
        limit = filters.get("limit", CONSTANTS['DEFAULT_LIMIT'])
        
        # Optimize edilmiş ana sorgu - Enhanced performance
        planned_query = """
            SELECT 
                pp.custom_opti_no as opti_no,
                pp.status as plan_status,
                ppi.sales_order,
                ppi.item_code,
                ppi.planned_qty as adet,
                so.customer as bayi,
                so.custom_end_customer as musteri,
                so.transaction_date as siparis_tarihi,
                so.delivery_date as bitis_tarihi,
                i.custom_color as renk,
                WEEK(so.transaction_date) as hafta,
                COALESCE(so.custom_acil_durum, 0) as acil,
                i.item_group as urun_grubu,
                i.custom_serial as seri,
                pp.creation as planlanan_baslangic_tarihi,
                ppi.planned_end_date as planned_end_date,
                CASE 
                    WHEN i.item_group = 'Camlar' OR i.custom_stok_türü = 'Camlar'
                    THEN ppi.planned_qty * COALESCE(ppi.custom_mtul_per_piece, %s)
                    ELSE ppi.planned_qty * COALESCE(i.custom_total_main_profiles_mtul, 0)
                END as toplam_mtul_m2,
                CASE 
                    WHEN i.item_group = 'PVC' THEN ppi.planned_qty
                    ELSE 0
                END as pvc_count,
                CASE 
                    WHEN i.item_group = 'Camlar' OR i.custom_stok_türü = 'Camlar'
                    THEN ppi.planned_qty
                    ELSE 0
                END as cam_count,
                so.custom_remarks as siparis_aciklama
            FROM `tabProduction Plan` pp
            INNER JOIN `tabProduction Plan Item` ppi ON pp.name = ppi.parent
            INNER JOIN `tabSales Order` so ON ppi.sales_order = so.name
            INNER JOIN `tabItem` i ON ppi.item_code = i.name
            WHERE pp.docstatus = 1 
            AND pp.status != 'Closed'
            AND ppi.planned_qty > 0
            AND i.item_group != 'All Item Groups'
        """
        
        # Filtreleri ekle - Enhanced filter system
        where_conditions = []
        params = [CONSTANTS['DEFAULT_MTUL_CAM']]  # MTÜL parametresi
        
        # Ortak filtreleri uygula
        apply_common_filters(where_conditions, params, filters)
        
        # Tip filtresi uygula
        apply_tip_filter(where_conditions, filters)
        
        # Durum filtresi
        durum_filter = filters.get('durum', 'tumu')
        if durum_filter == 'tamamlandi':
            where_conditions.append("pp.status = 'Completed'")
        elif durum_filter == 'devam_ediyor':
            where_conditions.append("pp.status = 'In Process'")
        elif durum_filter == 'planlanmamis':
            where_conditions.append("pp.status = 'Not Started'")
        
        # Tamamlananları göster/gizle
        if not filters.get('showCompleted', True):
            where_conditions.append("pp.status != 'Completed'")
        
        # WHERE koşullarını ekle
        if where_conditions:
            planned_query += " AND " + " AND ".join(where_conditions)
        
        # Optimize edilmiş sıralama ve limit
        planned_query += " ORDER BY so.delivery_date ASC, pp.custom_opti_no"
        if limit > 0:
            planned_query += f" LIMIT {limit}"
        
        # Sorguyu çalıştır
        planned_data = frappe.db.sql(planned_query, params, as_dict=True)
        
        # Verileri formatla
        return format_planned_data_for_takip(planned_data)
        
    except Exception as e:
        frappe.log_error(f"get_optimized_planned_data hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return []

def format_planned_data_for_takip(planned_data: List[Dict]) -> List[Dict]:
    """
    Planlanan verileri takip paneli için formatla - Enhanced version
    """
    if not planned_data:
        return []
    
    # Veri formatlaması ve ek işlemler
    for item in planned_data:
        # Tarih formatlaması - Enhanced date handling
        if item.get('siparis_tarihi'):
            item['siparis_tarihi'] = format_date_for_takip(item['siparis_tarihi'])
        if item.get('bitis_tarihi'):
            item['bitis_tarihi'] = format_date_for_takip(item['bitis_tarihi'])
        if item.get('planlanan_baslangic_tarihi'):
            item['planlanan_baslangic_tarihi'] = format_date_for_takip(item['planlanan_baslangic_tarihi'])
        if item.get('planned_end_date'):
            item['planned_end_date'] = format_date_for_takip(item['planned_end_date'])
        else:
            # planned_end_date yoksa None olarak ayarla
            item['planned_end_date'] = None
        
        # Boolean değerleri
        item['acil'] = bool(item.get('acil', 0))
        
        # Status badge - Enhanced
        item['status_badge'] = get_status_badge_for_takip(item.get('plan_status', 'Not Started'))
        
        # MTÜL formatlaması
        item['toplam_mtul_m2'] = round(float(item.get('toplam_mtul_m2', 0) or 0), 2)
    
    return planned_data


@frappe.whitelist()
def get_opti_details_for_takip(opti_no: str) -> Dict[str, Any]:
    """
    Opti numarasına göre detaylı bilgileri getirir.
    Modern ve optimize edilmiş - N+1 Query problemi çözüldü.
    """
    try:
        # Opti numarasına göre üretim planlarını getir
        production_plans = frappe.get_all(
            "Production Plan",
            filters={
                "custom_opti_no": opti_no,
                "docstatus": 1
            },
            fields=[
                "name",
                "custom_opti_no",
                "status",
                "creation",
                "modified"
            ],
            order_by="creation desc"
        )
        
        if not production_plans:
            return {"error": "Opti bulunamadı"}
        
        # En son üretim planını al
        latest_plan = production_plans[0]
        
        # Bu üretim planındaki tüm siparişleri getir
        plan_items = frappe.get_all(
            "Production Plan Item",
            filters={
                "parent": latest_plan.name,
                "planned_qty": [">", 0]
            },
            fields=[
                "sales_order",
                "item_code",
                "planned_qty",
                "produced_qty",
                "custom_serial",
                "custom_color",
                "custom_mtul_per_piece"
            ]
        )
        
        # Her sipariş için detaylı bilgileri topla
        orders = []
        total_mtul = 0
        total_pvc = 0
        total_cam = 0
        
        for item in plan_items:
            # Sales Order bilgilerini al
            sales_order = frappe.get_doc("Sales Order", item.sales_order)
            
            # Item bilgilerini al
            item_doc = frappe.get_doc("Item", item.item_code)
            
            # MTÜL hesaplama
            mtul_value = 0
            if item_doc.item_group == "Camlar":
                mtul_value = item.planned_qty * (item.custom_mtul_per_piece or CONSTANTS['DEFAULT_MTUL_CAM'])
                total_cam += item.planned_qty
            else:
                mtul_value = item.planned_qty * (item_doc.custom_total_main_profiles_mtul or 0)
                if item_doc.item_group == "PVC":
                    total_pvc += item.planned_qty
            
            total_mtul += mtul_value
            
            order_info = {
                "sales_order": item.sales_order,
                "bayi": sales_order.customer,
                "musteri": sales_order.custom_end_customer,
                "siparis_tarihi": format_date_for_takip(sales_order.transaction_date),
                "bitis_tarihi": format_date_for_takip(sales_order.delivery_date),
                "seri": item.custom_serial or item_doc.custom_serial,
                "renk": item.custom_color or item_doc.custom_color,
                "pvc_qty": item.planned_qty if item_doc.item_group == "PVC" else 0,
                "cam_qty": item.planned_qty if item_doc.item_group == "Camlar" else 0,
                "total_mtul": mtul_value,
                "acil": bool(sales_order.custom_acil_durum),
                "siparis_aciklama": sales_order.custom_remarks,
                "uretim_plani_durumu": latest_plan.status,
                "produced_qty": item.produced_qty or 0,
                "progress": round((item.produced_qty / item.planned_qty * 100) if item.planned_qty > 0 else 0, 1)
            }
            
            orders.append(order_info)
        
        return {
            "opti_no": opti_no,
            "uretim_plani": latest_plan.name,
            "orders": orders,
            "total_orders": len(orders),
            "plan_status": latest_plan.status,
            "creation_date": format_date_for_takip(latest_plan.creation),
            "modified_date": format_date_for_takip(latest_plan.modified),
            "summary": {
                "total_orders": len(orders),
                "total_mtul": total_mtul,
                "total_pvc": total_pvc,
                "total_cam": total_cam
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Opti Detay Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return {"error": str(e)}


@frappe.whitelist()
def get_sales_order_details_for_takip(sales_order: str) -> Dict[str, Any]:
    """
    Satış siparişi detaylarını getirir - Enhanced version
    """
    try:
        # Sales Order bilgilerini al
        so_doc = frappe.get_doc("Sales Order", sales_order)
        
        # Sipariş itemlerini al
        items = frappe.get_all(
            "Sales Order Item",
            filters={"parent": sales_order},
            fields=[
                "item_code",
                "item_name",
                "qty",
                "rate",
                "amount"
            ]
        )
        
        # MTÜL hesaplama
        total_mtul = 0
        pvc_count = 0
        cam_count = 0
        
        for item in items:
            item_doc = frappe.get_doc("Item", item.item_code)
            
            if item_doc.item_group == "PVC":
                pvc_count += item.qty
                mtul = item.qty * (item_doc.custom_total_main_profiles_mtul or 0)
            elif item_doc.item_group == "Camlar":
                cam_count += item.qty
                mtul = item.qty * (item_doc.custom_mtul_per_piece or CONSTANTS['DEFAULT_MTUL_CAM'])
            else:
                mtul = 0
            
            total_mtul += mtul
        
        return {
            "sales_order": sales_order,
            "bayi": so_doc.customer,
            "musteri": so_doc.custom_end_customer,
            "siparis_tarihi": format_date_for_takip(so_doc.transaction_date),
            "bitis_tarihi": format_date_for_takip(so_doc.delivery_date),
            "opti_no": so_doc.custom_opti_no,
            "seri": so_doc.custom_serial,
            "renk": so_doc.custom_color,
            "pvc_count": pvc_count,
            "cam_count": cam_count,
            "toplam_mtul": total_mtul,
            "acil": bool(so_doc.custom_acil_durum),
            "aciklama": so_doc.custom_remarks
        }
        
    except Exception as e:
        frappe.log_error(f"Sipariş Detay Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return {"error": str(e)}


@frappe.whitelist()
def get_work_orders_for_takip(sales_order: str) -> Union[List[Dict], Dict[str, str]]:
    """
    Satış siparişi için iş emirlerini getirir - Enhanced version
    """
    try:
        # Sales Order'a bağlı iş emirlerini getir
        work_orders = frappe.get_all(
            "Work Order",
            filters={"sales_order": sales_order},
            fields=[
                "name",
                "production_item",
                "qty",
                "produced_qty",
                "status",
                "planned_start_date",
                "planned_end_date",
                "actual_start_date",
                "actual_end_date",
                "creation",
                "modified"
            ],
            order_by="creation desc"
        )
        
        # Her iş emri için ek bilgileri ekle
        for wo in work_orders:
            # Progress hesaplama - Enhanced
            produced_qty = float(wo.get("produced_qty", 0) or 0)
            planned_qty = float(wo.get("qty", 0) or 0)
            if planned_qty > 0:
                wo["progress_percentage"] = round((produced_qty / planned_qty) * 100, 2)
            else:
                wo["progress_percentage"] = 0
                
            wo["status_badge"] = get_status_badge_for_takip(wo.get("status", ""))
        
        return work_orders
            
    except Exception as e:
        frappe.log_error(f"İş Emri Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return {"error": str(e)}


@frappe.whitelist()
def get_autocomplete_data_for_takip(field: str, search: str) -> List[str]:
    """
    Autocomplete için optimize edilmiş veri getirme - Enhanced version
    """
    try:
        search_term = f"%{search}%"
        
        field_queries = {
            'opti_no': """
                SELECT DISTINCT custom_opti_no 
                FROM `tabProduction Plan` 
                WHERE custom_opti_no LIKE %s 
                AND docstatus = 1
                ORDER BY custom_opti_no
                LIMIT 10
            """,
            'bayi': """
                SELECT DISTINCT customer 
                FROM `tabSales Order` 
                WHERE customer LIKE %s 
                AND docstatus = 1
                ORDER BY customer
                LIMIT 10
            """,
            'musteri': """
                SELECT DISTINCT custom_end_customer 
                FROM `tabSales Order` 
                WHERE custom_end_customer LIKE %s 
                AND docstatus = 1
                ORDER BY custom_end_customer
                LIMIT 10
            """,
            'seri': """
                SELECT DISTINCT custom_serial 
                FROM `tabItem` 
                WHERE custom_serial LIKE %s 
                AND item_group IN ('PVC', 'Camlar')
                ORDER BY custom_serial
                LIMIT 10
            """,
            'renk': """
                SELECT DISTINCT custom_color 
                FROM `tabItem` 
                WHERE custom_color LIKE %s 
                AND item_group IN ('PVC', 'Camlar')
                ORDER BY custom_color
                LIMIT 10
            """
        }
        
        if field not in field_queries:
            return []
            
        result = frappe.db.sql(field_queries[field], [search_term], as_list=True)
        return [row[0] for row in result if row[0]]
        
    except Exception as e:
        frappe.log_error(f"Autocomplete Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return []


@frappe.whitelist()
def get_work_order_operations_for_takip(work_order_name: str) -> Dict[str, Any]:
    """
    İş emri operasyonlarını detaylı olarak getirir - Enhanced version
    """
    try:
        # İş emri bilgilerini al
        work_order = frappe.get_doc("Work Order", work_order_name)
        
        # İş emri operasyonlarını getir
        operations = frappe.get_all(
            "Work Order Operation",
            filters={"parent": work_order_name},
            fields=[
                "name",
                "operation",
                "workstation",
                "status",
                "completed_qty",
                "planned_start_time",
                "planned_end_time",
                "actual_start_time",
                "actual_end_time",
                "description"
            ],
            order_by="idx"
        )
        
        # Her operasyon için ek bilgileri al
        for op in operations:
            # Operasyon bilgilerini al
            if op.operation:
                try:
                    operation_doc = frappe.get_doc("Operation", op.operation)
                    op["operation_description"] = operation_doc.description
                    op["operation_time"] = operation_doc.time_in_mins
                except:
                    op["operation_description"] = ""
                    op["operation_time"] = 0
            else:
                op["operation_description"] = ""
                op["operation_time"] = 0
            
            # İş istasyonu bilgilerini al
            if op.workstation:
                try:
                    workstation_doc = frappe.get_doc("Workstation", op.workstation)
                    op["workstation_description"] = workstation_doc.workstation_name
                except:
                    op["workstation_description"] = ""
            else:
                op["workstation_description"] = ""
            
            # İlerleme yüzdesi hesapla
            work_order_qty = work_order.qty or 0
            if work_order_qty > 0:
                op["progress_percentage"] = round((op.completed_qty / work_order_qty) * 100, 2)
            else:
                op["progress_percentage"] = 0
            
            # Durum badge'i oluştur - Modern format
            op["status_badge"] = get_status_badge_for_takip(op.status)
            op["qty"] = work_order_qty
            
            # Tarih formatlarını düzenle
            op["planned_start_formatted"] = format_datetime_for_takip(op.planned_start_time)
            op["planned_end_formatted"] = format_datetime_for_takip(op.planned_end_time)
            op["actual_start_formatted"] = format_datetime_for_takip(op.actual_start_time)
            op["actual_end_formatted"] = format_datetime_for_takip(op.actual_end_time)
        
        return {
            "work_order": {
                "name": work_order.name,
                "production_item": work_order.production_item,
                "qty": work_order.qty,
                "produced_qty": work_order.produced_qty,
                "status": work_order.status,
                "planned_start_date": work_order.planned_start_date,
                "planned_end_date": work_order.planned_end_date,
                "actual_start_date": work_order.actual_start_date,
                "actual_end_date": work_order.actual_end_date
            },
            "operations": operations,
            "total_operations": len(operations),
            "completed_operations": len([op for op in operations if op.status == "Completed"]),
            "in_progress_operations": len([op for op in operations if op.status == "In Progress"]),
            "pending_operations": len([op for op in operations if op.status == "Pending"])
        }
        
    except Exception as e:
        frappe.log_error(f"İş Emri Operasyon Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return {"error": str(e)}


@frappe.whitelist()
def get_production_plan_details(plan_name: str) -> Dict[str, Any]:
    """
    Üretim planı detaylarını getirir - Enhanced version
    """
    try:
        # Üretim planı bilgilerini al
        plan_doc = frappe.get_doc("Production Plan", plan_name)
        
        # Plan itemlerini al
        plan_items = frappe.get_all(
            "Production Plan Item",
            filters={"parent": plan_name},
            fields=[
                "sales_order",
                "item_code",
                "planned_qty",
                "produced_qty",
                "status"
            ]
        )
        
        # İstatistikleri hesapla
        total_qty = sum(item.planned_qty for item in plan_items)
        produced_qty = sum(item.produced_qty for item in plan_items)
        progress_percentage = round((produced_qty / total_qty * 100) if total_qty > 0 else 0, 2)
        
        return {
            "name": plan_doc.name,
            "status": plan_doc.status,
            "planned_start_date": format_date_for_takip(plan_doc.planned_start_date),
            "planned_end_date": format_date_for_takip(plan_doc.planned_end_date),
            "actual_start_date": format_date_for_takip(plan_doc.actual_start_date),
            "actual_end_date": format_date_for_takip(plan_doc.actual_end_date),
            "total_orders": len(set(item.sales_order for item in plan_items)),
            "total_qty": total_qty,
            "produced_qty": produced_qty,
            "progress_percentage": progress_percentage,
            "items": plan_items
        }
        
    except Exception as e:
        frappe.log_error(f"Üretim Planı Detay Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return {"error": str(e)}


@frappe.whitelist()
def get_item_details_for_takip(item_code: str) -> Dict[str, Any]:
    """
    Ürün detaylarını getirir - Enhanced version
    """
    try:
        # Item bilgilerini al
        item_doc = frappe.get_doc("Item", item_code)
        
        return {
            "item_code": item_doc.name,
            "item_name": item_doc.item_name,
            "item_group": item_doc.item_group,
            "seri": item_doc.custom_serial,
            "renk": item_doc.custom_color,
            "stok_turu": item_doc.custom_stok_türü,
            "mtul_per_piece": item_doc.custom_mtul_per_piece,
            "total_main_profiles_mtul": item_doc.custom_total_main_profiles_mtul,
            "length": item_doc.length,
            "width": item_doc.width,
            "height": item_doc.height,
            "weight": item_doc.weight_per_unit,
            "description": item_doc.description,
            "is_stock_item": item_doc.is_stock_item,
            "allow_alternative_item": item_doc.allow_alternative_item
        }
        
    except Exception as e:
        frappe.log_error(f"Ürün Detay Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return {"error": str(e)}


@frappe.whitelist()
def get_sales_order_details_v2(order_no: str) -> Dict[str, Any]:
    """
    Deprecated: use get_sales_order_details_for_takip
    """
    return get_sales_order_details_for_takip(order_no)

@frappe.whitelist()
def get_work_orders_for_sales_order(sales_order: Union[str, Dict], production_plan: str = None) -> List[Dict]:
    """
    Deprecated: use get_work_orders_for_takip
    """
    if isinstance(sales_order, dict):
        sales_order = sales_order.get('sales_order', '')
    return get_work_orders_for_takip(sales_order)

@frappe.whitelist()
def get_work_order_operations(work_order: str) -> List[Dict]:
    """
    Deprecated: use get_work_order_operations_for_takip
    """
    result = get_work_order_operations_for_takip(work_order)
    return result.get("operations", []) if isinstance(result, dict) else result

@frappe.whitelist()
def get_opti_details(opti_no: str) -> Dict[str, Any]:
    """
    Opti numarasına göre detaylı sipariş bilgilerini getir - OPTIMIZE EDİLMİŞ VERSİYON
    N+1 Query problemi çözüldü
    """
    try:
        # Opti numarasına göre üretim planlarını getir
        production_plans = frappe.get_all(
            "Production Plan",
            filters={
                "custom_opti_no": opti_no,
                "docstatus": ["in", [0, 1]]
            },
            fields=["name", "custom_opti_no", "status", "creation", "modified"],
            order_by="creation desc"
        )
        
        if not production_plans:
            return {"error": f"Opti {opti_no} için üretim planı bulunamadı"}
        
        latest_plan = production_plans[0]
        
        # Production Plan Item'ları tek seferde çek
        plan_items = frappe.get_all(
            "Production Plan Item",
            filters={
                "parent": latest_plan.name,
                "planned_qty": [">", 0]
            },
            fields=[
                "sales_order", "item_code", "planned_qty", 
                "custom_serial", "custom_color", "custom_mtul_per_piece"
            ]
        )
        
        # Tüm sales order ve item kodlarını topla
        sales_order_names = list(set(item.sales_order for item in plan_items))
        item_codes = list(set(item.item_code for item in plan_items))
        
        # Sales Order'ları toplu çek - N+1 Query çözümü
        sales_orders_data = {}
        if sales_order_names:
            sales_orders = frappe.get_all(
                "Sales Order",
                filters={"name": ["in", sales_order_names]},
                fields=[
                    "name", "customer", "custom_end_customer", "transaction_date", 
                    "delivery_date", "custom_remarks", "custom_acil_durum"
                ]
            )
            sales_orders_data = {so.name: so for so in sales_orders}
        
        # Item'ları toplu çek - N+1 Query çözümü
        items_data = {}
        if item_codes:
            items = frappe.get_all(
                "Item",
                filters={"name": ["in", item_codes]},
                fields=[
                    "name", "item_group", "custom_serial", "custom_color", 
                    "custom_total_main_profiles_mtul"
                ]
            )
            items_data = {item.name: item for item in items}
        
        # Siparişleri gruplandır (sipariş numarası bazında)
        orders_grouped = {}
        total_mtul = 0
        total_pvc = 0
        total_cam = 0
        
        for item in plan_items:
            sales_order_data = sales_orders_data.get(item.sales_order, {})
            item_data = items_data.get(item.item_code, {})
            
            # MTÜL hesaplama
            mtul_value = 0
            item_group = item_data.get('item_group', '')
            
            if item_group == "Camlar":
                mtul_per_piece = item.custom_mtul_per_piece or CONSTANTS['DEFAULT_MTUL_CAM']
                mtul_value = item.planned_qty * mtul_per_piece
                total_cam += item.planned_qty
            else:
                total_main_profiles_mtul = item_data.get('custom_total_main_profiles_mtul', 0) or 0
                mtul_value = item.planned_qty * total_main_profiles_mtul
                if item_group == "PVC":
                    total_pvc += item.planned_qty
            
            total_mtul += mtul_value
            
            # Sipariş numarasına göre gruplandır
            sales_order = item.sales_order
            if sales_order not in orders_grouped:
                orders_grouped[sales_order] = {
                    "sales_order": sales_order,
                    "bayi": sales_order_data.get('customer', ''),
                    "musteri": sales_order_data.get('custom_end_customer', ''),
                    "siparis_tarihi": format_date_for_takip(sales_order_data.get('transaction_date', '')),
                    "bitis_tarihi": format_date_for_takip(sales_order_data.get('delivery_date', '')),
                    "pvc_qty": 0,
                    "cam_qty": 0,
                    "total_mtul": 0,
                    "uretim_plani_durumu": latest_plan.status,
                    "siparis_aciklama": sales_order_data.get('custom_remarks', '') or "",
                    "is_urgent": sales_order_data.get('custom_acil_durum', False) or False,
                    "items": [],  # Bu siparişe ait ürünler
                    "seri_list": set(),  # Benzersiz seri listesi
                    "renk_list": set()   # Benzersiz renk listesi
                }
            
            # Ürün bilgilerini ekle
            orders_grouped[sales_order]["items"].append({
                "item_code": item.item_code,
                "planned_qty": item.planned_qty,
                "seri": item.custom_serial or item_data.get('custom_serial', ''),
                "renk": item.custom_color or item_data.get('custom_color', ''),
                "item_group": item_group,
                "mtul_value": mtul_value
            })
            
            # PVC/Cam miktarlarını topla
            if item_group == "PVC":
                orders_grouped[sales_order]["pvc_qty"] += item.planned_qty
            elif item_group == "Camlar":
                orders_grouped[sales_order]["cam_qty"] += item.planned_qty
            
            # Toplam MTÜL'ü topla
            orders_grouped[sales_order]["total_mtul"] += mtul_value
            
            # Benzersiz seri ve renkleri ekle
            if item.custom_serial or item_data.get('custom_serial'):
                orders_grouped[sales_order]["seri_list"].add(item.custom_serial or item_data.get('custom_serial', ''))
            if item.custom_color or item_data.get('custom_color'):
                orders_grouped[sales_order]["renk_list"].add(item.custom_color or item_data.get('custom_color', ''))
        
        # Gruplandırılmış verileri düz listeye çevir
        orders = []
        for sales_order, order_data in orders_grouped.items():
            # Seri ve renk bilgilerini string olarak birleştir
            seri_text = ", ".join(filter(None, order_data["seri_list"])) if order_data["seri_list"] else "-"
            renk_text = ", ".join(filter(None, order_data["renk_list"])) if order_data["renk_list"] else "-"
            
            order_info = {
                "sales_order": order_data["sales_order"],
                "bayi": order_data["bayi"],
                "musteri": order_data["musteri"],
                "siparis_tarihi": order_data["siparis_tarihi"],
                "bitis_tarihi": order_data["bitis_tarihi"],
                "seri": seri_text,
                "renk": renk_text,
                "pvc_qty": order_data["pvc_qty"],
                "cam_qty": order_data["cam_qty"],
                "total_mtul": order_data["total_mtul"],
                "uretim_plani_durumu": order_data["uretim_plani_durumu"],
                "siparis_aciklama": order_data["siparis_aciklama"],
                "is_urgent": order_data["is_urgent"],
                "item_count": len(order_data["items"])  # Bu siparişteki toplam ürün sayısı
            }
            
            orders.append(order_info)
        
        # Progress hesaplama - Modern yaklaşım
        progress_data = calculate_progress_data_for_takip(plan_items)
        
        # Özet bilgileri
        summary = {
            "total_pvc": total_pvc,
            "total_cam": total_cam,
            "total_mtul": total_mtul,
            "progress_percentage": progress_data["progress_percentage"],
            "total_planned": progress_data["total_planned"],
            "total_produced": progress_data["total_produced"],
            "is_completed": progress_data["is_completed"],
            "remaining_qty": progress_data["remaining_qty"]
        }
        
        # Plan status badge
        plan_status_badge = get_status_badge_for_takip(latest_plan.status)
        
        return {
            "opti_no": opti_no,
            "production_plan": latest_plan.name,
            "plan_status": latest_plan.status,
            "plan_status_badge": plan_status_badge,
            "orders": orders,
            "summary": summary
        }
        
    except Exception as e:
        frappe.log_error(f"get_opti_details hatası: {str(e)}")
        return {"error": str(e)}

# Enhanced Helper Functions - Modern yaklaşım
def get_completion_percentage(produced_qty: float, planned_qty: float) -> float:
    """Tamamlanma yüzdesini hesaplar - Enhanced version"""
    if not planned_qty or planned_qty == 0:
        return 0
    return round((float(produced_qty) / float(planned_qty)) * 100, 2)

def get_status_badge_for_takip(status: str) -> Dict[str, str]:
    """Status badge bilgilerini döndürür - Enhanced version"""
    status_map = {
        "Completed": {"class": "success", "label": "Tamamlandı"},
        "In Process": {"class": "warning", "label": "Devam Ediyor"}, 
        "Not Started": {"class": "secondary", "label": "Başlanmadı"},
        "Stopped": {"class": "danger", "label": "Durduruldu"},
        "Closed": {"class": "info", "label": "Kapatıldı"},
        "Draft": {"class": "light", "label": "Taslak"}
    }
    
    return status_map.get(status, {"class": "secondary", "label": status})

def format_date_for_takip(date_str: Any) -> Optional[str]:
    """
    Tarih formatını düzenler - Enhanced version
    """
    if not date_str:
        return None
    
    try:
        if isinstance(date_str, str):
            # Farklı tarih formatlarını destekle
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime("%d.%m.%Y")
                except ValueError:
                    continue
        elif hasattr(date_str, 'strftime'):
            return date_str.strftime("%d.%m.%Y")
        
        return str(date_str)
    except Exception:
        return str(date_str)

def calculate_mtul_for_takip(qty: Union[int, float], mtul_per_piece: Union[int, float]) -> float:
    """
    MTÜL hesaplama fonksiyonu - Enhanced version
    """
    try:
        return round(float(qty) * float(mtul_per_piece), 2)
    except (ValueError, TypeError):
        return 0.0

def check_urgent_delivery_for_takip(delivery_date: Any) -> bool:
    """
    Acil teslimat kontrolü - Enhanced version
    """
    if not delivery_date:
        return False
    
    try:
        if isinstance(delivery_date, str):
            delivery = datetime.strptime(delivery_date, "%Y-%m-%d")
        elif hasattr(delivery_date, 'date'):
            delivery = delivery_date
        else:
            return False
        
        today = datetime.now()
        # 3 gün içinde teslim edilecekse acil say
        return (delivery.date() - today.date()).days <= 3
    except Exception:
        return False 

def format_datetime_for_takip(datetime_str: Any) -> Optional[str]:
    """
    Datetime formatını düzenler - Enhanced version
    """
    if not datetime_str:
        return None
    
    try:
        if isinstance(datetime_str, str):
            # Farklı datetime formatlarını destekle
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
                try:
                    datetime_obj = datetime.strptime(datetime_str, fmt)
                    return datetime_obj.strftime("%d.%m.%Y %H:%M")
                except ValueError:
                    continue
        elif hasattr(datetime_str, 'strftime'):
            return datetime_str.strftime("%d.%m.%Y %H:%M")
        
        return str(datetime_str)
    except Exception:
        return str(datetime_str)

def calculate_progress_data_for_takip(items: List[Dict]) -> Dict[str, Any]:
    """
    İlerleme verilerini hesaplar - Enhanced version
    """
    total_planned = sum(float(item.get('planned_qty', 0) or 0) for item in items)
    total_produced = sum(float(item.get('produced_qty', 0) or 0) for item in items)
    
    progress_percentage = round((total_produced / total_planned * 100) if total_planned > 0 else 0, 1)
    
    return {
        "total_planned": total_planned,
        "total_produced": total_produced,
        "progress_percentage": progress_percentage,
        "is_completed": progress_percentage >= 100,
        "remaining_qty": max(0, total_planned - total_produced)
    }


@frappe.whitelist()
def update_work_order_status(work_order_name: str, new_status: str) -> Dict[str, Any]:
    """
    İş emri durumunu günceller - Enhanced version
    """
    try:
        # İş emri dokümanını al
        work_order = frappe.get_doc("Work Order", work_order_name)
        
        # Durumu güncelle
        work_order.status = new_status
        
        # Açıklama ekle
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')
        work_order.custom_remarks = f"Durum {new_status} olarak güncellendi - {timestamp}"
        
        # Kaydet
        work_order.save()
        
        # Log kaydı
        frappe.logger().info(f"İş Emri durumu güncellendi: {work_order_name} -> {new_status}")
        
        return {
            "success": True,
            "message": f"İş emri durumu başarıyla güncellendi: {new_status}",
            "work_order": work_order_name,
            "new_status": new_status,
            "updated_at": timestamp
        }
        
    except Exception as e:
        error_msg = f"İş Emri Durum Güncelleme Hatası: {str(e)}"
        frappe.log_error(error_msg, "Uretim Planlama Takip Paneli")
        return {
            "success": False,
            "error": str(e),
            "work_order": work_order_name,
            "attempted_status": new_status
        } 