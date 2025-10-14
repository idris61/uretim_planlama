# 📦 Profile Stock Import Guide

Bu dokümantasyon Profile Stock Ledger toplu import işlemleri ve Profile Entry otomatik oluşturma sürecini açıklar.

## 🎯 **Özet**

Profile Stock Ledger'a toplu import yapıldığında, sistem otomatik olarak Profile Entry kayıtları da oluşturur. Bu sayede:
- ✅ Stok girişi yapılır
- ✅ Profile Entry kayıtları oluşturulur  
- ✅ Audit trail sağlanır
- ✅ Raporlama tutarlılığı korunur

---

## 🔧 **Teknik Detaylar**

### **1. Profile Stock Ledger Import Hook**
- `after_insert()` metodu eklendi
- Import sırasında `frappe.flags.in_import` kontrolü
- Sadece normal stoklar için (scrap değil) Profile Entry oluşturur

### **2. Otomatik Profile Entry Oluşturma**
- Tarih: Bugünün tarihi
- Tedarikçi: Import verisinden alınır (varsa)
- Açıklama: "Import ile oluşturuldu - {user}"
- Submit: Otomatik submit edilir

### **3. Bulk Import Handler**
- `/uretim_planlama/api/bulk_profile_import.py`
- CSV dosyası okuma ve işleme
- Tarihe göre gruplama
- Toplu Profile Entry oluşturma

---

## 📋 **Import Formatı**

### **CSV Dosya Yapısı**
```csv
profile_type,length,qty,is_scrap_piece,date,supplier,remarks
101073427,6.5,100,0,2025-01-15,Tedarikçi A,Test import
102003427,6.5,50,0,2025-01-15,Tedarikçi A,Test import
101073427,5.0,75,0,2025-01-16,Tedarikçi B,Test import 2
102003427,5.0,25,0,2025-01-16,Tedarikçi B,Test import 2
101073427,6.5,10,1,2025-01-17,,Fire parça
```

### **Alan Açıklamaları**

| Alan | Tip | Zorunlu | Açıklama |
|------|-----|---------|----------|
| `profile_type` | String | ✅ | Ürün kodu |
| `length` | Float | ✅ | Boy (metre) |
| `qty` | Integer | ✅ | Miktar |
| `is_scrap_piece` | Boolean | ❌ | Fire parça mı? (0/1) |
| `date` | Date | ❌ | Giriş tarihi (varsayılan: bugün) |
| `supplier` | String | ❌ | Tedarikçi |
| `remarks` | String | ❌ | Açıklama |

---

## 🚀 **Kullanım Yöntemleri**

### **1. Standart Data Import (ERPNext UI)**

1. **Data Import** sayfasına git
2. **Reference DocType**: `Profile Stock Ledger` seç
3. **Import Type**: `Insert New Records` seç
4. CSV dosyasını yükle
5. Import'u çalıştır

**Sonuç**: 
- Profile Stock Ledger kayıtları oluşturulur
- Her kayıt için otomatik Profile Entry oluşturulur

### **2. Bulk Import Script (Komut Satırı)**

```bash
# Template oluştur
bench --site ozerpan.com execute uretim_planlama.api.bulk_profile_import.create_import_template

# Bulk import çalıştır
bench --site ozerpan.com execute uretim_planlama.api.bulk_profile_import.process_bulk_import --args "{'file_path': '/path/to/file.csv', 'create_profile_entries': True, 'submit_entries': True}"
```

### **3. Programatik Import**

```python
from uretim_planlama.api.bulk_profile_import import process_bulk_import

result = process_bulk_import(
    file_path='/path/to/file.csv',
    create_profile_entries=True,
    submit_entries=True
)
```

---

## 📊 **Import Süreci**

### **1. Veri Okuma**
- CSV dosyası parse edilir
- Gerekli alanlar kontrol edilir
- Veriler temizlenir ve dönüştürülür

### **2. Profile Stock Ledger Oluşturma**
- Her satır için Profile Stock Ledger kaydı oluşturulur
- `frappe.flags.in_import = True` set edilir
- Duplicate kontrolü yapılır

### **3. Profile Entry Oluşturma**
- Tarihe göre veriler gruplandırılır
- Her tarih grubu için Profile Entry oluşturulur
- Child table items eklenir
- Otomatik submit edilir

### **4. Sonuç Raporu**
- Oluşturulan kayıt sayıları
- Ürün bazında özet
- Hata raporları

---

## ⚠️ **Önemli Notlar**

### **Duplicate Kontrolü**
- Aynı `(profile_type, length, is_scrap_piece)` için sadece 1 kayıt
- Duplicate varsa otomatik birleştirilir
- Unique constraint ile korunur

### **Validation Bypass**
- Import sırasında validation'lar bypass edilir
- `ignore_validate`, `ignore_permissions` flag'leri
- Grup kontrolü bypass edilir (`bypass_group_check`)

### **Error Handling**
- Hata durumunda detaylı log
- Kısmi başarı durumunda devam eder
- Rollback mekanizması

### **Performance**
- Batch processing
- Database index'leri
- Commit her batch sonrası

---

## 🔍 **Troubleshooting**

### **Sık Karşılaşılan Sorunlar**

1. **Module Not Found Hatası**
   ```bash
   bench --site ozerpan.com migrate
   bench --site ozerpan.com clear-cache
   ```

2. **Validation Hatası**
   - Import sırasında validation bypass edilir
   - Manuel kayıtlarda grup kontrolü çalışır

3. **Duplicate Kayıt Hatası**
   - Consolidation script çalıştır:
   ```bash
   bench --site ozerpan.com execute uretim_planlama.api.consolidate_profile_stock.consolidate_duplicates --args "{'dry_run': False}"
   ```

### **Log Kontrolü**
```bash
# Profile Entry import logları
tail -f /home/idris/ozerpan-bench/logs/error.log | grep "Profile Entry Import"

# Bulk import logları  
tail -f /home/idris/ozerpan-bench/logs/error.log | grep "Bulk Profile Import"
```

---

## 📈 **Monitoring ve Raporlama**

### **Import Sonrası Kontroller**

1. **Profile Stock Ledger Kontrolü**
   ```sql
   SELECT profile_type, length, COUNT(*) as count 
   FROM `tabProfile Stock Ledger` 
   GROUP BY profile_type, length 
   HAVING COUNT(*) > 1;
   ```

2. **Profile Entry Kontrolü**
   ```sql
   SELECT date, COUNT(*) as entry_count, SUM(total_received_qty) as total_qty
   FROM `tabProfile Entry` 
   WHERE remarks LIKE '%Import ile oluşturuldu%'
   GROUP BY date
   ORDER BY date DESC;
   ```

3. **Stok Tutarlılığı**
   - Profile Stock Ledger vs Profile Entry toplamları
   - Duplicate kayıt kontrolü
   - Negatif stok kontrolü

---

## 🎯 **Best Practices**

### **Import Öncesi**
1. ✅ Backup al
2. ✅ CSV formatını kontrol et
3. ✅ Ürün kodlarını doğrula
4. ✅ Duplicate kayıtları temizle

### **Import Sırasında**
1. ✅ Test dosyası ile başla
2. ✅ Log'ları takip et
3. ✅ Batch size'ı ayarla
4. ✅ Error handling'i kontrol et

### **Import Sonrası**
1. ✅ Sonuçları doğrula
2. ✅ Duplicate kontrolü yap
3. ✅ Raporları kontrol et
4. ✅ Log'ları temizle

---

## 🔄 **Güncelleme ve Bakım**

### **Sistem Güncellemeleri**
- Migration sonrası index'ler otomatik eklenir
- Yeni alanlar için template güncellenir
- Validation kuralları güncellenir

### **Performance Optimizasyonu**
- Database index'leri
- Batch size ayarları
- Memory kullanımı

### **Güvenlik**
- Permission kontrolü
- Data validation
- Audit trail

---

## 📞 **Destek**

Sorun yaşadığınızda:

1. **Log Dosyalarını Kontrol Edin**
2. **Error Messages'ları Kaydedin**
3. **Import Dosyasını Paylaşın**
4. **System Information'ı Toplayın**

---

**📝 Son Güncelleme**: 2025-01-15  
**👨‍💻 Geliştirici**: idris  
**📋 Versiyon**: 1.0

