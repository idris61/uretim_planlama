import frappe
import time
import json
from datetime import datetime

def run_performance_tests():
    """
    Kapsamlı performans testleri çalıştır
    """
    print("=== Üretim Paneli Performans Testleri ===")
    print(f"Test Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Temel veri çekme testi
    test_basic_data_loading()
    
    # Test 2: Filtreleme testi
    test_filtering_performance()
    
    # Test 3: Büyük veri seti testi
    test_large_dataset()
    
    # Test 4: Badge çekme testi
    test_badge_loading()
    
    # Test 5: Genel performans raporu
    generate_performance_report()

def test_basic_data_loading():
    """
    Temel veri çekme performansını test et
    """
    print("1. Temel Veri Çekme Testi")
    print("-" * 40)
    
    start_time = time.time()
    
    try:
        result = frappe.call(
            'uretim_planlama.uretim_planlama.page.uretim_paneli.uretim_paneli.get_production_planning_data',
            args={'filters': json.dumps({})}
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result and 'message' in result:
            data = result['message']
            planned_count = len(data.get('planned', []))
            unplanned_count = len(data.get('unplanned', []))
            total_count = planned_count + unplanned_count
            
            print(f"✓ Başarılı")
            print(f"  - Çalışma süresi: {execution_time:.3f} saniye")
            print(f"  - Planlanan kayıt: {planned_count}")
            print(f"  - Planlanmamış kayıt: {unplanned_count}")
            print(f"  - Toplam kayıt: {total_count}")
            
            if execution_time < 1.0:
                print(f"  - Performans: Mükemmel (< 1 saniye)")
            elif execution_time < 2.0:
                print(f"  - Performans: İyi (< 2 saniye)")
            elif execution_time < 5.0:
                print(f"  - Performans: Kabul edilebilir (< 5 saniye)")
            else:
                print(f"  - Performans: Yavaş (> 5 saniye)")
                
        else:
            print("✗ Hata: Veri alınamadı")
            
    except Exception as e:
        print(f"✗ Hata: {str(e)}")
    
    print()

def test_filtering_performance():
    """
    Filtreleme performansını test et
    """
    print("2. Filtreleme Performans Testi")
    print("-" * 40)
    
    filters_to_test = [
        {"hafta": "1", "limit": 50},
        {"bayi": "Test Bayi", "limit": 50},
        {"acil_durum": "ACİL", "limit": 50},
        {"hafta": "1", "bayi": "Test Bayi", "acil_durum": "ACİL", "limit": 50}
    ]
    
    for i, filters in enumerate(filters_to_test, 1):
        print(f"Test {i}: {filters}")
        
        start_time = time.time()
        
        try:
            result = frappe.call(
                'uretim_planlama.uretim_planlama.page.uretim_paneli.uretim_paneli.get_production_planning_data',
                args={'filters': json.dumps(filters)}
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            if result and 'message' in result:
                data = result['message']
                total_count = len(data.get('planned', [])) + len(data.get('unplanned', []))
                
                print(f"  ✓ {execution_time:.3f}s - {total_count} kayıt")
            else:
                print(f"  ✗ Hata")
                
        except Exception as e:
            print(f"  ✗ Hata: {str(e)}")
    
    print()

def test_large_dataset():
    """
    Büyük veri seti performansını test et
    """
    print("3. Büyük Veri Seti Testi")
    print("-" * 40)
    
    large_filters = {"limit": 500}
    
    start_time = time.time()
    
    try:
        result = frappe.call(
            'uretim_planlama.uretim_planlama.page.uretim_paneli.uretim_paneli.get_production_planning_data',
            args={'filters': json.dumps(large_filters)}
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result and 'message' in result:
            data = result['message']
            total_count = len(data.get('planned', [])) + len(data.get('unplanned', []))
            
            print(f"✓ 500 kayıt testi başarılı")
            print(f"  - Çalışma süresi: {execution_time:.3f} saniye")
            print(f"  - Toplam kayıt: {total_count}")
            print(f"  - Saniyede kayıt: {total_count/execution_time:.1f}")
            
        else:
            print("✗ Hata: Veri alınamadı")
            
    except Exception as e:
        print(f"✗ Hata: {str(e)}")
    
    print()

def test_badge_loading():
    """
    Badge çekme performansını test et
    """
    print("4. Badge Çekme Testi")
    print("-" * 40)
    
    # Önce bazı sales order'ları al
    try:
        sales_orders = frappe.db.sql("""
            SELECT DISTINCT sales_order 
            FROM `tabProduction Plan Item` 
            WHERE sales_order IS NOT NULL 
            LIMIT 10
        """, as_list=True)
        
        if sales_orders:
            so_list = [so[0] for so in sales_orders]
            
            start_time = time.time()
            
            # Badge'leri toplu olarak çek
            badges_map = get_badges_bulk(so_list)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"✓ Badge testi başarılı")
            print(f"  - Çalışma süresi: {execution_time:.3f} saniye")
            print(f"  - Test edilen SO: {len(so_list)}")
            print(f"  - Badge'li SO: {len(badges_map)}")
            
        else:
            print("✗ Test edilecek sales order bulunamadı")
            
    except Exception as e:
        print(f"✗ Hata: {str(e)}")
    
    print()

def get_badges_bulk(sales_orders):
    """
    Badge'leri toplu olarak çek (test için)
    """
    if not sales_orders:
        return {}
    
    badges_map = {}
    
    # Work Order badge'leri
    work_order_query = """
        SELECT DISTINCT sales_order 
        FROM `tabWork Order` 
        WHERE sales_order IN ({})
        AND docstatus > 0
    """.format(','.join(['%s'] * len(sales_orders)))
    
    work_order_sales_orders = frappe.db.sql(work_order_query, sales_orders, as_list=True)
    for (sales_order,) in work_order_sales_orders:
        if sales_order not in badges_map:
            badges_map[sales_order] = []
        badges_map[sales_order].append({"label": "Üretim Başladı", "class": "badge-info"})
    
    # Delivery Note badge'leri
    delivery_query = """
        SELECT DISTINCT against_sales_order 
        FROM `tabDelivery Note Item` 
        WHERE against_sales_order IN ({})
    """.format(','.join(['%s'] * len(sales_orders)))
    
    delivery_sales_orders = frappe.db.sql(delivery_query, sales_orders, as_list=True)
    for (sales_order,) in delivery_sales_orders:
        if sales_order not in badges_map:
            badges_map[sales_order] = []
        badges_map[sales_order].append({"label": "Teslim Edildi", "class": "badge-success"})
    
    return badges_map

def generate_performance_report():
    """
    Genel performans raporu oluştur
    """
    print("5. Performans Raporu")
    print("-" * 40)
    
    # Veritabanı istatistikleri
    try:
        # Tablo boyutları
        table_stats = {}
        tables = [
            "tabProduction Plan",
            "tabProduction Plan Item", 
            "tabSales Order",
            "tabSales Order Item",
            "tabWork Order",
            "tabDelivery Note Item"
        ]
        
        for table in tables:
            count = frappe.db.sql(f"SELECT COUNT(*) as count FROM {table}", as_dict=True)[0]['count']
            table_stats[table] = count
        
        print("Veritabanı İstatistikleri:")
        for table, count in table_stats.items():
            print(f"  - {table}: {count:,} kayıt")
        
        # İndeks durumu
        print("\nİndeks Durumu:")
        indexes_to_check = [
            ("tabProduction Plan", "idx_production_plan_status"),
            ("tabProduction Plan Item", "idx_production_plan_item_parent"),
            ("tabSales Order", "idx_sales_order_status_date"),
            ("tabWork Order", "idx_work_order_sales_order")
        ]
        
        for table, index_name in indexes_to_check:
            try:
                result = frappe.db.sql(f"""
                    SHOW INDEX FROM {table} 
                    WHERE Key_name = '{index_name}'
                """, as_dict=True)
                
                if result:
                    print(f"  ✓ {index_name} - Mevcut")
                else:
                    print(f"  ✗ {index_name} - Eksik")
            except:
                print(f"  ? {index_name} - Kontrol edilemedi")
        
        # Öneriler
        print("\nPerformans Önerileri:")
        recommendations = [
            "1. Düzenli olarak tablo istatistiklerini güncelleyin",
            "2. Büyük tablolarda sayfalama kullanın",
            "3. Gereksiz indeksleri kaldırın",
            "4. Sık kullanılan sorguları cache'leyin",
            "5. Veritabanı bağlantı havuzunu optimize edin"
        ]
        
        for rec in recommendations:
            print(f"  {rec}")
            
    except Exception as e:
        print(f"Rapor oluşturma hatası: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Performans testleri tamamlandı!")

@frappe.whitelist()
def run_tests():
    """
    Web arayüzünden test çalıştır
    """
    try:
        run_performance_tests()
        return {"status": "success", "message": "Testler başarıyla tamamlandı"}
    except Exception as e:
        return {"status": "error", "message": f"Test hatası: {str(e)}"}

if __name__ == "__main__":
    run_performance_tests() 