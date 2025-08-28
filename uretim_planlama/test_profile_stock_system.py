# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
PROFİL STOK YÖNETİMİ SİSTEMİ TEST SENARYOLARI
==============================================

Bu dosya, geliştirilen profil stok yönetim sisteminin kapsamlı testini sağlar.
Her test senaryosu ayrı ayrı çalıştırılabilir ve sonuçları raporlanır.
"""

import frappe
import unittest
from frappe.test_runner import make_test_records
from frappe.utils import nowdate, add_days

class TestProfileStockSystem(unittest.TestCase):
    """Profil Stok Yönetim Sistemi Test Sınıfı"""
    
    def setUp(self):
        """Test öncesi hazırlık"""
        frappe.set_user("Administrator")
        self.setup_test_data()
    
    def setup_test_data(self):
        """Test verilerini hazırla"""
        # Test profil ürünleri oluştur
        self.create_test_profile_items()
        
        # Test depo oluştur
        self.create_test_warehouse()
        
        # Test tedarikçi oluştur
        self.create_test_supplier()
    
    def create_test_profile_items(self):
        """Test profil ürünleri oluştur"""
        test_items = [
            {
                "item_code": "TEST-PVC-001",
                "item_name": "Test PVC Profil 1",
                "item_group": "PVC",
                "stock_uom": "Nos",
                "custom_total_main_profiles_mtul": 11.35
            },
            {
                "item_code": "TEST-CAM-001", 
                "item_name": "Test Cam Profil 1",
                "item_group": "Camlar",
                "stock_uom": "Nos",
                "custom_mtul_per_piece": 1.745
            }
        ]
        
        for item_data in test_items:
            if not frappe.db.exists("Item", item_data["item_code"]):
                item = frappe.new_doc("Item")
                item.update(item_data)
                item.insert(ignore_permissions=True)
                print(f"✅ Test ürün oluşturuldu: {item_data['item_code']}")
    
    def create_test_warehouse(self):
        """Test depo oluştur"""
        if not frappe.db.exists("Warehouse", "Test Profil Depo"):
            warehouse = frappe.new_doc("Warehouse")
            warehouse.warehouse_name = "Test Profil Depo"
            warehouse.company = frappe.defaults.get_user_default("Company")
            warehouse.insert(ignore_permissions=True)
            print("✅ Test depo oluşturuldu: Test Profil Depo")
    
    def create_test_supplier(self):
        """Test tedarikçi oluştur"""
        if not frappe.db.exists("Supplier", "Test Profil Tedarikçi"):
            supplier = frappe.new_doc("Supplier")
            supplier.supplier_name = "Test Profil Tedarikçi"
            supplier.supplier_type = "Company"
            supplier.insert(ignore_permissions=True)
            print("✅ Test tedarikçi oluşturuldu: Test Profil Tedarikçi")
    
    def test_01_profile_entry_creation(self):
        """Test 1: Profile Entry oluşturma ve validasyon"""
        print("\n🧪 Test 1: Profile Entry Oluşturma ve Validasyon")
        
        try:
            # Profile Entry oluştur
            profile_entry = frappe.new_doc("Profile Entry")
            profile_entry.date = nowdate()
            profile_entry.supplier = "Test Profil Tedarikçi"
            profile_entry.warehouse = "Test Profil Depo"
            profile_entry.remarks = "Test profil girişi"
            
            # Satır ekle
            profile_entry.append("items", {
                "item_code": "TEST-PVC-001",
                "received_quantity": 10,
                "length": "5 m",
                "reference_type": "Manual Entry",
                "warehouse": "Test Profil Depo"
            })
            
            # Kaydet
            profile_entry.save()
            print("✅ Profile Entry başarıyla kaydedildi")
            
            # Validasyon testleri
            self.assertIsNotNone(profile_entry.total_received_length)
            self.assertIsNotNone(profile_entry.total_received_qty)
            self.assertEqual(profile_entry.total_received_qty, 10)
            self.assertEqual(profile_entry.total_received_length, 50.0)
            print("✅ Validasyon testleri başarılı")
            
            # Onayla
            profile_entry.submit()
            print("✅ Profile Entry başarıyla onaylandı")
            
            # Test sonrası temizlik
            profile_entry.cancel()
            profile_entry.delete()
            print("✅ Test verisi temizlendi")
            
        except Exception as e:
            self.fail(f"Profile Entry test hatası: {str(e)}")
    
    def test_02_profile_exit_creation(self):
        """Test 2: Profile Exit oluşturma ve stok kontrolü"""
        print("\n🧪 Test 2: Profile Exit Oluşturma ve Stok Kontrolü")
        
        try:
            # Önce stok girişi yap
            self.create_test_stock()
            
            # Profile Exit oluştur
            profile_exit = frappe.new_doc("Profile Exit")
            profile_exit.date = nowdate()
            profile_exit.warehouse = "Test Profil Depo"
            profile_exit.remarks = "Test profil çıkışı"
            
            # Satır ekle
            profile_exit.append("items", {
                "item_code": "TEST-PVC-001",
                "output_quantity": 5,
                "length": "5 m",
                "reference_type": "Manual Exit",
                "warehouse": "Test Profil Depo"
            })
            
            # Kaydet
            profile_exit.save()
            print("✅ Profile Exit başarıyla kaydedildi")
            
            # Validasyon testleri
            self.assertIsNotNone(profile_exit.total_output_length)
            self.assertIsNotNone(profile_exit.total_output_qty)
            self.assertEqual(profile_exit.total_output_qty, 5)
            self.assertEqual(profile_exit.total_output_length, 25.0)
            print("✅ Validasyon testleri başarılı")
            
            # Onayla
            profile_exit.submit()
            print("✅ Profile Exit başarıyla onaylandı")
            
            # Test sonrası temizlik
            profile_exit.cancel()
            profile_exit.delete()
            self.cleanup_test_stock()
            print("✅ Test verisi temizlendi")
            
        except Exception as e:
            self.fail(f"Profile Exit test hatası: {str(e)}")
    
    def test_03_scrap_profile_entry(self):
        """Test 3: Scrap Profile Entry oluşturma"""
        print("\n🧪 Test 3: Scrap Profile Entry Oluşturma")
        
        try:
            # Scrap Profile Entry oluştur
            scrap_entry = frappe.new_doc("Scrap Profile Entry")
            scrap_entry.profile_code = "TEST-PVC-001"
            scrap_entry.length = 2.5
            scrap_entry.qty = 3
            scrap_entry.scrap_reason = "Production Defect"
            scrap_entry.scrap_category = "Minor"
            scrap_entry.warehouse = "Test Profil Depo"
            scrap_entry.entry_date = nowdate()
            scrap_entry.description = "Test scrap girişi"
            
            # Kaydet
            scrap_entry.save()
            print("✅ Scrap Profile Entry başarıyla kaydedildi")
            
            # Validasyon testleri
            self.assertIsNotNone(scrap_entry.total_length)
            self.assertEqual(scrap_entry.total_length, 7.5)
            print("✅ Validasyon testleri başarılı")
            
            # Onayla
            scrap_entry.submit()
            print("✅ Scrap Profile Entry başarıyla onaylandı")
            
            # Test sonrası temizlik
            scrap_entry.cancel()
            scrap_entry.delete()
            print("✅ Test verisi temizlendi")
            
        except Exception as e:
            self.fail(f"Scrap Profile Entry test hatası: {str(e)}")
    
    def test_04_stock_validation(self):
        """Test 4: Stok validasyonu ve kontrolü"""
        print("\n🧪 Test 4: Stok Validasyonu ve Kontrolü")
        
        try:
            # Stok girişi yap
            self.create_test_stock()
            
            # Yetersiz stok ile çıkış denemesi
            profile_exit = frappe.new_doc("Profile Exit")
            profile_exit.date = nowdate()
            profile_exit.warehouse = "Test Profil Depo"
            
            # Mevcut stoktan fazla çıkış dene
            profile_exit.append("items", {
                "item_code": "TEST-PVC-001",
                "output_quantity": 15,  # Mevcut stoktan fazla
                "length": "5 m",
                "warehouse": "Test Profil Depo"
            })
            
            # Kaydetmeye çalış (hata vermeli)
            with self.assertRaises(Exception):
                profile_exit.save()
            print("✅ Yetersiz stok kontrolü başarılı")
            
            # Test sonrası temizlik
            self.cleanup_test_stock()
            print("✅ Test verisi temizlendi")
            
        except Exception as e:
            self.fail(f"Stok validasyon test hatası: {str(e)}")
    
    def test_05_api_functions(self):
        """Test 5: API fonksiyonları testi"""
        print("\n🧪 Test 5: API Fonksiyonları Testi")
        
        try:
            # Stok girişi yap
            self.create_test_stock()
            
            # API fonksiyonlarını test et
            from uretim_planlama.uretim_planlama.profile_stock_api import get_profile_stock_overview
            
            result = get_profile_stock_overview()
            self.assertTrue(result["success"])
            print("✅ API fonksiyon testi başarılı")
            
            # Test sonrası temizlik
            self.cleanup_test_stock()
            print("✅ Test verisi temizlendi")
            
        except Exception as e:
            self.fail(f"API fonksiyon test hatası: {str(e)}")
    
    def create_test_stock(self):
        """Test stoku oluştur"""
        try:
            # Profile Entry ile test stoku oluştur
            profile_entry = frappe.new_doc("Profile Entry")
            profile_entry.date = nowdate()
            profile_entry.supplier = "Test Profil Tedarikçi"
            profile_entry.warehouse = "Test Profil Depo"
            profile_entry.remarks = "Test stok oluşturma"
            
            profile_entry.append("items", {
                "item_code": "TEST-PVC-001",
                "received_quantity": 10,
                "length": "5 m",
                "warehouse": "Test Profil Depo"
            })
            
            profile_entry.insert(ignore_permissions=True)
            profile_entry.submit()
            print("✅ Test stoku oluşturuldu")
            
        except Exception as e:
            print(f"❌ Test stoku oluşturma hatası: {str(e)}")
    
    def cleanup_test_stock(self):
        """Test stokunu temizle"""
        try:
            # Profile Stock Ledger'dan test kayıtlarını temizle
            test_stocks = frappe.get_all(
                "Profile Stock Ledger",
                filters={"profile_type": ["like", "TEST-%"]},
                fields=["name"]
            )
            
            for stock in test_stocks:
                frappe.delete_doc("Profile Stock Ledger", stock.name, ignore_permissions=True)
            
            print("✅ Test stoku temizlendi")
            
        except Exception as e:
            print(f"❌ Test stoku temizleme hatası: {str(e)}")
    
    def tearDown(self):
        """Test sonrası temizlik"""
        try:
            # Test verilerini temizle
            self.cleanup_test_stock()
            
            # Test ürünlerini temizle
            test_items = ["TEST-PVC-001", "TEST-CAM-001"]
            for item_code in test_items:
                if frappe.db.exists("Item", item_code):
                    frappe.delete_doc("Item", item_code, ignore_permissions=True)
            
            # Test depo ve tedarikçiyi temizle
            if frappe.db.exists("Warehouse", "Test Profil Depo"):
                frappe.delete_doc("Warehouse", "Test Profil Depo", ignore_permissions=True)
            
            if frappe.db.exists("Supplier", "Test Profil Tedarikçi"):
                frappe.delete_doc("Supplier", "Test Profil Tedarikçi", ignore_permissions=True)
                
            print("✅ Tüm test verileri temizlendi")
            
        except Exception as e:
            print(f"❌ Test temizlik hatası: {str(e)}")

def run_profile_stock_tests():
    """Profil stok testlerini çalıştır"""
    print("🚀 PROFİL STOK YÖNETİMİ SİSTEMİ TESTLERİ BAŞLIYOR!")
    print("=" * 60)
    
    # Test suite oluştur
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProfileStockSystem)
    
    # Testleri çalıştır
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Sonuçları raporla
    print("\n" + "=" * 60)
    print("📊 TEST SONUÇLARI:")
    print(f"✅ Başarılı: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Başarısız: {len(result.failures)}")
    print(f"⚠️ Hatalı: {len(result.errors)}")
    print(f"📈 Toplam: {result.testsRun}")
    
    if result.failures:
        print("\n❌ BAŞARISIZ TESTLER:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n⚠️ HATALI TESTLER:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    print("\n🎯 Test tamamlandı!")
    return result.wasSuccessful()

if __name__ == "__main__":
    run_profile_stock_tests()
