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

# Frappe imports
import frappe
from frappe import _
from frappe.utils import get_datetime, getdate, add_days

# Third party imports (conditional)
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

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
    'DEFAULT_LIMIT': 500,
    'CACHE_DURATION': 30000,  # 30 saniye
    'MAX_RETRIES': 3,
    'DEFAULT_MTUL_CAM': 1.745,
    'DEFAULT_MTUL_PVC': 11.35,
    'MAX_QUERY_LIMIT': 1000
}

def validate_filters(filters: Dict) -> Dict:
    """Filter validation ve sanitization"""
    validated = {}
    if filters.get("limit"):
        validated["limit"] = min(int(filters["limit"]), CONSTANTS['MAX_QUERY_LIMIT'])
    else:
        validated["limit"] = CONSTANTS['DEFAULT_LIMIT']
    
    # String filtreleri sanitize et
    string_filters = ['hafta', 'opti_no', 'siparis_no', 'bayi', 'musteri', 'seri', 'renk', 'durum', 'workflow_state', 'tip']
    for filter_name in string_filters:
        if filters.get(filter_name):
            validated[filter_name] = str(filters[filter_name]).strip()
    
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

def add_business_days(start_date, business_days):
    """
    Verilen tarihe iş günü sayısı ekler (hafta sonları hariç)
    """
    from datetime import timedelta
    
    if not start_date:
        return start_date
    
    current_date = start_date
    added_days = 0
    
    while added_days < business_days:
        current_date += timedelta(days=1)
        # Hafta sonu kontrolü (0=Monday, 6=Sunday)
        if current_date.weekday() < 5:  # 0-4 = Monday to Friday
            added_days += 1
    
    return current_date

@frappe.whitelist()
def get_production_planning_data(filters: Optional[Union[str, Dict]] = None) -> Dict[str, Any]:
    """
    Üretim planlama sayfası için optimize edilmiş veri çekme
    """
    try:
        filters = json.loads(filters) if isinstance(filters, str) else (filters or {})
        filters = validate_filters(filters)

        # Tüm verileri tek seferde çek
        planned, unplanned = get_optimized_data(filters)
        
        result = {"planned": planned, "unplanned": unplanned}
        return result
    except Exception as e:
        frappe.log_error(f"Üretim Paneli Hatası: {str(e)}")
        return {"error": str(e), "planned": [], "unplanned": []}

def get_optimized_data(filters: Dict) -> tuple[List[Dict], List[Dict]]:
    """
    Tek sorgu ile tüm verileri optimize edilmiş şekilde çek
    """
    try:
        limit = filters.get("limit", CONSTANTS['DEFAULT_LIMIT'])
        
        # Planlanan siparişler için optimize edilmiş sorgu
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
                CASE 
                    WHEN i.item_group = 'Camlar' OR i.custom_stok_türü = 'Camlar'
                    THEN ppi.planned_qty * COALESCE(ppi.custom_mtul_per_piece, %s)
                    ELSE ppi.planned_qty * COALESCE(i.custom_total_main_profiles_mtul, 0)
                END as toplam_mtul_m2,
                ppi.planned_qty as planlanan_miktar,
                COALESCE(so.custom_remarks, '') as siparis_aciklama,
                CASE 
                    WHEN wo_stats.total_wo = 0 THEN 'Not Started'
                    WHEN wo_stats.completed_wo = wo_stats.total_wo THEN 'Completed'
                    WHEN wo_stats.in_process_wo > 0 THEN 'In Process'
                    ELSE 'Not Started'
                END as work_order_status
            FROM `tabProduction Plan` pp
            INNER JOIN `tabProduction Plan Item` ppi ON pp.name = ppi.parent
            INNER JOIN `tabSales Order` so ON ppi.sales_order = so.name
            INNER JOIN `tabSales Order Item` soi ON ppi.sales_order_item = soi.name
            INNER JOIN `tabItem` i ON ppi.item_code = i.name
            LEFT JOIN (
                SELECT 
                    wo.production_plan,
                    COUNT(*) as total_wo,
                    SUM(CASE WHEN wo.status = 'Completed' THEN 1 ELSE 0 END) as completed_wo,
                    SUM(CASE WHEN wo.status IN ('In Process', 'Completed') THEN 1 ELSE 0 END) as in_process_wo
                FROM `tabWork Order` wo
                WHERE wo.docstatus = 1
                GROUP BY wo.production_plan
            ) wo_stats ON wo_stats.production_plan = pp.name
            WHERE pp.docstatus = 1 
            AND pp.status != 'Closed'
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
        
        planned_query += f" ORDER BY so.delivery_date ASC LIMIT {limit}"
        
        planned_data = frappe.db.sql(planned_query, params, as_dict=True)
        
        # Planlanmamış siparişler için optimize edilmiş sorgu
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
                    CASE WHEN EXISTS (
                        SELECT 1 FROM `tabProduction Plan Item` ppi2
                        INNER JOIN `tabProduction Plan` pp2 ON ppi2.parent = pp2.name
                        INNER JOIN `tabSales Order Item` soi2 ON ppi2.sales_order_item = soi2.name
                        INNER JOIN `tabItem` i2 ON soi2.item_code = i2.name
                        WHERE pp2.docstatus = 1 AND pp2.status != 'Closed'
                        AND soi2.parent = so.name
                        AND (i2.custom_serial != i.custom_serial OR i2.custom_color != i.custom_color)
                    ) THEN 1 ELSE 0 END as kismi_planlama
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
        
        unplanned_query += " ORDER BY so.delivery_date ASC LIMIT 2000"
        
        unplanned_data = frappe.db.sql(unplanned_query, unplanned_params, as_dict=True)
        
        # Verileri formatla
        planned_formatted = format_planned_data(planned_data)
        unplanned_formatted = format_unplanned_data(unplanned_data)
        
        return planned_formatted, unplanned_formatted
        
    except Exception as e:
        frappe.log_error(f"get_optimized_data hatası: {str(e)}")
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
            urun_grubu = item['urun_grubu']
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
            
            # Gruplandırılmış verilerden formatlanmış veri oluştur
            sales_order = group_data['sales_order']
            seri = group_data['seri']
            renk = group_data['renk']
            
            # İş emirlerinin durumunu kontrol et
            work_order_status = first_item.get('work_order_status', 'Not Started')
            plan_status = 'Completed' if work_order_status == 'Completed' else first_item.get('plan_status', 'Not Started')
            
            # Teslim tarihi hesaplama: Başlangıç tarihi + 4 iş günü
            baslangic_tarihi = first_item.get('planlanan_baslangic_tarihi')
            hesaplanan_teslim_tarihi = None
            if baslangic_tarihi:
                hesaplanan_teslim_tarihi = add_business_days(baslangic_tarihi, 4)
            
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
                'bitis_tarihi': hesaplanan_teslim_tarihi.strftime('%Y-%m-%d') if hesaplanan_teslim_tarihi else None,
                'acil': bool(first_item['acil']),
                'durum_badges': [],  # Badge logic kaldırıldı - performans için
                'pvc_count': group_data['total_pvc'],
                'cam_count': group_data['total_cam'],
                'toplam_mtul_m2': group_data['total_mtul'],
                'planlanan_baslangic_tarihi': first_item.get('planlanan_baslangic_tarihi').strftime('%Y-%m-%d') if first_item.get('planlanan_baslangic_tarihi') else None,
                'plan_status': plan_status
            }
            planned_formatted.append(formatted_item)
        
        return planned_formatted
        
    except Exception as e:
        frappe.log_error(f"format_planned_data hatası: {str(e)}")
        return []

def format_unplanned_data(unplanned_data: List[Dict]) -> List[Dict]:
    """
    Planlanmamış verileri formatla - PVC ve CAM için AYRI SATIRLAR oluştur
    HER SİPARİŞ PVC ise bir satır, CAM ise ayrı bir satır olacak
    """
    try:
        if not unplanned_data:
            return []
        
        # Sipariş + ürün tipine göre grupla (PVC/CAM ayrı ayrı)
        product_groups = {}
        
        for item in unplanned_data:
            sales_order = item['sales_order']
            item_group = item.get('urun_grubu', 'Other')
            
            # PVC mi CAM mı? (hem item_group hem custom_stok_türü kontrol et)
            stok_turu = item.get('tip', '')
            if item_group == 'PVC' or stok_turu == 'PVC':
                product_type = 'PVC'
            elif item_group == 'Camlar' or stok_turu == 'Camlar':
                product_type = 'CAM'
            else:
                product_type = 'OTHER'
            
            # SADECE PVC veya CAM olan ürünleri kabul et
            if product_type == 'OTHER':
                continue
                
            # Unique key: sipariş + ürün tipi
            group_key = f"{sales_order}_{product_type}"
            
            # İlk kez görülen grup için kayıt oluştur
            if group_key not in product_groups:
                product_groups[group_key] = {
                    'sales_order': sales_order,
                    'product_type': product_type,
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
                    'total_qty': 0,
                    'total_mtul': 0,
                    'seri_list': set(),
                    'renk_list': set()
                }
            
            # Miktarları topla (sadece ilgili ürün tipine göre)
            group = product_groups[group_key]
            if product_type == 'PVC':
                group['total_qty'] += float(item.get('pvc_qty', 0) or 0)
            elif product_type == 'CAM':
                group['total_qty'] += float(item.get('cam_qty', 0) or 0)
            
            group['total_mtul'] += float(item.get('total_mtul', 0) or 0)
            
            # Seri ve renkleri topla
            if item.get('seri'):
                group['seri_list'].add(str(item['seri']))
            if item.get('renk'):
                group['renk_list'].add(str(item['renk']))
        
        # Formatlanmış listeye çevir - Her grup bir satır olacak
        unplanned_formatted = []
        for group_key, group in product_groups.items():
            # Set'leri virgülle ayrılmış string'e çevir
            seri_str = ', '.join(sorted(group['seri_list'])) if group['seri_list'] else '-'
            renk_str = ', '.join(sorted(group['renk_list'])) if group['renk_list'] else '-'
            
            # Planlanmamış veriler için teslim tarihi hesaplama: Sipariş tarihi + 4 iş günü
            siparis_tarihi = group['siparis_tarihi']
            hesaplanan_teslim_tarihi = None
            if siparis_tarihi:
                hesaplanan_teslim_tarihi = add_business_days(siparis_tarihi, 4)
            
            formatted_item = {
                'sales_order': group['sales_order'],
                'item_code': f"{group['sales_order']}_{group['product_type']}",
                'bayi': group['bayi'],
                'musteri': group['musteri'],
                'siparis_tarihi': group['siparis_tarihi'].strftime('%Y-%m-%d') if group['siparis_tarihi'] else None,
                'bitis_tarihi': hesaplanan_teslim_tarihi.strftime('%Y-%m-%d') if hesaplanan_teslim_tarihi else None,
                'hafta': group['hafta'],
                'seri': seri_str,
                'renk': renk_str,
                'aciklama': group['aciklama'],
                'acil': group['acil'],
                'product_type': group['product_type'],
                # PVC satırında sadece PVC count, CAM satırında sadece CAM count
                'pvc_count': group['total_qty'] if group['product_type'] == 'PVC' else 0,
                'cam_count': group['total_qty'] if group['product_type'] == 'CAM' else 0,
                'total_mtul': group['total_mtul'],
                'siparis_durumu': group['siparis_durumu'],
                'is_akisi_durumu': group['is_akisi_durumu'],
                'workflow_state': group['workflow_state'],
                'belge_durumu': group['belge_durumu'],
                'mly_dosyani_var': group['mly_dosyasi_var'],
                'kismi_planlama': group['kismi_planlama']
            }
            unplanned_formatted.append(formatted_item)
        
        # Sipariş numarasına göre sırala
        unplanned_formatted.sort(key=lambda x: (x['sales_order'], x['product_type']))
        
        return unplanned_formatted
        
    except Exception as e:
        frappe.log_error(f"format_unplanned_data hatası: {str(e)}")
        return []

@frappe.whitelist()
def get_unplanned_data(filters: Optional[Union[str, Dict]] = None) -> Dict[str, Any]:
    """
    Sadece "Onaylandı" durumundaki planlanmamış siparişleri getirir
    """
    try:
        filters = json.loads(filters) if isinstance(filters, str) else (filters or {})
        filters = validate_filters(filters)
        
        # Zorla sadece "Onaylandı" durumundaki siparişleri getir
        filters["workflow_state"] = "Onaylandı"
        
        # Sadece planlanmamış verileri çek
        _, unplanned = get_optimized_data(filters)
        
        return {"unplanned": unplanned, "error": None}
    except Exception as e:
        frappe.log_error(f"get_unplanned_data hatası: {str(e)}")
        return {"error": str(e), "unplanned": []}

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

@frappe.whitelist()
def get_sales_order_details_v2(order_no: str) -> Dict[str, Any]:
    """
    Satış siparişi detaylarını döndürür - OPTIMIZE EDİLMİŞ VERSİYON
    N+1 Query problemi çözüldü
    """
    try:
        # Sales Order'ı bir kerede çek
        sales_order = frappe.get_doc("Sales Order", order_no)
        
        # Tüm item kodlarını topla
        item_codes = [item.item_code for item in sales_order.items]
        
        # Tüm item verilerini tek seferde çek - N+1 Query çözümü
        items_data = {}
        if item_codes:
            items_query = """
                SELECT 
                    name, item_group, custom_amount_per_piece, 
                    custom_serial, custom_color
                FROM `tabItem` 
                WHERE name IN ({})
            """.format(','.join(['%s'] * len(item_codes)))
            
            items_result = frappe.db.sql(items_query, item_codes, as_dict=True)
            items_data = {item.name: item for item in items_result}
        
        # PVC ve Cam sayılarını hesapla
        pvc_qty = 0
        cam_qty = 0
        total_mtul = 0
        seri_list = []
        renk_list = []
        
        for item in sales_order.items:
            item_data = items_data.get(item.item_code, {})
            item_group = item_data.get('item_group', '')
            
            # Item group'a göre PVC/Cam tespiti
            if item_group in ["Profiller", "PVC"] or "PVC" in item_group or "profil" in item_group.lower():
                pvc_qty += item.qty
            elif item_group in ["Camlar", "CAM"] or "cam" in item_group.lower():
                cam_qty += item.qty
            
            # MTÜL hesapla
            custom_amount_per_piece = item_data.get('custom_amount_per_piece', 0) or 0
            if custom_amount_per_piece:
                total_mtul += item.qty * custom_amount_per_piece
            else:
                # Fallback: conversion_factor kullan
                conversion_factor = getattr(item, 'conversion_factor', 0) or 1
                total_mtul += item.qty * conversion_factor
            
            # Seri ve renk bilgilerini topla
            custom_serial = item_data.get('custom_serial', '')
            custom_color = item_data.get('custom_color', '')
            
            if custom_serial and custom_serial.strip() and custom_serial not in seri_list:
                seri_list.append(custom_serial.strip())
            if custom_color and custom_color.strip() and custom_color not in renk_list:
                renk_list.append(custom_color.strip())
        
        # Seri ve renk bilgilerini birleştir
        seri_text = ", ".join(seri_list) if seri_list else getattr(sales_order, 'custom_seri', '')
        renk_text = ", ".join(renk_list) if renk_list else getattr(sales_order, 'custom_renk', '')
        
        # Teslim tarihi hesaplama: Sipariş tarihi + 4 iş günü
        siparis_tarihi = sales_order.transaction_date
        hesaplanan_teslim_tarihi = None
        if siparis_tarihi:
            hesaplanan_teslim_tarihi = add_business_days(siparis_tarihi, 4)
        
        return {
            "sales_order": sales_order.name,
            "bayi": sales_order.customer,
            "musteri": sales_order.custom_end_customer,
            "siparis_tarihi": sales_order.transaction_date,
            "bitis_tarihi": hesaplanan_teslim_tarihi,
            "durum": sales_order.status,
            "workflow_state": getattr(sales_order, 'workflow_state', ''),
            "custom_acil_durum": getattr(sales_order, 'custom_acil_durum', 0),
            "seri": seri_text,
            "renk": renk_text,
            "seri_list": seri_list,
            "renk_list": renk_list,
            "pvc_qty": pvc_qty,
            "cam_qty": cam_qty,
            "total_mtul": total_mtul,
            "aciklama": getattr(sales_order, 'custom_remarks', '') or ""
        }
    except Exception as e:
        frappe.log_error(f"Satış Siparişi Detayları Hatası: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def get_work_orders_for_sales_order(sales_order: Union[str, Dict]) -> List[Dict]:
    """
    Satış siparişi için iş emirlerini getir
    """
    try:
        # Parametre handling
        if isinstance(sales_order, dict):
            sales_order = sales_order.get('sales_order', '')
        elif isinstance(sales_order, str) and sales_order.startswith('{'):
            try:
                sales_order = json.loads(sales_order).get('sales_order', '')
            except:
                pass
        
        # Satış siparişinin varlığını kontrol et
        if not frappe.db.exists("Sales Order", sales_order):
            return []
        
        # İş emirlerini optimize edilmiş sorgu ile al
        work_orders = frappe.db.sql("""
            SELECT 
                name, status, production_item, qty, produced_qty,
                planned_start_date, planned_end_date, sales_order,
                creation, modified
            FROM `tabWork Order`
            WHERE sales_order = %s
            ORDER BY creation DESC
        """, (sales_order,), as_dict=1)
        
        # Her iş emri için progress ve status badge ekle
        for wo in work_orders:
            wo["progress_percentage"] = get_completion_percentage(
                wo.get("produced_qty", 0), 
                wo.get("qty", 0)
            )
            wo["status_badge"] = get_status_badge(wo.get("status", ""))
            
        return work_orders
        
    except Exception as e:
        frappe.log_error(f"Satış Siparişi İş Emirleri Hatası: {str(e)}")
        return []

@frappe.whitelist()
def get_work_order_operations(work_order: str) -> List[Dict]:
    """
    İş emri için tüm operasyonları ve detaylarını getir
    """
    try:
        if not work_order:
            return []
        
        # İş emri operasyonlarını al
        operations = frappe.db.sql("""
            SELECT 
                name, operation, workstation, status, completed_qty,
                planned_start_time, planned_end_time, actual_start_time, 
                actual_end_time, description, time_in_mins as time_required
            FROM `tabWork Order Operation`
            WHERE parent = %s
            ORDER BY idx
        """, (work_order,), as_dict=1)
        
        # Eğer operasyon yoksa BOM'dan al
        if not operations:
            work_order_doc = frappe.get_doc("Work Order", work_order)
            bom_no = work_order_doc.bom_no
            
            if bom_no:
                bom_operations = frappe.db.sql("""
                    SELECT 
                        operation, workstation, description, time_in_mins
                    FROM `tabBOM Operation`
                    WHERE parent = %s
                    ORDER BY idx
                """, (bom_no,), as_dict=1)
                
                # BOM operasyonlarını formatla
                for i, bom_op in enumerate(bom_operations):
                    operations.append({
                        "name": f"BOM-OP-{i+1:03d}",
                        "operation": bom_op.operation,
                        "workstation": bom_op.workstation,
                        "status": "Not Started",
                        "completed_qty": 0,
                        "planned_start_time": None,
                        "planned_end_time": None,
                        "actual_start_time": None,
                        "actual_end_time": None,
                        "description": bom_op.description,
                        "time_required": bom_op.time_in_mins
                    })
        
        # Job Card'ları toplu olarak çek - Optimize edilmiş
        job_cards = frappe.db.sql("""
            SELECT 
                name, operation, for_quantity, status, total_completed_qty,
                actual_start_date, actual_end_date, started_time
            FROM `tabJob Card`
            WHERE work_order = %s
        """, (work_order,), as_dict=1)
        
        # Operasyonları Job Card'larla eşleştir
        job_cards_by_operation = {}
        for job_card in job_cards:
            op_name = job_card.operation
            if op_name not in job_cards_by_operation:
                job_cards_by_operation[op_name] = []
            job_cards_by_operation[op_name].append(job_card)
        
        # Operasyonları güncelle
        for operation in operations:
            operation["job_cards"] = job_cards_by_operation.get(operation.operation, [])
            
            # Job Card verilerini operasyona yansıt
            for job_card in operation["job_cards"]:
                if job_card.status:
                    operation["status"] = job_card.status
                if job_card.total_completed_qty:
                    operation["completed_qty"] = job_card.total_completed_qty
                if job_card.actual_start_date:
                    operation["actual_start_time"] = job_card.actual_start_date
                if job_card.actual_end_date:
                    operation["actual_end_time"] = job_card.actual_end_date
        
        return operations
        
    except Exception as e:
        frappe.log_error(f"İş Emri Operasyon Hatası: {str(e)}")
        return []

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
        
        # Siparişleri işle
        orders = []
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
            
            # Teslim tarihi hesaplama: Üretim planı oluşturma tarihi + 4 iş günü
            plan_creation_date = latest_plan.get('creation')
            hesaplanan_teslim_tarihi = None
            if plan_creation_date:
                hesaplanan_teslim_tarihi = add_business_days(plan_creation_date, 4)
            
            order_info = {
                "sales_order": item.sales_order,
                "bayi": sales_order_data.get('customer', ''),
                "musteri": sales_order_data.get('custom_end_customer', ''),
                "siparis_tarihi": str(sales_order_data.get('transaction_date', '')) if sales_order_data.get('transaction_date') else None,
                "bitis_tarihi": hesaplanan_teslim_tarihi.strftime('%Y-%m-%d') if hesaplanan_teslim_tarihi else None,
                "seri": item.custom_serial or item_data.get('custom_serial', ''),
                "renk": item.custom_color or item_data.get('custom_color', ''),
                "pvc_qty": item.planned_qty if item_group == "PVC" else 0,
                "cam_qty": item.planned_qty if item_group == "Camlar" else 0,
                "total_mtul": mtul_value,
                "uretim_plani_durumu": latest_plan.status,
                "siparis_aciklama": sales_order_data.get('custom_remarks', '') or "",
                "is_urgent": sales_order_data.get('custom_acil_durum', False) or False
            }
            
            orders.append(order_info)
        
        # Progress hesaplama - Modern yaklaşım
        progress_data = calculate_progress_data(plan_items)
        
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
        plan_status_badge = get_status_badge(latest_plan.status)
        
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

# Helper functions - Optimize edilmiş
def get_status_color(status: str) -> str:
    """Durum rengini döndürür"""
    status_colors = {
        'Draft': 'default',
        'Not Started': 'warning', 
        'In Process': 'info',
        'Completed': 'success',
        'Stopped': 'danger',
        'Cancelled': 'danger'
    }
    return status_colors.get(status, 'default')

def get_completion_percentage(produced_qty: float, planned_qty: float) -> float:
    """Tamamlanma yüzdesini hesaplar"""
    if not planned_qty or planned_qty == 0:
        return 0
    return round((float(produced_qty) / float(planned_qty)) * 100, 2)

def get_status_badge(status: str) -> Dict[str, str]:
    """Status badge bilgilerini döndürür - Modern yaklaşım"""
    status_map = {
        "Completed": {"class": "success", "label": "Tamamlandı"},
        "In Process": {"class": "warning", "label": "Devam Ediyor"}, 
        "Not Started": {"class": "secondary", "label": "Başlanmadı"},
        "Stopped": {"class": "danger", "label": "Durduruldu"},
        "Closed": {"class": "info", "label": "Kapatıldı"},
        "Draft": {"class": "light", "label": "Taslak"}
    }
    
    return status_map.get(status, {"class": "secondary", "label": status})

def calculate_progress_data(items: List[Dict]) -> Dict[str, Any]:
    """İlerleme verilerini hesaplar - Toplu hesaplama"""
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
