import frappe
from frappe import _

def optimize_database_performance():
    """
    Üretim planlama sayfası için veritabanı performansını optimize eder
    """
    try:
        # Gerekli indeksleri kontrol et ve ekle
        create_indexes()
        
        # İstatistikleri güncelle
        update_table_statistics()
        
        frappe.msgprint("Veritabanı performans optimizasyonu tamamlandı!", indicator="green")
        
    except Exception as e:
        frappe.log_error(f"Performans optimizasyonu hatası: {str(e)}")
        frappe.msgprint(f"Optimizasyon hatası: {str(e)}", indicator="red")

def create_indexes():
    """
    Performans için gerekli indeksleri oluştur
    """
    indexes_to_create = [
        # Production Plan indeksleri
        {
            "table": "tabProduction Plan",
            "index_name": "idx_production_plan_status",
            "columns": ["docstatus", "status"]
        },
        {
            "table": "tabProduction Plan Item", 
            "index_name": "idx_production_plan_item_parent",
            "columns": ["parent"]
        },
        {
            "table": "tabProduction Plan Item",
            "index_name": "idx_production_plan_item_sales_order", 
            "columns": ["sales_order"]
        },
        
        # Sales Order indeksleri
        {
            "table": "tabSales Order",
            "index_name": "idx_sales_order_status_date",
            "columns": ["docstatus", "status", "transaction_date"]
        },
        {
            "table": "tabSales Order",
            "index_name": "idx_sales_order_delivery_date",
            "columns": ["delivery_date"]
        },
        {
            "table": "tabSales Order",
            "index_name": "idx_sales_order_customer",
            "columns": ["customer"]
        },
        
        # Sales Order Item indeksleri
        {
            "table": "tabSales Order Item",
            "index_name": "idx_sales_order_item_parent",
            "columns": ["parent"]
        },
        
        # Work Order indeksleri
        {
            "table": "tabWork Order",
            "index_name": "idx_work_order_sales_order",
            "columns": ["sales_order", "docstatus"]
        },
        
        # Delivery Note Item indeksleri
        {
            "table": "tabDelivery Note Item",
            "index_name": "idx_delivery_note_item_sales_order",
            "columns": ["against_sales_order"]
        }
    ]
    
    for index_info in indexes_to_create:
        create_index_if_not_exists(index_info)

def create_index_if_not_exists(index_info):
    """
    İndeks yoksa oluştur
    """
    try:
        table = index_info["table"]
        index_name = index_info["index_name"]
        columns = index_info["columns"]
        
        # İndeksin var olup olmadığını kontrol et
        existing_indexes = frappe.db.sql(f"""
            SHOW INDEX FROM {table} 
            WHERE Key_name = '{index_name}'
        """, as_dict=True)
        
        if not existing_indexes:
            # İndeksi oluştur
            columns_str = ", ".join(columns)
            frappe.db.sql(f"""
                CREATE INDEX {index_name} ON {table} ({columns_str})
            """)
            frappe.db.commit()
            print(f"İndeks oluşturuldu: {index_name} on {table}")
        else:
            print(f"İndeks zaten mevcut: {index_name} on {table}")
            
    except Exception as e:
        print(f"İndeks oluşturma hatası {index_info['index_name']}: {str(e)}")

def update_table_statistics():
    """
    Tablo istatistiklerini güncelle
    """
    tables_to_analyze = [
        "tabProduction Plan",
        "tabProduction Plan Item", 
        "tabSales Order",
        "tabSales Order Item",
        "tabWork Order",
        "tabDelivery Note Item",
        "tabItem"
    ]
    
    for table in tables_to_analyze:
        try:
            frappe.db.sql(f"ANALYZE TABLE {table}")
            print(f"Tablo istatistikleri güncellendi: {table}")
        except Exception as e:
            print(f"İstatistik güncelleme hatası {table}: {str(e)}")

@frappe.whitelist()
def check_performance():
    """
    Performans durumunu kontrol et
    """
    try:
        # Basit bir performans testi yap
        start_time = frappe.utils.now()
        
        # Test sorgusu
        test_result = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabProduction Plan` pp
            INNER JOIN `tabProduction Plan Item` ppi ON pp.name = ppi.parent
            WHERE pp.docstatus = 1 AND pp.status != 'Closed'
            LIMIT 1
        """, as_dict=True)
        
        end_time = frappe.utils.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return {
            "status": "success",
            "execution_time": execution_time,
            "message": f"Test sorgusu {execution_time:.3f} saniyede tamamlandı"
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Performans testi hatası: {str(e)}"
        }

def get_performance_recommendations():
    """
    Performans iyileştirme önerileri
    """
    recommendations = [
        "1. Veritabanı indekslerinin güncel olduğundan emin olun",
        "2. Büyük tablolarda sayfalama kullanın (limit parametresi)",
        "3. Gereksiz alanları çekmekten kaçının",
        "4. Sık kullanılan sorguları cache'leyin",
        "5. Veritabanı bağlantı havuzunu optimize edin",
        "6. Düzenli olarak tablo istatistiklerini güncelleyin"
    ]
    
    return recommendations 