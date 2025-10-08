# -*- coding: utf-8 -*-
# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
Üretim Planlama Paneli API Metodları
Bu dosya uretim_planlama_paneli sayfası için tüm API metodlarını içerir.
SADECE KULLANILAN METHODLAR - TEMIZ KOD - YÜKSEK PERFORMANS
OPTIMIZE EDİLMİŞ VERSİYON - N+1 Query problemleri çözüldü
"""

# Standard library imports
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import time

# Frappe imports
import frappe
from frappe import _

def get_real_completed_qty_from_job_cards(work_order_name: str, operation_id: str) -> float:
    """
    Job Card'lardan gerçek tamamlanan miktarı hesaplar (artırımlı güncelleme için).
    Bu fonksiyon duplicate kodu önlemek için ortak olarak kullanılır.
    """
    try:
        job_card_completed_qty = frappe.db.sql("""
            SELECT COALESCE(SUM(total_completed_qty), 0) as total_completed
            FROM `tabJob Card`
            WHERE work_order = %s AND operation_id = %s AND docstatus = 1
        """, (work_order_name, operation_id), as_dict=True)
        
        return job_card_completed_qty[0].total_completed if job_card_completed_qty else 0
    except Exception as e:
        frappe.log_error(f"get_real_completed_qty_from_job_cards hatası: {str(e)}")
        return 0

from frappe.utils import get_datetime, getdate, add_days

# Third party imports (conditional) - pandas kullanılmadığı için kaldırıldı

# Constants - Optimize edilmiş
CONSTANTS = {
    'DAY_NAMES_TR': {
        "Monday": "Pazartesi",
        "Tuesday": "Salı", 
        "Wednesday": "Çarşamba",
        "Thursday": "Perşembe",
        "Friday": "Cuma",
        "Saturday": "Cumartesi",
        "Sunday": "Pazar",
    },
    'STATUS_MAP': {
        "In Process": "Devam ediyor",
        "Completed": "Tamamlandı", 
        "Not Started": "Açık",
        "Açık": "Açık",
        "Devam ediyor": "Devam ediyor",
        "Tamamlandı": "Tamamlandı",
        "İptal Edildi": "İptal Edildi",
    },
    'DEFAULT_LIMIT': 0,  # 0 = sınırsız
    'CACHE_DURATION': 600000,  # 10 dakika - artırıldı
    'MAX_RETRIES': 3,
    'DEFAULT_MTUL_CAM': 1.745,
    'DEFAULT_MTUL_PVC': 11.35,
    'MAX_QUERY_LIMIT': 0  # 0 = sınırsız
}

# Enhanced cache helpers (Redis-backed via frappe.cache)
def _cache_get(key: str, ttl_seconds: int = 600):
    try:
        cache = frappe.cache()
        cached = cache.get_value(key)
        if not cached:
            return None
        ts = cached.get('ts', 0)
        if (time.time() - float(ts)) <= ttl_seconds:
            return cached.get('data')
        # Eski cache'i temizle
        cache.delete_value(key)
        return None
    except Exception:
        return None

def _cache_set(key: str, data: Any, ttl_seconds: int = 600):
    try:
        cache = frappe.cache()
        cache_data = {"data": data, "ts": time.time(), "ttl": ttl_seconds}
        cache.set_value(key, cache_data, expires_in_sec=ttl_seconds)
    except Exception:
        pass

def validate_filters(filters: Dict) -> Dict:
    """Filter validation ve sanitization"""
    validated = {}
    if filters.get("limit"):
        validated["limit"] = int(filters["limit"]) if int(filters["limit"]) > 0 else 0
    else:
        validated["limit"] = CONSTANTS['DEFAULT_LIMIT']
    
    # String filtreleri sanitize et
    string_filters = ['hafta', 'opti_no', 'siparis_no', 'bayi', 'musteri', 'seri', 'renk', 'durum', 'workflow_state', 'tip']
    for filter_name in string_filters:
        if filters.get(filter_name):
            validated[filter_name] = str(filters[filter_name]).strip()
    
    # Planlanan tarih filtreleri (YYYY-MM-DD)
    if filters.get('from_date'):
        validated['from_date'] = str(filters['from_date']).strip()
    if filters.get('to_date'):
        validated['to_date'] = str(filters['to_date']).strip()

    # Planlanmamış teslim tarih filtreleri
    if filters.get('delivery_from_date'):
        validated['delivery_from_date'] = str(filters['delivery_from_date']).strip()
    if filters.get('delivery_to_date'):
        validated['delivery_to_date'] = str(filters['delivery_to_date']).strip()
    
    return validated

def apply_common_filters(where_conditions: List[str], params: List, filters: Dict, table_prefix: str = "so") -> None:
    """Ortak filter logic'i - DRY prensibi"""
    
    if filters.get("hafta"):
        where_conditions.append(f"WEEK({table_prefix}.transaction_date) = %s")
        params.append(int(filters["hafta"]))
    
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
    
    if filters.get("acil_durum"):
        if filters["acil_durum"] == "ACİL":
            where_conditions.append(f"COALESCE({table_prefix}.custom_acil_durum, 0) = 1")
        elif filters["acil_durum"] == "NORMAL":
            where_conditions.append(f"COALESCE({table_prefix}.custom_acil_durum, 0) = 0")

def apply_tip_filter(where_conditions: List[str], filters: Dict, query_type: str = "planned") -> None:
    """PLANLANAN ÜRETİMLER için Cam/PVC/Karışık filtresi - DOKUNMA!"""
    tip_filter = filters.get("tip")
    if not tip_filter:
        return
        
    if tip_filter == "PVC":
        where_conditions.append("(i.item_group = 'PVC' OR i.custom_stok_türü = 'PVC')")
    elif tip_filter == "Cam":
        where_conditions.append("(i.item_group = 'Camlar' OR i.custom_stok_türü = 'Camlar')")
    elif tip_filter == "Karışık":
        if query_type == "planned":
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

def apply_tip_filter_unplanned(where_conditions: List[str], filters: Dict) -> None:
    """PLANLANMAMIŞ SİPARİŞLER için sadece Cam/PVC filtresi - Karışık YOK"""
    tip_filter = filters.get("tip")
    if not tip_filter:
        return
        
    if tip_filter == "PVC":
        where_conditions.append("(i.item_group = 'PVC' OR i.custom_stok_türü = 'PVC')")
    elif tip_filter == "Cam":
        where_conditions.append("(i.item_group = 'Camlar' OR i.custom_stok_türü = 'Camlar')")
    # Karışık filtresi yok - performans için

@frappe.whitelist()
def get_production_planning_data(filters: Optional[Union[str, Dict]] = None) -> Dict[str, Any]:
    """
    Üretim planlama sayfası için optimize edilmiş veri çekme
    """
    try:
        filters = json.loads(filters) if isinstance(filters, str) else (filters or {})
        filters = validate_filters(filters)

        # Cache kontrolü
        cache_key = f"upp:planned-unplanned:{json.dumps(filters, sort_keys=True)}"
        cached = _cache_get(cache_key, ttl_seconds=int(CONSTANTS['CACHE_DURATION'] / 1000))
        if cached:
            return cached

        # Tüm verileri tek seferde çek
        planned, unplanned = get_optimized_data_v2(filters)
        
        result = {"planned": planned, "unplanned": unplanned}
        # Cache'e kaydet
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        frappe.log_error(f"Üretim Paneli Hatası: {str(e)}")
        return {"error": str(e), "planned": [], "unplanned": []}

def get_optimized_data_v2(filters: Dict) -> tuple[List[Dict], List[Dict]]:
    """
    V2: Daha da optimize edilmiş veri çekme - Subquery'ler JOIN'e çevrildi
    """
    try:
        limit = filters.get("limit", CONSTANTS['DEFAULT_LIMIT'])  # LIMIT kısıtlaması kaldırıldı
        
        # Production Plan için optimize edilmiş sorgu - Subquery JOIN'e çevrildi
        planned_query = """
            SELECT 
                pp.name as uretim_plani,
                pp.custom_opti_no as opti_no,
                pp.status as plan_status,
                ppi.sales_order,
                ppi.sales_order_item,
                ppi.item_code,
                ppi.planned_qty as adet,
                so.customer as bayi,
                so.custom_end_customer as musteri,
                so.transaction_date as siparis_tarihi,
                so.delivery_date as bitis_tarihi,
                soi.description as aciklama,
                COALESCE(i.custom_stok_türü, i.item_group) as tip,
                i.custom_color as renk,
                WEEK(so.transaction_date) as hafta,
                COALESCE(so.custom_acil_durum, 0) as acil,
                so.total_qty as siparis_total_qty,
                i.item_group as urun_grubu,
                soi.qty as siparis_item_qty,
                i.custom_serial as seri,
                ppi.planned_start_date as planlanan_baslangic_tarihi,
                ppi.planned_end_date as planned_end_date,
                CASE 
                    WHEN i.item_group = 'Camlar' OR i.custom_stok_türü = 'Camlar'
                    THEN ppi.planned_qty * COALESCE(ppi.custom_mtul_per_piece, %s)
                    ELSE ppi.planned_qty * COALESCE(i.custom_total_main_profiles_mtul, 0)
                END as toplam_mtul_m2,
                ppi.planned_qty as planlanan_miktar,
                COALESCE(so.custom_remarks, '') as siparis_aciklama,
                'Not Started' as work_order_status
            FROM `tabProduction Plan` pp
            INNER JOIN `tabProduction Plan Item` ppi ON pp.name = ppi.parent
            INNER JOIN `tabSales Order` so ON ppi.sales_order = so.name
            INNER JOIN `tabSales Order Item` soi ON ppi.sales_order_item = soi.name
            INNER JOIN `tabItem` i ON ppi.item_code = i.name
            WHERE pp.docstatus = 1 
            AND ppi.planned_qty > 0
            AND i.item_group != 'All Item Groups'
        """
        
        # Filtreleri ekle
        where_conditions = []
        params = [CONSTANTS['DEFAULT_MTUL_CAM']]
        
        if filters.get("opti_no"):
            where_conditions.append("pp.custom_opti_no LIKE %s")
            params.append(f"%{filters['opti_no']}%")
        
        apply_common_filters(where_conditions, params, filters)
        apply_tip_filter(where_conditions, filters, "planned")
        
        if where_conditions:
            planned_query += " AND " + " AND ".join(where_conditions)

        # Planlanan başlangıç tarihi filtreleri (tek taraflı ve aralık)
        if filters.get("from_date") and filters.get("to_date"):
            planned_query += " AND ppi.planned_start_date BETWEEN %s AND %s"
            params.append(filters["from_date"])
            params.append(filters["to_date"])
        elif filters.get("from_date") and not filters.get("to_date"):
            planned_query += " AND ppi.planned_start_date >= %s"
            params.append(filters["from_date"])
        elif filters.get("to_date") and not filters.get("from_date"):
            planned_query += " AND ppi.planned_start_date <= %s"
            params.append(filters["to_date"])
        
        planned_query += " ORDER BY so.delivery_date ASC"
        
        # TÜM VERİLERİ çek - LIMIT yok
        planned_data = frappe.db.sql(planned_query, params, as_dict=True)
        
        # Planlanmamış siparişler için optimize edilmiş sorgu - TÜM VERİLER
        
        unplanned_query = """
            SELECT 
                so.name as sales_order,
                so.customer as bayi,
                so.custom_end_customer as musteri,
                soi.item_code,
                (soi.qty - COALESCE(planned_qty.planned_qty, 0)) as unplanned_qty,
                so.transaction_date as siparis_tarihi,
                so.delivery_date as bitis_tarihi,
                soi.description as aciklama,
                COALESCE(i.custom_stok_türü, i.item_group) as tip,
                i.custom_color as renk,
                WEEK(so.transaction_date) as hafta,
                COALESCE(so.custom_acil_durum, 0) as acil,
                i.item_group as urun_grubu,
                soi.qty as siparis_item_qty,
                i.custom_serial as seri,
                so.custom_remarks as siparis_aciklama,
                so.status as siparis_durumu,
                so.workflow_state as is_akisi_durumu,
                so.docstatus as belge_durumu,
                COALESCE(so.custom_mly_list_uploaded, 0) as mly_dosyasi_var,
                CASE 
                    WHEN i.item_group = 'PVC' THEN (soi.qty - COALESCE(planned_qty.planned_qty, 0))
                    ELSE 0 
                END as pvc_qty,
                CASE 
                    WHEN i.item_group = 'Camlar' THEN (soi.qty - COALESCE(planned_qty.planned_qty, 0))
                    ELSE 0 
                END as cam_qty,
                CASE 
                    WHEN i.custom_amount_per_piece IS NOT NULL AND i.custom_amount_per_piece > 0 
                    THEN (soi.qty - COALESCE(planned_qty.planned_qty, 0)) * i.custom_amount_per_piece
                    ELSE (soi.qty - COALESCE(planned_qty.planned_qty, 0))
                END as total_mtul,
                COALESCE(kismi_check.kismi_planlama, 0) as kismi_planlama
            FROM `tabSales Order` so
            INNER JOIN `tabSales Order Item` soi ON so.name = soi.parent
            INNER JOIN `tabItem` i ON soi.item_code = i.name
            LEFT JOIN (
                SELECT 
                    ppi.sales_order_item,
                    SUM(ppi.planned_qty) as planned_qty
                FROM `tabProduction Plan Item` ppi
                INNER JOIN `tabProduction Plan` pp ON ppi.parent = pp.name
                WHERE pp.docstatus = 1 AND pp.status != 'Closed'
                GROUP BY ppi.sales_order_item
            ) planned_qty ON soi.name = planned_qty.sales_order_item
            LEFT JOIN (
                SELECT DISTINCT 
                    soi2.parent as sales_order,
                    1 as kismi_planlama
                FROM `tabProduction Plan Item` ppi2
                INNER JOIN `tabProduction Plan` pp2 ON ppi2.parent = pp2.name
                INNER JOIN `tabSales Order Item` soi2 ON ppi2.sales_order_item = soi2.name
                INNER JOIN `tabItem` i2 ON soi2.item_code = i2.name
                INNER JOIN `tabSales Order Item` soi3 ON soi2.parent = soi3.parent
                INNER JOIN `tabItem` i3 ON soi3.item_code = i3.name
                WHERE pp2.docstatus = 1 AND pp2.status != 'Closed'
                AND (i2.custom_serial != i3.custom_serial OR i2.custom_color != i3.custom_color)
            ) kismi_check ON kismi_check.sales_order = so.name
            WHERE so.docstatus = 1
            AND i.item_group IS NOT NULL
            AND (i.item_group IN ('PVC', 'Camlar') OR i.custom_stok_türü IN ('PVC', 'Camlar'))
            AND (soi.qty - COALESCE(planned_qty.planned_qty, 0)) > 0
        """
        
        # Planlanmamış için filtreleri ekle
        unplanned_where_conditions = []
        unplanned_params = []
        
        apply_common_filters(unplanned_where_conditions, unplanned_params, filters)
        
        if filters.get("siparis_durum"):
            unplanned_where_conditions.append("so.status = %s")
            unplanned_params.append(filters["siparis_durum"])
        
        if filters.get("workflow_state") and filters["workflow_state"].strip():
            unplanned_where_conditions.append("so.workflow_state = %s")
            unplanned_params.append(filters["workflow_state"])
        
        apply_tip_filter_unplanned(unplanned_where_conditions, filters)
        
        if unplanned_where_conditions:
            unplanned_query += " AND " + " AND ".join(unplanned_where_conditions)

        # Planlanmamış için teslim tarihi filtreleri (tek taraflı ve aralık)
        if filters.get("delivery_from_date") and filters.get("delivery_to_date"):
            unplanned_query += " AND so.delivery_date BETWEEN %s AND %s"
            unplanned_params.append(filters["delivery_from_date"])
            unplanned_params.append(filters["delivery_to_date"])
        elif filters.get("delivery_from_date") and not filters.get("delivery_to_date"):
            unplanned_query += " AND so.delivery_date >= %s"
            unplanned_params.append(filters["delivery_from_date"])
        elif filters.get("delivery_to_date") and not filters.get("delivery_from_date"):
            unplanned_query += " AND so.delivery_date <= %s"
            unplanned_params.append(filters["delivery_to_date"])

        # TÜM VERİLERİ çek - LIMIT yok
        unplanned_query += " ORDER BY so.delivery_date ASC"
        
        unplanned_data = frappe.db.sql(unplanned_query, unplanned_params, as_dict=True)
        
        # Veri sayısını log'la
        frappe.logger().info(f"Unplanned data count: {len(unplanned_data)}")
        
        # Verileri formatla - Optimize edilmiş
        planned_formatted = format_planned_data_optimized(planned_data)
        unplanned_formatted = format_unplanned_data_optimized(unplanned_data)
        
        return planned_formatted, unplanned_formatted
        
    except Exception as e:
        frappe.log_error(f"get_optimized_data_v2 hatası: {str(e)}")
        return [], []

def format_planned_data(planned_data: List[Dict]) -> List[Dict]:
    """
    Planlanan verileri formatla
    """
    try:
        if not planned_data:
            return []
        
        # Verileri formatla ve PVC/Camlar sayısını hesapla
        planned_formatted = []
        processed_combinations = set()
        
        # Önce tüm verileri grupla (sipariş + seri + renk bazında)
        grouped_data = {}
        
        for item in planned_data:
            sales_order = item['sales_order']
            seri = item.get('seri', '')
            renk = item.get('renk', '')
            combination_key = f"{sales_order}_{seri}_{renk}"
            
            if combination_key not in grouped_data:
                grouped_data[combination_key] = {
                    'sales_order': sales_order,
                    'seri': seri,
                    'renk': renk,
                    'items': [],
                    'total_pvc': 0,
                    'total_cam': 0,
                    'total_mtul': 0,
                    'total_planned_qty': 0
                }
            
            # Bu ürünü gruba ekle
            grouped_data[combination_key]['items'].append(item)
            
            # PVC/Cam hesapla (sipariş miktarı)
            urun_grubu = item.get('urun_grubu', '')
            planlanan_miktar = float(item.get('planlanan_miktar', 0) or 0)
            toplam_mtul_m2 = float(item.get('toplam_mtul_m2', 0) or 0)
            urun_grubu_str = str(urun_grubu or '').lower()
            
            if urun_grubu_str == 'pvc':
                grouped_data[combination_key]['total_pvc'] += planlanan_miktar
            elif urun_grubu_str == 'camlar':
                grouped_data[combination_key]['total_cam'] += planlanan_miktar
            
            grouped_data[combination_key]['total_mtul'] += toplam_mtul_m2
            grouped_data[combination_key]['total_planned_qty'] += planlanan_miktar
        
        # Gruplandırılmış verileri formatla
        for combination_key, group_data in grouped_data.items():
            if combination_key in processed_combinations:
                continue
                
            processed_combinations.add(combination_key)
            
            # İlk ürünü temel al (sipariş bilgileri için)
            first_item = group_data['items'][0]
            
            # Debug loglar kaldırıldı (performans için)
            
            # Gruplandırılmış verilerden formatlanmış veri oluştur
            sales_order = group_data['sales_order']
            seri = group_data['seri']
            renk = group_data['renk']
            
            # İş emirlerinin durumunu kontrol et
            work_order_status = first_item.get('work_order_status', 'Not Started')
            plan_status = 'Completed' if work_order_status == 'Completed' else first_item.get('plan_status', 'Not Started')
            
            formatted_item = {
                'uretim_plani': first_item['uretim_plani'],
                'opti_no': first_item.get('opti_no'),
                'sales_order': sales_order,
                'item_code': f"{sales_order} ({len(group_data['items'])} ürün)",
                'adet': group_data['total_planned_qty'],
                'hafta': first_item.get('hafta'),
                'siparis_total_qty': first_item['siparis_total_qty'],
                'bayi': first_item['bayi'],
                'musteri': first_item['musteri'],
                'siparis_tarihi': first_item['siparis_tarihi'].strftime('%Y-%m-%d') if first_item['siparis_tarihi'] else None,
                'tip': first_item['tip'],
                'renk': renk or '-',
                'seri': seri or '-',
                'aciklama': first_item.get('siparis_aciklama') or f"{len(group_data['items'])} ürün grubu",
                'bitis_tarihi': first_item['bitis_tarihi'].strftime('%Y-%m-%d') if first_item['bitis_tarihi'] else None,
                'acil': bool(first_item['acil']),
                'durum_badges': [],  # Badge logic kaldırıldı - performans için
                'pvc_count': group_data['total_pvc'],
                'cam_count': group_data['total_cam'],
                'toplam_mtul_m2': group_data['total_mtul'],
                'planlanan_baslangic_tarihi': first_item.get('planlanan_baslangic_tarihi').strftime('%Y-%m-%d') if first_item.get('planlanan_baslangic_tarihi') else None,
                'planned_end_date': first_item.get('planned_end_date').strftime('%Y-%m-%d') if first_item.get('planned_end_date') and first_item.get('planned_end_date') != 'None' else None,
                'plan_status': plan_status
            }
            planned_formatted.append(formatted_item)
        
        return planned_formatted
        
    except Exception as e:
        frappe.log_error(f"format_planned_data hatası: {str(e)}")
        return []

def format_unplanned_data(unplanned_data: List[Dict]) -> List[Dict]:
    """
    Planlanmamış verileri formatla - Aynı sipariş + seri + renk kombinasyonunu grupla
    Aynı sipariş, seri ve renk olan ürünler tek satırda toplu gösterilecek
    """
    try:
        
        if not unplanned_data:
            return []
        
        # Sipariş + seri + renk kombinasyonuna göre grupla
        product_groups = {}
        
        for item in unplanned_data:
            sales_order = item['sales_order']
            seri = item.get('seri', '')
            renk = item.get('renk', '')
            
            # Unique key: sipariş + seri + renk
            group_key = f"{sales_order}_{seri}_{renk}"
            
            # İlk kez görülen grup için kayıt oluştur
            if group_key not in product_groups:
                product_groups[group_key] = {
                    'sales_order': sales_order,
                    'seri': seri,
                    'renk': renk,
                    'bayi': item.get('bayi', ''),
                    'musteri': item.get('musteri', ''),
                    'siparis_tarihi': item.get('siparis_tarihi'),
                    'bitis_tarihi': item.get('bitis_tarihi'),
                    'hafta': item.get('hafta'),
                    'aciklama': item.get('siparis_aciklama', ''),
                    'acil': bool(item.get('acil', 0)),
                    'siparis_durumu': item.get('siparis_durumu', 'Draft'),
                    'is_akisi_durumu': item.get('is_akisi_durumu', ''),
                    'workflow_state': item.get('is_akisi_durumu', ''),
                    'belge_durumu': item.get('belge_durumu', 0),
                    'mly_dosyasi_var': item.get('mly_dosyasi_var', 0),
                    'kismi_planlama': item.get('kismi_planlama', 0),
                    'pvc_qty': 0,
                    'cam_qty': 0,
                    'total_mtul': 0
                }
            
            # Miktarları topla
            group = product_groups[group_key]
            group['pvc_qty'] += float(item.get('pvc_qty', 0) or 0)
            group['cam_qty'] += float(item.get('cam_qty', 0) or 0)
            group['total_mtul'] += float(item.get('total_mtul', 0) or 0)
        
        # Formatlanmış listeye çevir - Her grup bir satır olacak
        unplanned_formatted = []
        for group_key, group in product_groups.items():
            formatted_item = {
                'sales_order': group['sales_order'],
                'item_code': f"{group['sales_order']}_{group['seri']}_{group['renk']}",
                'bayi': group['bayi'],
                'musteri': group['musteri'],
                'siparis_tarihi': group['siparis_tarihi'].strftime('%Y-%m-%d') if group['siparis_tarihi'] else None,
                'bitis_tarihi': group['bitis_tarihi'].strftime('%Y-%m-%d') if group['bitis_tarihi'] else None,
                'hafta': group['hafta'],
                'seri': group['seri'] or '-',
                'renk': group['renk'] or '-',
                'aciklama': group['aciklama'],
                'acil': group['acil'],
                'pvc_count': group['pvc_qty'],
                'cam_count': group['cam_qty'],
                'total_mtul': group['total_mtul'],
                'siparis_durumu': group['siparis_durumu'],
                'is_akisi_durumu': group['is_akisi_durumu'],
                'workflow_state': group['workflow_state'],
                'belge_durumu': group['belge_durumu'],
                'mly_dosyasi_var': group['mly_dosyasi_var'],
                'kismi_planlama': group['kismi_planlama']
            }
            
            unplanned_formatted.append(formatted_item)
        
        # Sipariş numarasına göre sırala
        unplanned_formatted.sort(key=lambda x: x['sales_order'])
        
        return unplanned_formatted
        
    except Exception as e:
        frappe.log_error(f"format_unplanned_data hatası: {str(e)}")
        return []

def format_planned_data_optimized(planned_data: List[Dict]) -> List[Dict]:
    """
    Optimize edilmiş planlanan veri formatlaması - Daha hızlı gruplama
    """
    try:
        if not planned_data:
            return []
        
        # Tek geçişte gruplama ve hesaplama
        grouped_data = {}
        
        for item in planned_data:
            sales_order = item['sales_order']
            seri = item.get('seri', '') or ''
            renk = item.get('renk', '') or ''
            combination_key = f"{sales_order}_{seri}_{renk}"
            
            if combination_key not in grouped_data:
                # İlk kayıt - tüm bilgileri al
                grouped_data[combination_key] = {
                    'uretim_plani': item['uretim_plani'],
                    'opti_no': item.get('opti_no'),
                    'sales_order': sales_order,
                    'item_code': f"{sales_order} (1 ürün)",  # Başlangıç
                    'hafta': item.get('hafta'),
                    'siparis_total_qty': item['siparis_total_qty'],
                    'bayi': item['bayi'],
                    'musteri': item['musteri'],
                    'siparis_tarihi': item['siparis_tarihi'].strftime('%Y-%m-%d') if item['siparis_tarihi'] else None,
                    'tip': item['tip'],
                    'renk': renk or '-',
                    'seri': seri or '-',
                    'aciklama': item.get('siparis_aciklama') or 'Ürün grubu',
                    'bitis_tarihi': item['bitis_tarihi'].strftime('%Y-%m-%d') if item['bitis_tarihi'] else None,
                    'acil': bool(item['acil']),
                    'durum_badges': [],
                    'planlanan_baslangic_tarihi': item.get('planlanan_baslangic_tarihi').strftime('%Y-%m-%d') if item.get('planlanan_baslangic_tarihi') else None,
                    'planned_end_date': item.get('planned_end_date').strftime('%Y-%m-%d') if item.get('planned_end_date') and item.get('planned_end_date') != 'None' else None,
                    'plan_status': 'Completed' if item.get('work_order_status') == 'Completed' else item.get('plan_status', 'Not Started'),
                    'adet': 0,
                    'pvc_count': 0,
                    'cam_count': 0,
                    'toplam_mtul_m2': 0,
                    'item_count': 0
                }
            
            # Miktarları topla
            group = grouped_data[combination_key]
            planlanan_miktar = float(item.get('planlanan_miktar', 0) or 0)
            toplam_mtul_m2 = float(item.get('toplam_mtul_m2', 0) or 0)
            urun_grubu = str(item.get('urun_grubu', '') or '').lower()
            
            group['adet'] += planlanan_miktar
            group['toplam_mtul_m2'] += toplam_mtul_m2
            group['item_count'] += 1
            
            # PVC/Cam ayrımı
            if urun_grubu == 'pvc':
                group['pvc_count'] += planlanan_miktar
            elif urun_grubu == 'camlar':
                group['cam_count'] += planlanan_miktar
            
            # Item code güncelle
            if group['item_count'] > 1:
                group['item_code'] = f"{sales_order} ({group['item_count']} ürün)"
        
        return list(grouped_data.values())
        
    except Exception as e:
        frappe.log_error(f"format_planned_data_optimized hatası: {str(e)}")
        return []

def format_unplanned_data_optimized(unplanned_data: List[Dict]) -> List[Dict]:
    """
    Optimize edilmiş planlanmamış veri formatlaması - Daha hızlı gruplama
    """
    try:
        if not unplanned_data:
            return []
        
        # Tek geçişte gruplama
        grouped_data = {}
        
        for item in unplanned_data:
            sales_order = item['sales_order']
            seri = item.get('seri', '') or ''
            renk = item.get('renk', '') or ''
            group_key = f"{sales_order}_{seri}_{renk}"
            
            if group_key not in grouped_data:
                # İlk kayıt - tüm bilgileri al
                grouped_data[group_key] = {
                    'sales_order': sales_order,
                    'item_code': f"{sales_order}_{seri}_{renk}",
                    'bayi': item.get('bayi', ''),
                    'musteri': item.get('musteri', ''),
                    'siparis_tarihi': item.get('siparis_tarihi').strftime('%Y-%m-%d') if item.get('siparis_tarihi') else None,
                    'bitis_tarihi': item.get('bitis_tarihi').strftime('%Y-%m-%d') if item.get('bitis_tarihi') else None,
                    'hafta': item.get('hafta'),
                    'seri': seri or '-',
                    'renk': renk or '-',
                    'aciklama': item.get('siparis_aciklama', ''),
                    'acil': bool(item.get('acil', 0)),
                    'siparis_durumu': item.get('siparis_durumu', 'Draft'),
                    'is_akisi_durumu': item.get('is_akisi_durumu', ''),
                    'workflow_state': item.get('is_akisi_durumu', ''),
                    'belge_durumu': item.get('belge_durumu', 0),
                    'mly_dosyasi_var': item.get('mly_dosyasi_var', 0),
                    'kismi_planlama': item.get('kismi_planlama', 0),
                    'pvc_count': 0,
                    'cam_count': 0,
                    'total_mtul': 0
                }
            
            # Miktarları topla
            group = grouped_data[group_key]
            group['pvc_count'] += float(item.get('pvc_qty', 0) or 0)
            group['cam_count'] += float(item.get('cam_qty', 0) or 0)
            group['total_mtul'] += float(item.get('total_mtul', 0) or 0)
        
        # Sipariş numarasına göre sıralı liste döndür
        return sorted(grouped_data.values(), key=lambda x: x['sales_order'])
        
    except Exception as e:
        frappe.log_error(f"format_unplanned_data_optimized hatası: {str(e)}")
        return []

@frappe.whitelist()
def clear_production_panel_cache():
    """
    Üretim paneli cache'ini temizle - Performance maintenance için
    """
    try:
        cache = frappe.cache()
        # Cache prefix'i ile tüm panel cache'lerini temizle
        cache_keys = cache.get_keys("upp:*")
        cleared_count = 0
        
        for key in cache_keys:
            try:
                cache.delete_value(key)
                cleared_count += 1
            except:
                continue
        
        return {
            "success": True,
            "message": f"{cleared_count} cache kaydı temizlendi",
            "cleared_count": cleared_count
        }
    except Exception as e:
        frappe.log_error(f"Cache temizleme hatası: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_work_order_statuses(production_plans: str) -> Dict[str, str]:
    """
    Üretim planları için Work Order durumlarını ayrı olarak getir
    Ana sorgudan ayrıldı - performans için
    """
    try:
        import json
        if isinstance(production_plans, str):
            plans = json.loads(production_plans)
        else:
            plans = production_plans
            
        if not plans:
            return {}
            
        # Cache kontrolü
        cache_key = f"upp:wo_status:{hash(str(sorted(plans)))}"
        cached = _cache_get(cache_key, ttl_seconds=300)  # 5 dakika cache
        if cached:
            return cached
            
        # Toplu Work Order durumu sorgusu
        placeholders = ', '.join(['%s'] * len(plans))
        wo_status_query = f"""
            SELECT 
                wo.production_plan,
                CASE 
                    WHEN COUNT(*) = 0 THEN 'Not Started'
                    WHEN SUM(CASE WHEN wo.status = 'Completed' THEN 1 ELSE 0 END) = COUNT(*) THEN 'Completed'
                    WHEN SUM(CASE WHEN wo.status IN ('In Process', 'Completed') THEN 1 ELSE 0 END) > 0 THEN 'In Process'
                    ELSE 'Not Started'
                END as work_order_status
            FROM `tabWork Order` wo
            WHERE wo.production_plan IN ({placeholders})
            AND wo.docstatus = 1
            GROUP BY wo.production_plan
        """
        
        results = frappe.db.sql(wo_status_query, plans, as_dict=True)
        
        # Dictionary formatına çevir
        status_map = {}
        for result in results:
            status_map[result['production_plan']] = result['work_order_status']
            
        # Eksik planlar için varsayılan durum
        for plan in plans:
            if plan not in status_map:
                status_map[plan] = 'Not Started'
                
        # Cache'e kaydet
        _cache_set(cache_key, status_map, ttl_seconds=300)
        
        return status_map
        
    except Exception as e:
        frappe.log_error(f"get_work_order_statuses hatası: {str(e)}")
        return {}

@frappe.whitelist()
def refresh_cache_background():
    """
    Background'da cache'i yenile - Cron job için
    """
    try:
        # Varsayılan filtrelerle cache'i yenile
        default_filters = validate_filters({})
        
        # Ana verileri background'da yükle
        planned, unplanned = get_optimized_data_v2(default_filters)
        
        # Cache'e kaydet
        cache_key = f"upp:planned-unplanned:{json.dumps(default_filters, sort_keys=True)}"
        result = {"planned": planned, "unplanned": unplanned}
        _cache_set(cache_key, result, ttl_seconds=int(CONSTANTS['CACHE_DURATION'] / 1000))
        
        frappe.logger().info(f"Background cache refresh tamamlandı: {len(planned)} planlanan, {len(unplanned)} planlanmamış")
        
        return {
            "success": True,
            "planned_count": len(planned),
            "unplanned_count": len(unplanned),
            "timestamp": time.time()
        }
        
    except Exception as e:
        frappe.log_error(f"Background cache refresh hatası: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_autocomplete_data(field: str, search: str) -> List[str]:
    """
    Autocomplete için veri çekme - Filtrelerde kullanılır
    """
    try:
        search_term = f"%{search}%"
        
        field_queries = {
            'bayi': """
                SELECT DISTINCT customer 
                FROM `tabSales Order` 
                WHERE customer LIKE %s 
                ORDER BY customer 
                LIMIT 10
            """,
            'musteri': """
                SELECT DISTINCT custom_end_customer 
                FROM `tabSales Order` 
                WHERE custom_end_customer LIKE %s 
                ORDER BY custom_end_customer 
                LIMIT 10
            """,
            'seri': """
                SELECT DISTINCT custom_serial 
                FROM `tabItem` 
                WHERE custom_serial LIKE %s 
                ORDER BY custom_serial 
                LIMIT 10
            """,
            'renk': """
                SELECT DISTINCT custom_color 
                FROM `tabItem` 
                WHERE custom_color LIKE %s 
                ORDER BY custom_color 
                LIMIT 10
            """
        }
        
        if field not in field_queries:
            return []
            
        result = frappe.db.sql(field_queries[field], [search_term], as_list=True)
        return [row[0] for row in result if row[0]]
        
    except Exception as e:
        frappe.log_error(f"Autocomplete Hatası: {str(e)}")
        return []

# Helper functions - Optimize edilmiş


@frappe.whitelist()
def get_opti_details(opti_no=None) -> Dict[str, Any]:
    """
    Opti numarasına göre detaylı bilgileri getirir.
    Modern ve optimize edilmiş - N+1 Query problemi çözüldü.
    """
    try:
        # Cache kontrolü (v2: sipariş bazında gruplanmış sonuç)
        cache_key = f"upp:opti:v2:{opti_no}"
        cached = _cache_get(cache_key, ttl_seconds=int(CONSTANTS['CACHE_DURATION'] / 1000))
        if cached:
            return cached

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
        
        # Her sipariş için detaylı bilgileri topla
        orders = []
        total_mtul = 0
        total_pvc = 0
        total_cam = 0
        
        for item in plan_items:
            # Sales Order bilgilerini al (cache'den)
            sales_order_data = sales_orders_data.get(item.sales_order, {})
            
            # Item bilgilerini al (cache'den)
            item_data = items_data.get(item.item_code, {})
            
            # MTÜL hesaplama
            mtul_value = 0
            item_group = item_data.get('item_group', '')
            
            if item_group == 'PVC AKSESUAR':
                mtul_value = CONSTANTS['DEFAULT_MTUL_PVC']
                total_pvc += item.planned_qty
                per_line_pvc = float(item.planned_qty or 0)
                per_line_cam = 0.0
            elif item_group == 'CAM AKSESUAR':
                mtul_value = CONSTANTS['DEFAULT_MTUL_CAM']
                total_cam += item.planned_qty
                per_line_pvc = 0.0
                per_line_cam = float(item.planned_qty or 0)
            else:
                mtul_value = item.custom_mtul_per_piece or 0
                # Ürün grubu genel sınıfları için adet dağılımı
                if item_group == 'PVC':
                    per_line_pvc = float(item.planned_qty or 0)
                    per_line_cam = 0.0
                    total_pvc += item.planned_qty
                elif item_group == 'Camlar':
                    per_line_cam = float(item.planned_qty or 0)
                    per_line_pvc = 0.0
                    total_cam += item.planned_qty
                else:
                    per_line_pvc = 0.0
                    per_line_cam = 0.0
            
            line_total_mtul = float(mtul_value) * float(item.planned_qty or 0)
            total_mtul += line_total_mtul
            
            orders.append({
                'sales_order': item.sales_order,
                'item_code': item.item_code,
                'planned_qty': item.planned_qty,
                'produced_qty': item.produced_qty,
                'serial': item.custom_serial or item_data.get('custom_serial', ''),
                'color': item.custom_color or item_data.get('custom_color', ''),
                'mtul_per_piece': mtul_value,
                # UI'nin beklediği alan adları (kolay tüketim için)
                'pvc_count': per_line_pvc,
                'cam_count': per_line_cam,
                'total_mtul': line_total_mtul,
                'bayi': sales_order_data.get('customer', ''),
                'musteri': sales_order_data.get('custom_end_customer', ''),
                'siparis_tarihi': sales_order_data.get('transaction_date'),
                'bitis_tarihi': sales_order_data.get('delivery_date'),
                'siparis_aciklama': sales_order_data.get('custom_remarks', ''),
                'seri': item.custom_serial or item_data.get('custom_serial', ''),
                'renk': item.custom_color or item_data.get('custom_color', ''),
                'customer': sales_order_data.get('customer', ''),
                'end_customer': sales_order_data.get('custom_end_customer', ''),
                'transaction_date': sales_order_data.get('transaction_date'),
                'delivery_date': sales_order_data.get('delivery_date'),
                'remarks': sales_order_data.get('custom_remarks', ''),
                'acil_durum': sales_order_data.get('custom_acil_durum', '')
            })
        
        # Aynı siparişe ait ürünleri tek satırda birleştir (uretim_planlama_takip mantığına benzer)
        grouped: Dict[str, Dict[str, Any]] = {}
        for row in orders:
            so = row['sales_order']
            if so not in grouped:
                grouped[so] = {
                    'sales_order': so,
                    'bayi': row.get('bayi', ''),
                    'musteri': row.get('musteri', ''),
                    'siparis_tarihi': row.get('siparis_tarihi'),
                    'bitis_tarihi': row.get('bitis_tarihi'),
                    'siparis_aciklama': row.get('siparis_aciklama', ''),
                    'seri_list': set(),
                    'renk_list': set(),
                    'pvc_count': 0.0,
                    'cam_count': 0.0,
                    'total_mtul': 0.0,
                    'item_count': 0,
                }
            g = grouped[so]
            if row.get('seri'):
                g['seri_list'].add(str(row.get('seri')))
            if row.get('renk'):
                g['renk_list'].add(str(row.get('renk')))
            g['pvc_count'] += float(row.get('pvc_count', 0) or 0)
            g['cam_count'] += float(row.get('cam_count', 0) or 0)
            g['total_mtul'] += float(row.get('total_mtul', 0) or 0)
            g['item_count'] += 1

        grouped_orders = []
        for so, g in grouped.items():
            grouped_orders.append({
                'sales_order': so,
                'bayi': g['bayi'],
                'musteri': g['musteri'],
                'siparis_tarihi': g['siparis_tarihi'],
                'bitis_tarihi': g['bitis_tarihi'],
                'siparis_aciklama': g['siparis_aciklama'],
                'seri': ', '.join(sorted(g['seri_list'])) if g['seri_list'] else '-',
                'renk': ', '.join(sorted(g['renk_list'])) if g['renk_list'] else '-',
                'pvc_count': g['pvc_count'],
                'cam_count': g['cam_count'],
                'total_mtul': g['total_mtul'],
                'toplam_mtul_m2': g['total_mtul'],
                'item_count': g['item_count'],
            })

        result = {
            'opti_no': opti_no,
            'production_plan': latest_plan.name,
            'status': latest_plan.status,
            'creation': latest_plan.creation,
            'modified': latest_plan.modified,
            'orders': grouped_orders,
            'total_mtul': total_mtul,
            'total_pvc': total_pvc,
            'total_cam': total_cam,
            'total_orders': len(grouped_orders)
        }
        
        # Cache'e kaydet
        _cache_set(cache_key, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"get_opti_details hatası: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def get_sales_order_details_v2(sales_order=None) -> Dict[str, Any]:
    """
    Sales Order için detaylı bilgileri getirir.
    Modern ve optimize edilmiş - N+1 Query problemi çözüldü.
    """
    try:
        
        # Cache kontrolü
        cache_key = f"upp:so:{sales_order}"
        cached = _cache_get(cache_key, ttl_seconds=int(CONSTANTS['CACHE_DURATION'] / 1000))
        if cached:
            return cached

        # Sales Order'ı getir
        so_data = frappe.get_doc("Sales Order", sales_order)
        if not so_data:
            return {"error": "Sales Order bulunamadı"}
        
        # Sales Order Item'ları getir
        so_items = frappe.get_all(
            "Sales Order Item",
            filters={"parent": sales_order},
            fields=[
                "item_code", "qty", "rate", "amount"
            ]
        )
        
        # Item kodlarını topla
        item_codes = list(set(item.item_code for item in so_items))
        
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
        
        # Her item için detaylı bilgileri topla
        items_detail = []
        total_mtul = 0
        total_pvc = 0
        total_cam = 0
        
        for item in so_items:
            item_data = items_data.get(item.item_code, {})
            
            # MTÜL hesaplama
            mtul_value = 0
            item_group = item_data.get('item_group', '')
            
            if item_group == 'PVC':
                mtul_value = item_data.get('custom_total_main_profiles_mtul', CONSTANTS['DEFAULT_MTUL_PVC'])
                total_pvc += item.qty
            elif item_group == 'Camlar':
                mtul_value = CONSTANTS['DEFAULT_MTUL_CAM']
                total_cam += item.qty
            else:
                # Diğer ürün grupları için
                mtul_value = 0
                if item_group == 'PVC AKSESUAR':
                    total_pvc += item.qty
                elif item_group == 'CAM AKSESUAR':
                    total_cam += item.qty
            
            total_mtul += mtul_value * item.qty
            
            items_detail.append({
                'item_code': item.item_code,
                'qty': item.qty,
                'rate': item.rate,
                'amount': item.amount,
                'serial': item_data.get('custom_serial', ''),
                'color': item_data.get('custom_color', ''),
                'mtul_per_piece': mtul_value,
                'item_group': item_group,
                'total_mtul': mtul_value * item.qty
            })
        
        # CAM M2 hesaplama (ortalama 0.95 m2/adet)
        total_cam_m2 = total_cam * 0.95
        
        result = {
            'sales_order': sales_order,
            'customer': so_data.customer,
            'customer_name': so_data.customer_name,
            'end_customer': so_data.custom_end_customer,
            'transaction_date': so_data.transaction_date,
            'delivery_date': so_data.delivery_date,
            'status': so_data.status,
            'workflow_state': so_data.workflow_state,
            'remarks': so_data.custom_remarks,
            'acil_durum': so_data.custom_acil_durum,
            'items': items_detail,
            'total_mtul': total_mtul,
            'total_pvc': total_pvc,
            'total_cam': total_cam,
            'total_cam_m2': total_cam_m2,
            'total_items': len(items_detail)
        }
        
        # Cache'e kaydet
        _cache_set(cache_key, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"get_sales_order_details_v2 hatası: {str(e)}")
        return {"error": str(e)}

def get_status_badge_for_takip(status: str) -> Dict[str, str]:
    """Status badge bilgilerini döndürür - Takip sayfasından kopyalandı"""
    status_map = {
        "Completed": {"class": "success", "label": "Tamamlandı"},
        "In Process": {"class": "warning", "label": "Devam Ediyor"}, 
        "Not Started": {"class": "secondary", "label": "Başlanmadı"},
        "Stopped": {"class": "danger", "label": "Durduruldu"},
        "Closed": {"class": "info", "label": "Kapatıldı"},
        "Draft": {"class": "light", "label": "Taslak"}
    }
    
    return status_map.get(status, {"class": "secondary", "label": status})

@frappe.whitelist()
def get_work_orders_for_sales_order(sales_order=None, production_plan=None) -> Dict[str, Any]:
    """
    Sales Order için Work Order'ları getirir - Takip sayfasındaki çalışan mantığa göre düzeltildi
    """
    try:
        # Cache kontrolü
        cache_key = f"upp:wo:v3:so:{sales_order}|pp:{production_plan}"
        cached = _cache_get(cache_key, ttl_seconds=int(CONSTANTS['CACHE_DURATION'] / 1000))
        if cached:
            return cached

        # Takip sayfasındaki çalışan mantığı kullan
        work_orders = []
        
        # Üretim planına göre filtreleme (takip sayfasındaki mantık)
        if production_plan:
            # Opti numarası ile Production Plan'ı bul
            production_plans = frappe.get_all(
                "Production Plan",
                filters={
                    "custom_opti_no": production_plan,
                    "docstatus": ["in", [0, 1]]
                },
                fields=["name"],
                limit=1
            )
            
            if production_plans:
                plan_name = production_plans[0].name
                # Sadece belirtilen üretim planına ait iş emirlerini getir - JOIN ile
                work_orders = frappe.db.sql("""
                    SELECT 
                        wo.name, wo.status, wo.production_item, wo.qty as qty, wo.produced_qty,
                        wo.planned_start_date, wo.planned_end_date, wo.sales_order,
                        wo.creation, wo.modified, wo.bom_no, wo.item_name, 
                        wo.custom_opti_no, wo.production_plan
                    FROM `tabWork Order` wo
                    INNER JOIN `tabProduction Plan Item` ppi ON wo.production_plan_item = ppi.name
                    INNER JOIN `tabProduction Plan` pp ON ppi.parent = pp.name
                    WHERE wo.sales_order = %s AND pp.name = %s
                    ORDER BY wo.creation DESC
                """, (sales_order, plan_name), as_dict=1)
            else:
                # Opti bulunamadıysa boş liste döndür
                work_orders = []
        else:
            # Tüm iş emirlerini getir (eski davranış)
            work_orders = frappe.get_all(
                "Work Order",
                filters={"sales_order": sales_order},
                fields=[
                    "name", "status", "planned_start_date", "planned_end_date",
                    "qty as qty", "produced_qty", "bom_no", "production_item",
                    "item_name", "custom_opti_no", "sales_order", "production_plan",
                    "creation", "modified", "production_item"
                ],
                order_by="creation desc"
            )
        
        # Her iş emri için ek bilgileri ekle (takip sayfasındaki mantık)
        for wo in work_orders:
            # Progress hesaplama
            produced_qty = float(wo.get("produced_qty", 0) or 0)
            planned_qty = float(wo.get("qty", 0) or 0)
            if planned_qty > 0:
                wo["progress_percentage"] = round((produced_qty / planned_qty) * 100, 2)
            else:
                wo["progress_percentage"] = 0
                
            wo["status_badge"] = get_status_badge_for_takip(wo.get("status", ""))
        
        result = {
            'sales_order': sales_order,
            'production_plan': production_plan,
            'work_orders': work_orders,
            'total_work_orders': len(work_orders)
        }
        
        # Cache'e kaydet
        _cache_set(cache_key, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"get_work_orders_for_sales_order hatası: {str(e)}")
        return {"error": str(e)}

def format_datetime_for_paneli(datetime_str: Any) -> Optional[str]:
    """
    Datetime formatını düzenler - Takip sayfasındaki gibi
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
        return str(datetime_str) if datetime_str else None


@frappe.whitelist()
def get_work_order_operations(work_order=None) -> Dict[str, Any]:
    """
    Work Order için operasyonları getirir - Takip sayfasındaki gibi.
    """
    try:
        # Cache kontrolü
        cache_key = f"upp:wo_ops:{work_order}"
        cached = _cache_get(cache_key, ttl_seconds=int(CONSTANTS['CACHE_DURATION'] / 1000))
        if cached:
            return cached

        # Work Order operasyonlarını getir - Takip sayfasındaki gibi
        operations = frappe.get_all(
            "Work Order Operation",
            filters={"parent": work_order},
            fields=[
                "name", "operation", "workstation", "status", "completed_qty",
                "planned_start_time", "planned_end_time", "actual_start_time", "actual_end_time",
                "description"
            ],
            order_by="idx"
        )
        
        # Her operasyon için tarih formatlarını düzenle ve gerçek tamamlanan miktarı hesapla
        for op in operations:
            # Job Card'lardan gerçek tamamlanan miktarı hesapla (artırımlı güncelleme için)
            op["completed_qty"] = get_real_completed_qty_from_job_cards(work_order, op.name)
            
            op["planned_start_formatted"] = format_datetime_for_paneli(op.planned_start_time)
            op["planned_end_formatted"] = format_datetime_for_paneli(op.planned_end_time)
            op["actual_start_formatted"] = format_datetime_for_paneli(op.actual_start_time)
            op["actual_end_formatted"] = format_datetime_for_paneli(op.actual_end_time)
        
        result = {
            'work_order': work_order,
            'operations': operations,
            'total_operations': len(operations)
        }
        
        # Cache'e kaydet
        _cache_set(cache_key, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"get_work_order_operations hatası: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def get_unplanned_data(filters=None) -> Dict[str, Any]:
    """
    Planlanmamış verileri getirir - Gruplama ile birlikte.
    """
    try:
        # JavaScript'ten gelen string filters'ı parse et
        if isinstance(filters, str):
            try:
                import json
                filters = json.loads(filters)
            except (json.JSONDecodeError, TypeError):
                filters = {}
        elif not filters:
            filters = {}
        
        
        # Cache kontrolü
        cache_key = f"upp:unplanned:{hash(str(filters))}"
        cached = _cache_get(cache_key, ttl_seconds=int(CONSTANTS['CACHE_DURATION'] / 1000))
        if cached:
            return cached

        # Planlanmamış verileri getir - Gruplama ile birlikte
        planned, unplanned = get_optimized_data_v2(filters)
        
        result = {"unplanned_orders": unplanned}
        
        # Cache'e kaydet
        _cache_set(cache_key, result)
        return result
        
    except Exception as e:
        frappe.log_error(f"get_unplanned_data hatası: {str(e)}")
        return {"error": str(e)}
