"""
Üretim Planlama Takip Paneli - Backend API
ERPNext v15 + Frappe

Bu dosya üretim planlama takip panelinin backend API fonksiyonlarını içerir.
Tamamen bağımsız çalışır, api.py ile karışmaz.
"""

import frappe
from frappe import _
from datetime import datetime, timedelta
import json


@frappe.whitelist()
def get_production_planning_data(filters=None):
    """
    Üretim planlama verilerini getirir.
    Sadece planlanan siparişler için optimize edilmiş.
    """
    try:
        if filters:
            filters = json.loads(filters) if isinstance(filters, str) else filters
        else:
            filters = {}
        
        # Filtreleri al
        opti_no_filter = filters.get('optiNo', '')
        siparis_no_filter = filters.get('siparisNo', '')
        bayi_filter = filters.get('bayi', '')
        musteri_filter = filters.get('musteri', '')
        seri_filter = filters.get('seri', '')
        renk_filter = filters.get('renk', '')
        uretim_tipi = filters.get('uretimTipi', 'tumu')
        durum_filter = filters.get('durum', 'tumu')
        show_completed = filters.get('showCompleted', True)
        
        # Optimize edilmiş ana sorgu - sadece gerekli alanlar
        planned_query = """
            SELECT 
                pp.custom_opti_no as opti_no,
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
                CASE 
                    WHEN i.item_group = 'Camlar' OR i.custom_stok_türü = 'Camlar'
                    THEN ppi.planned_qty * COALESCE(ppi.custom_mtul_per_piece, 1.745)
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
                END as cam_count
            FROM `tabProduction Plan` pp
            INNER JOIN `tabProduction Plan Item` ppi ON pp.name = ppi.parent
            INNER JOIN `tabSales Order` so ON ppi.sales_order = so.name
            INNER JOIN `tabItem` i ON ppi.item_code = i.name
            WHERE pp.docstatus = 1 
            AND pp.status != 'Closed'
            AND ppi.planned_qty > 0
            AND i.item_group != 'All Item Groups'
        """
        
        # Filtreleri ekle
        where_conditions = []
        params = []
        
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
        
        # Üretim tipi filtresi
        if uretim_tipi == 'pvc':
            where_conditions.append("i.item_group = 'PVC'")
        elif uretim_tipi == 'cam':
            where_conditions.append("(i.item_group = 'Camlar' OR i.custom_stok_türü = 'Camlar')")
        elif uretim_tipi == 'karisik':
            where_conditions.append("(i.item_group = 'PVC' OR i.item_group = 'Camlar' OR i.custom_stok_türü = 'Camlar')")
        
        # Durum filtresi
        if durum_filter == 'tamamlandi':
            where_conditions.append("pp.status = 'Completed'")
        elif durum_filter == 'devam_ediyor':
            where_conditions.append("pp.status = 'In Process'")
        elif durum_filter == 'planlanmamis':
            where_conditions.append("pp.status = 'Not Started'")
        
        # Tamamlananları göster/gizle
        if not show_completed:
            where_conditions.append("pp.status != 'Completed'")
        
        # WHERE koşullarını ekle
        if where_conditions:
            planned_query += " AND " + " AND ".join(where_conditions)
        
        # Limit ekle ve optimize edilmiş sıralama
        planned_query += " ORDER BY so.transaction_date DESC, pp.custom_opti_no LIMIT 500"
        
        # Sorguyu çalıştır
        planned_data = frappe.db.sql(planned_query, params, as_dict=True)
        
        return {
            "planned": planned_data,
            "total_planned": len(planned_data)
        }
        
    except Exception as e:
        frappe.log_error(f"Üretim Takip Paneli Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return {
            "planned": [],
            "error": str(e)
        }


@frappe.whitelist()
def get_opti_details_for_takip(opti_no):
    """
    Opti numarasına göre detaylı bilgileri getirir.
    Modern ve optimize edilmiş.
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
                mtul_value = item.planned_qty * (item.custom_mtul_per_piece or 1.745)
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
                "siparis_tarihi": str(sales_order.transaction_date) if sales_order.transaction_date else None,
                "bitis_tarihi": str(sales_order.delivery_date) if sales_order.delivery_date else None,
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
            "creation_date": str(latest_plan.creation) if latest_plan.creation else None,
            "modified_date": str(latest_plan.modified) if latest_plan.modified else None,
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
def get_sales_order_details_for_takip(sales_order):
    """
    Satış siparişi detaylarını getirir.
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
                mtul = item.qty * (item_doc.custom_mtul_per_piece or 1.745)
            else:
                mtul = 0
            
            total_mtul += mtul
        
        return {
            "sales_order": sales_order,
            "bayi": so_doc.customer,
            "musteri": so_doc.custom_end_customer,
            "siparis_tarihi": str(so_doc.transaction_date) if so_doc.transaction_date else None,
            "bitis_tarihi": str(so_doc.delivery_date) if so_doc.delivery_date else None,
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
def get_work_orders_for_takip(sales_order):
    """
    Satış siparişi için iş emirlerini getirir.
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
        
        return work_orders
            
    except Exception as e:
        frappe.log_error(f"İş Emri Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return {"error": str(e)}


@frappe.whitelist()
def get_autocomplete_data_for_takip(field, search):
    """
    Autocomplete için veri getirir.
    """
    try:
        if field == "opti_no":
            # Opti numaralarını getir
            data = frappe.db.sql("""
                SELECT DISTINCT custom_opti_no 
                FROM `tabProduction Plan` 
                WHERE custom_opti_no LIKE %s 
                AND docstatus = 1
                LIMIT 10
            """, f"%{search}%", as_list=True)
            return [row[0] for row in data]
        
        elif field == "bayi":
            # Bayileri getir
            data = frappe.db.sql("""
                SELECT DISTINCT customer 
                FROM `tabSales Order` 
                WHERE customer LIKE %s 
                AND docstatus = 1
                LIMIT 10
            """, f"%{search}%", as_list=True)
            return [row[0] for row in data]
        
        elif field == "musteri":
            # Müşterileri getir
            data = frappe.db.sql("""
                SELECT DISTINCT custom_end_customer 
                FROM `tabSales Order` 
                WHERE custom_end_customer LIKE %s 
                AND docstatus = 1
                LIMIT 10
            """, f"%{search}%", as_list=True)
            return [row[0] for row in data]
        
        elif field == "seri":
            # Serileri getir
            data = frappe.db.sql("""
                SELECT DISTINCT custom_serial 
                FROM `tabItem` 
                WHERE custom_serial LIKE %s 
                AND item_group IN ('PVC', 'Camlar')
                LIMIT 10
            """, f"%{search}%", as_list=True)
            return [row[0] for row in data]
        
        elif field == "renk":
            # Renkleri getir
            data = frappe.db.sql("""
                SELECT DISTINCT custom_color 
                FROM `tabItem` 
                WHERE custom_color LIKE %s 
                AND item_group IN ('PVC', 'Camlar')
                LIMIT 10
            """, f"%{search}%", as_list=True)
            return [row[0] for row in data]
        
        return []
        
    except Exception as e:
        frappe.log_error(f"Autocomplete Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return []


@frappe.whitelist()
def get_work_order_operations_for_takip(work_order_name):
    """
    İş emri operasyonlarını detaylı olarak getirir.
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
            
            # Durum badge'i oluştur
            op["status_badge"] = get_status_badge_for_takip(op.status)
            
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
def get_production_plan_details(plan_name):
    """
    Üretim planı detaylarını getirir.
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
            "planned_start_date": str(plan_doc.planned_start_date) if plan_doc.planned_start_date else None,
            "planned_end_date": str(plan_doc.planned_end_date) if plan_doc.planned_end_date else None,
            "actual_start_date": str(plan_doc.actual_start_date) if plan_doc.actual_start_date else None,
            "actual_end_date": str(plan_doc.actual_end_date) if plan_doc.actual_end_date else None,
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
def get_item_details_for_takip(item_code):
    """
    Ürün detaylarını getirir.
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


# Yardımcı fonksiyonlar
def format_date_for_takip(date_str):
    """
    Tarih formatını düzenler.
    """
    if not date_str:
        return None
    
    try:
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            date_obj = date_str
        
        return date_obj.strftime("%d.%m.%Y")
    except:
        return str(date_str)


def calculate_mtul_for_takip(qty, mtul_per_piece):
    """
    MTÜL hesaplama fonksiyonu.
    """
    try:
        return float(qty) * float(mtul_per_piece)
    except:
        return 0.0


def get_status_badge_for_takip(status):
    """
    Durum badge'i oluşturur.
    """
    status_map = {
        "Completed": "success",
        "In Process": "warning", 
        "Not Started": "secondary",
        "Stopped": "danger",
        "Closed": "info"
    }
    
    badge_class = status_map.get(status, "secondary")
    return f'<span class="badge badge-{badge_class}">{status}</span>'


def check_urgent_delivery_for_takip(delivery_date):
    """
    Acil teslimat kontrolü.
    """
    if not delivery_date:
        return False
    
    try:
        if isinstance(delivery_date, str):
            delivery = datetime.strptime(delivery_date, "%Y-%m-%d")
        else:
            delivery = delivery_date
        
        today = datetime.now()
        return delivery.date() < today.date()
    except:
        return False 


def format_datetime_for_takip(datetime_str):
    """
    Datetime formatını düzenler.
    """
    if not datetime_str:
        return None
    
    try:
        if isinstance(datetime_str, str):
            datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        else:
            datetime_obj = datetime_str
        
        return datetime_obj.strftime("%d.%m.%Y %H:%M")
    except:
        return str(datetime_str)


@frappe.whitelist()
def update_work_order_status(work_order_name, new_status):
    """
    İş emri durumunu günceller.
    """
    try:
        # İş emri dokümanını al
        work_order = frappe.get_doc("Work Order", work_order_name)
        
        # Durumu güncelle
        work_order.status = new_status
        
        # Açıklama ekle
        work_order.custom_remarks = f"Durum {work_order.status} olarak güncellendi - {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        # Kaydet
        work_order.save()
        
        return {
            "success": True,
            "message": f"İş emri durumu başarıyla güncellendi: {new_status}"
        }
        
    except Exception as e:
        frappe.log_error(f"İş Emri Durum Güncelleme Hatası: {str(e)}", "Uretim Planlama Takip Paneli")
        return {
            "success": False,
            "error": str(e)
        } 