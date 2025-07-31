import frappe
import json
from datetime import datetime, timedelta

@frappe.whitelist()
def get_production_planning_data(filters=None):
    """
    Üretim planlama sayfası için optimize edilmiş veri çekme
    """
    try:
        filters = json.loads(filters) if isinstance(filters, str) else (filters or {})

        # Tüm verileri tek seferde çek
        planned, unplanned = get_optimized_data(filters)
        
        return {"planned": planned, "unplanned": unplanned}
    except Exception as e:
        frappe.log_error(f"Üretim Paneli Hatası: {str(e)}")
        return {"error": str(e)}

def get_optimized_data(filters):
    """
    Tek sorgu ile tüm verileri optimize edilmiş şekilde çek
    """
    limit = int(filters.get("limit") or 200)
    hafta_filter = filters.get("hafta")
    opti_no_filter = filters.get("opti_no")
    siparis_no_filter = filters.get("siparis_no")
    bayi_filter = filters.get("bayi")
    musteri_filter = filters.get("musteri")
    seri_filter = filters.get("seri")
    renk_filter = filters.get("renk")
    durum_filter = filters.get("acil_durum")
    siparis_durum_filter = filters.get("siparis_durum")
    
    # Tarih filtreleri
    today = frappe.utils.getdate()
    urgent_date = today + timedelta(days=7)
    
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
            i.custom_stok_türü as tip,
            i.custom_color as renk,
            WEEK(so.transaction_date) as hafta,
            COALESCE(so.custom_acil_durum, 0) as acil,  -- Manuel acil durumu
            so.total_qty as siparis_total_qty,
            i.item_group as urun_grubu,
            soi.qty as siparis_item_qty,
            i.custom_serial as seri,
            ppi.planned_start_date as planlanan_baslangic_tarihi,
            ppi.planned_qty * COALESCE(i.custom_total_main_profiles_mtul, 0) as toplam_mtul_m2,
            ppi.planned_qty as planlanan_miktar,
            so.custom_remarks as siparis_aciklama
            FROM `tabProduction Plan` pp
            INNER JOIN `tabProduction Plan Item` ppi ON pp.name = ppi.parent
            INNER JOIN `tabSales Order` so ON ppi.sales_order = so.name
            INNER JOIN `tabSales Order Item` soi ON ppi.sales_order_item = soi.name
            INNER JOIN `tabItem` i ON ppi.item_code = i.name
        WHERE pp.docstatus = 1 
        AND pp.status != 'Closed'
        AND ppi.planned_qty > 0
        AND i.item_group != 'All Item Groups'
    """
    
    # Filtreleri ekle
    where_conditions = []
    params = []
    
    if hafta_filter:
        where_conditions.append("WEEK(so.transaction_date) = %s")
        params.append(int(hafta_filter))
    
    if opti_no_filter:
        where_conditions.append("pp.custom_opti_no LIKE %s")
        params.append(f"%{opti_no_filter}%")
    
    if siparis_no_filter:
        where_conditions.append("so.name LIKE %s")
        params.append(f"%{siparis_no_filter}%")
    
    if bayi_filter:
        where_conditions.append("so.customer LIKE %s")
        params.append(f"%{bayi_filter}%")
    
    if musteri_filter:
        where_conditions.append("so.custom_end_customer LIKE %s")
        params.append(f"%{musteri_filter}%")
    
    if seri_filter:
        where_conditions.append("i.custom_serial LIKE %s")
        params.append(f"%{seri_filter}%")
    
    if renk_filter:
        where_conditions.append("i.custom_color LIKE %s")
        params.append(f"%{renk_filter}%")
    
    if durum_filter:
        if durum_filter == "ACİL":
            where_conditions.append("so.delivery_date <= %s")
            params.append(urgent_date.strftime('%Y-%m-%d'))
        elif durum_filter == "NORMAL":
            where_conditions.append("(so.delivery_date > %s OR so.delivery_date IS NULL)")
            params.append(urgent_date.strftime('%Y-%m-%d'))
    
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
            i.custom_stok_türü as tip,
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
            -- MLY dosyası kontrolü (custom_mly_list_uploaded alanından)
            COALESCE(so.custom_mly_list_uploaded, 0) as mly_dosyasi_var,
            -- PVC/Cam hesaplama (sipariş miktarı - planlanan miktarları düşerek)
            CASE 
                WHEN i.item_group = 'PVC' THEN (soi.qty - COALESCE(planned_qty.planned_qty, 0))
                ELSE 0 
            END as pvc_qty,
            CASE 
                WHEN i.item_group = 'Camlar' THEN (soi.qty - COALESCE(planned_qty.planned_qty, 0))
                ELSE 0 
            END as cam_qty,
            -- Kısmi planlama kontrolü
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
        WHERE so.docstatus IN (0, 1)  -- Taslak ve onaylanmış siparişler
        AND so.status NOT IN ('Closed', 'Cancelled')  -- Kapatılmamış ve iptal edilmemiş
        AND (soi.qty - COALESCE(planned_qty.planned_qty, 0)) > 0  -- Planlanmamış miktar var
        AND i.item_group IS NOT NULL  -- NULL olmayan ürün grupları
        AND i.item_group IN ('PVC', 'Camlar')  -- Sadece PVC ve Cam ürünleri
    """
    
    # Planlanmamış için filtreleri ekle
    unplanned_where_conditions = []
    unplanned_params = []
    
    if hafta_filter:
        unplanned_where_conditions.append("WEEK(so.transaction_date) = %s")
        unplanned_params.append(int(hafta_filter))
    
    if siparis_no_filter:
        unplanned_where_conditions.append("so.name LIKE %s")
        unplanned_params.append(f"%{siparis_no_filter}%")
    
    if bayi_filter:
        unplanned_where_conditions.append("so.customer LIKE %s")
        unplanned_params.append(f"%{bayi_filter}%")
    
    if musteri_filter:
        unplanned_where_conditions.append("so.custom_end_customer LIKE %s")
        unplanned_params.append(f"%{musteri_filter}%")
    
    if seri_filter:
        unplanned_where_conditions.append("i.custom_serial LIKE %s")
        unplanned_params.append(f"%{seri_filter}%")
    
    if renk_filter:
        unplanned_where_conditions.append("i.custom_color LIKE %s")
        unplanned_params.append(f"%{renk_filter}%")
    
    if durum_filter:
        if durum_filter == "ACİL":
            unplanned_where_conditions.append("so.delivery_date <= %s")
            unplanned_params.append(urgent_date.strftime('%Y-%m-%d'))
        elif durum_filter == "NORMAL":
            unplanned_where_conditions.append("(so.delivery_date > %s OR so.delivery_date IS NULL)")
            unplanned_params.append(urgent_date.strftime('%Y-%m-%d'))
    
    if siparis_durum_filter:
        unplanned_where_conditions.append("so.status = %s")
        unplanned_params.append(siparis_durum_filter)
    
    if unplanned_where_conditions:
        unplanned_query += " AND " + " AND ".join(unplanned_where_conditions)
    
    unplanned_query += f" ORDER BY so.delivery_date ASC LIMIT {limit}"
    
    unplanned_data = frappe.db.sql(unplanned_query, unplanned_params, as_dict=True)
    

    
    # Badge bilgilerini geçici olarak devre dışı bırak
    badges = {}
    
    # Verileri formatla ve PVC/Camlar sayısını hesapla
    planned_formatted = []
    pvc_cam_counts = {}
    processed_combinations = set()  # İşlenmiş kombinasyonları takip etmek için (sales_order + seri + renk)
    
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
        
        # İlk ürünün bilgilerini temel al
        first_item = group_data['items'][0]
        
        formatted_item = {
            'uretim_plani': first_item['uretim_plani'],
            'opti_no': first_item.get('opti_no'),
            'sales_order': sales_order,
            'item_code': f"{sales_order} ({len(group_data['items'])} ürün)",  # Kaç ürün olduğunu göster
            'adet': group_data['total_planned_qty'],  # Toplam planlanan miktar
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
            'durum_badges': badges.get(sales_order, []),
            'pvc_count': group_data['total_pvc'],
            'cam_count': group_data['total_cam'],
            'toplam_mtul_m2': group_data['total_mtul'],
            'planlanan_baslangic_tarihi': first_item.get('planlanan_baslangic_tarihi').strftime('%Y-%m-%d') if first_item.get('planlanan_baslangic_tarihi') else None
        }
        planned_formatted.append(formatted_item)
    
    # Planlanmamış verileri formatla ve PVC/Camlar sayısını hesapla
    unplanned_formatted = []
    unplanned_processed_combinations = set()  # İşlenmiş kombinasyonları takip etmek için
    
    # Önce tüm planlanmamış verileri grupla (sipariş + seri + renk bazında)
    unplanned_grouped_data = {}
    
    for item in unplanned_data:
        sales_order = item['sales_order']
        seri = item.get('seri', '')
        renk = item.get('renk', '')
        combination_key = f"{sales_order}_{seri}_{renk}"
        
        if combination_key not in unplanned_grouped_data:
            unplanned_grouped_data[combination_key] = {
                'sales_order': sales_order,
                'seri': seri,
                'renk': renk,
                'items': [],
                'total_pvc': 0,
                'total_cam': 0,
                'total_unplanned_qty': 0
            }
        
        # Bu ürünü gruba ekle
        unplanned_grouped_data[combination_key]['items'].append(item)
        
        # PVC/Cam hesapla - SQL'den gelen değerleri kullan (zaten doğru hesaplanmış)
        pvc_qty = float(item.get('pvc_qty', 0) or 0)
        cam_qty = float(item.get('cam_qty', 0) or 0)
        unplanned_qty = float(item.get('unplanned_qty', 0) or 0)
        
        unplanned_grouped_data[combination_key]['total_pvc'] += pvc_qty
        unplanned_grouped_data[combination_key]['total_cam'] += cam_qty
        unplanned_grouped_data[combination_key]['total_unplanned_qty'] += unplanned_qty
    
    # Gruplandırılmış planlanmamış verileri formatla
    for combination_key, group_data in unplanned_grouped_data.items():
        if combination_key in unplanned_processed_combinations:
            continue
            
        unplanned_processed_combinations.add(combination_key)
        
        # İlk ürünü temel al (sipariş bilgileri için)
        first_item = group_data['items'][0]
        
        # Gruplandırılmış planlanmamış verilerden formatlanmış veri oluştur
        sales_order = group_data['sales_order']
        seri = group_data['seri']
        renk = group_data['renk']
        
        # İlk ürünün bilgilerini temel al
        first_item = group_data['items'][0]
        
        formatted_item = {
            'sales_order': sales_order,
            'item_code': f"{sales_order} ({len(group_data['items'])} ürün)",  # Kaç ürün olduğunu göster
            'adet': group_data['total_unplanned_qty'],  # Toplam planlanmamış miktar
            'bayi': first_item['bayi'],
            'musteri': first_item['musteri'],
            'siparis_tarihi': first_item['siparis_tarihi'].strftime('%Y-%m-%d') if first_item['siparis_tarihi'] else None,
            'hafta': first_item['hafta'],
            'tip': first_item['tip'],
            'renk': renk or '-',
            'seri': seri or '-',
            'aciklama': first_item.get('siparis_aciklama') or f"{len(group_data['items'])} ürün grubu (planlanmamış)",
            'bitis_tarihi': first_item['bitis_tarihi'].strftime('%Y-%m-%d') if first_item['bitis_tarihi'] else None,
            'acil': bool(first_item['acil']),
            'durum_badges': badges.get(sales_order, []),
            'pvc_count': group_data['total_pvc'],
            'cam_count': group_data['total_cam'],
            'siparis_durumu': first_item.get('siparis_durumu', 'Draft'),
            'is_akisi_durumu': first_item.get('is_akisi_durumu', ''),
            'belge_durumu': first_item.get('belge_durumu', 0),
            'mly_dosyasi_var': any(item.get('mly_dosyasi_var', 0) for item in group_data['items']),
            'kismi_planlama': any(item.get('kismi_planlama', 0) for item in group_data['items'])
        }
        unplanned_formatted.append(formatted_item)
    
    return planned_formatted, unplanned_formatted

def get_badges_bulk(sales_orders):
    """
    Tüm siparişler için badge bilgilerini toplu olarak çek
    """
    if not sales_orders:
        return {}
    
    # Üretim başladı badge'i için (Work Order üzerinden)
    production_started = frappe.db.sql("""
        SELECT DISTINCT wo.sales_order 
        FROM `tabJob Card` jc
        INNER JOIN `tabWork Order` wo ON jc.work_order = wo.name
        WHERE wo.sales_order IN %s AND jc.docstatus = 1
    """, [tuple(sales_orders)], as_dict=True)
    
    # Teslim edildi badge'i için
    delivered = frappe.db.sql("""
        SELECT DISTINCT against_sales_order 
        FROM `tabDelivery Note Item` dni
        INNER JOIN `tabDelivery Note` dn ON dni.parent = dn.name
        WHERE dni.against_sales_order IN %s AND dn.docstatus = 1
    """, [tuple(sales_orders)], as_dict=True)
    
    # Badge'leri organize et
    badges = {}
    for so in sales_orders:
        so_badges = []
        
        # Üretim başladı
        if any(item['sales_order'] == so for item in production_started):
            so_badges.append({
                'label': 'Üretim Başladı',
                'class': 'badge-info'
            })
        
        # Teslim edildi
        if any(item['against_sales_order'] == so for item in delivered):
            so_badges.append({
                'label': 'Teslim Edildi',
                'class': 'badge-success'
            })
        
        if so_badges:
            badges[so] = so_badges
    
    return badges

def optimize_database_performance():
    """
    Veritabanı performansını optimize et
    """
    try:
        # Gerekli indexleri oluştur
        create_indexes()
        
        # Tablo istatistiklerini güncelle
        update_table_statistics()
        
        return {"status": "success", "message": "Veritabanı optimizasyonu tamamlandı"}
    except Exception as e:
        frappe.log_error(f"Veritabanı optimizasyon hatası: {str(e)}")
        return {"status": "error", "message": str(e)}

def create_indexes():
    """
    Gerekli indexleri oluştur
    """
    indexes = [
        ("tabSales Order", ["docstatus", "status", "transaction_date", "delivery_date"]),
        ("tabSales Order", ["customer", "custom_end_customer"]),
        ("tabProduction Plan", ["docstatus", "status"]),
        ("tabProduction Plan Item", ["parent", "sales_order"]),
        ("tabSales Order Item", ["parent", "item_code"]),
        ("tabItem", ["custom_stok_türü", "custom_color"]),
        ("tabJob Card", ["work_order", "docstatus"]),
        ("tabDelivery Note", ["docstatus"]),
        ("tabDelivery Note Item", ["against_sales_order"])
    ]
    
    for table, columns in indexes:
        for column in columns:
            create_index_if_not_exists(table, column)

def create_index_if_not_exists(table, column):
    """
    Index yoksa oluştur
    """
    try:
        index_name = f"idx_{table.replace('tab', '')}_{column}"
        frappe.db.sql(f"""
            CREATE INDEX IF NOT EXISTS {index_name} 
            ON `{table}` (`{column}`)
        """)
    except Exception as e:
        frappe.log_error(f"Index oluşturma hatası {table}.{column}: {str(e)}")

def update_table_statistics():
    """
    Tablo istatistiklerini güncelle
    """
    tables = [
        "tabSales Order", "tabSales Order Item", "tabProduction Plan", 
        "tabProduction Plan Item", "tabItem", "tabJob Card", 
        "tabDelivery Note", "tabDelivery Note Item"
    ]
    
    for table in tables:
        try:
            frappe.db.sql(f"ANALYZE TABLE `{table}`")
        except Exception as e:
            frappe.log_error(f"Tablo analizi hatası {table}: {str(e)}")

def check_performance():
    """
    Performans kontrolü yap
    """
    try:
        # Sorgu performansını test et
        start_time = datetime.now()
        
        result = get_production_planning_data('{}')
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        planned_count = len(result.get('planned', []))
        unplanned_count = len(result.get('unplanned', []))
        
        return {
            "execution_time": execution_time,
            "planned_count": planned_count,
            "unplanned_count": unplanned_count,
            "total_count": planned_count + unplanned_count,
            "performance_status": "good" if execution_time < 2 else "needs_optimization"
        }
    except Exception as e:
        return {"error": str(e)}

def get_performance_recommendations():
    """
    Performans önerilerini getir
    """
    recommendations = [
        "Veritabanı indexlerinin oluşturulduğundan emin olun",
        "Tablo istatistiklerini düzenli olarak güncelleyin",
        "Sorgu limitlerini kontrol edin",
        "Gereksiz JOIN'leri kaldırın",
        "WHERE koşullarını optimize edin"
    ]
    
    return recommendations

@frappe.whitelist()
def get_autocomplete_data(field, search):
    """
    Autocomplete için veri çekme
    """
    try:
        search_term = f"%{search}%"
        
        if field == 'bayi':
            result = frappe.db.sql("""
                SELECT DISTINCT customer 
                FROM `tabSales Order` 
                WHERE customer LIKE %s 
                ORDER BY customer 
                LIMIT 10
            """, [search_term], as_list=True)
            return [row[0] for row in result]
            
        elif field == 'musteri':
            result = frappe.db.sql("""
                SELECT DISTINCT custom_end_customer 
                FROM `tabSales Order` 
                WHERE custom_end_customer LIKE %s 
                ORDER BY custom_end_customer 
                LIMIT 10
            """, [search_term], as_list=True)
            return [row[0] for row in result if row[0]]
            
        elif field == 'seri':
            result = frappe.db.sql("""
                SELECT DISTINCT custom_serial 
                FROM `tabItem` 
                WHERE custom_serial LIKE %s 
                ORDER BY custom_serial 
                LIMIT 10
            """, [search_term], as_list=True)
            return [row[0] for row in result if row[0]]
            
        elif field == 'renk':
            result = frappe.db.sql("""
                SELECT DISTINCT custom_color 
                FROM `tabItem` 
                WHERE custom_color LIKE %s 
                ORDER BY custom_color 
                LIMIT 10
            """, [search_term], as_list=True)
            return [row[0] for row in result if row[0]]
            
        return []
        
    except Exception as e:
        frappe.log_error(f"Autocomplete Hatası: {str(e)}")
        return [] 