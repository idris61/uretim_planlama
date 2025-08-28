# 🧪 PROFİL STOK YÖNETİMİ MANUEL TEST REHBERİ

## 📋 **Test Öncesi Hazırlık**

### **1. Sistem Kontrolü**
- [ ] ERPNext çalışıyor
- [ ] Uretim Planlama uygulaması kurulu
- [ ] Migration tamamlandı
- [ ] Cache temizlendi

### **2. Test Verileri Hazırlığı**
- [ ] Test profil ürünleri oluşturuldu
- [ ] Test depo oluşturuldu
- [ ] Test tedarikçi oluşturuldu
- [ ] Boy (Length) seçenekleri mevcut

---

## 🧪 **TEST SENARYOLARI**

### **TEST 1: Profile Entry Oluşturma ve Validasyon**

#### **Adım 1: Yeni Profile Entry Oluştur**
1. **Uretim Planlama** → **Profile Entry** → **New**
2. **Date**: Bugünün tarihi
3. **Supplier**: Test tedarikçi seç
4. **Warehouse**: Test depo seç
5. **Remarks**: "Test profil girişi"

#### **Adım 2: Satır Ekleme**
1. **Items** tablosuna satır ekle:
   - **Item Code**: Test PVC ürünü seç
   - **Received Quantity**: 10
   - **Length**: "5 m" seç
   - **Reference Type**: "Manual Entry"
   - **Warehouse**: Test depo seç

#### **Adım 3: Validasyon Testleri**
- [ ] **Kaydet** butonuna tıkla
- [ ] **Total Received Length** otomatik hesaplandı mı? (50.0 m olmalı)
- [ ] **Total Received Quantity** otomatik hesaplandı mı? (10 olmalı)
- [ ] Hata mesajı var mı?

#### **Adım 4: Onaylama Testi**
1. **Submit** butonuna tıkla
2. **Başarı mesajı** görüldü mü?
3. **Profile Stock Ledger**'da stok güncellendi mi?

#### **Beklenen Sonuçlar:**
- ✅ Doküman başarıyla kaydedildi
- ✅ Toplam değerler otomatik hesaplandı
- ✅ Stok başarıyla güncellendi
- ✅ Başarı mesajı görüldü

---

### **TEST 2: Profile Exit Oluşturma ve Stok Kontrolü**

#### **Adım 1: Önce Stok Girişi Yap**
1. **TEST 1**'i tamamla (stok girişi)

#### **Adım 2: Yeni Profile Exit Oluştur**
1. **Uretim Planlama** → **Profile Exit** → **New**
2. **Date**: Bugünün tarihi
3. **Warehouse**: Test depo seç
4. **Remarks**: "Test profil çıkışı"

#### **Adım 3: Satır Ekleme**
1. **Items** tablosuna satır ekle:
   - **Item Code**: Test PVC ürünü seç
   - **Output Quantity**: 5
   - **Length**: "5 m" seç
   - **Reference Type**: "Manual Exit"
   - **Warehouse**: Test depo seç

#### **Adım 4: Validasyon Testleri**
- [ ] **Kaydet** butonuna tıkla
- [ ] **Total Output Length** otomatik hesaplandı mı? (25.0 m olmalı)
- [ ] **Total Output Quantity** otomatik hesaplandı mı? (5 olmalı)
- [ ] Hata mesajı var mı?

#### **Adım 5: Onaylama Testi**
1. **Submit** butonuna tıkla
2. **Başarı mesajı** görüldü mü?
3. **Profile Stock Ledger**'da stok azaldı mı?

#### **Beklenen Sonuçlar:**
- ✅ Doküman başarıyla kaydedildi
- ✅ Toplam değerler otomatik hesaplandı
- ✅ Stok başarıyla azaldı
- ✅ Başarı mesajı görüldü

---

### **TEST 3: Scrap Profile Entry Oluşturma**

#### **Adım 1: Yeni Scrap Profile Entry Oluştur**
1. **Uretim Planlama** → **Scrap Profile Entry** → **New**
2. **Profile Code**: Test PVC ürünü seç
3. **Length**: 2.5
4. **Quantity**: 3
5. **Scrap Reason**: "Production Defect" seç
6. **Scrap Category**: "Minor" seç
7. **Warehouse**: Test depo seç
8. **Description**: "Test scrap girişi"

#### **Adım 2: Validasyon Testleri**
- [ ] **Kaydet** butonuna tıkla
- [ ] **Total Length** otomatik hesaplandı mı? (7.5 m olmalı)
- [ ] Hata mesajı var mı?

#### **Adım 3: Onaylama Testi**
1. **Submit** butonuna tıkla
2. **Başarı mesajı** görüldü mü?
3. **Profile Stock Ledger**'da scrap stok eklendi mi?

#### **Beklenen Sonuçlar:**
- ✅ Doküman başarıyla kaydedildi
- ✅ Toplam uzunluk otomatik hesaplandı
- ✅ Scrap stok başarıyla eklendi
- ✅ Başarı mesajı görüldü

---

### **TEST 4: Stok Validasyonu ve Hata Kontrolü**

#### **Adım 1: Yetersiz Stok Testi**
1. **TEST 1**'i tamamla (10 adet stok girişi)
2. **Profile Exit** oluştur
3. **Output Quantity**: 15 (mevcut stoktan fazla)
4. **Kaydet** butonuna tıkla

#### **Beklenen Sonuç:**
- ❌ **Hata mesajı** görülmeli: "Yetersiz stok"
- ❌ Doküman kaydedilmemeli

#### **Adım 2: Geçersiz Boy Format Testi**
1. **Profile Entry** oluştur
2. **Length** alanına geçersiz değer gir: "abc"
3. **Kaydet** butonuna tıkla

#### **Beklenen Sonuç:**
- ❌ **Hata mesajı** görülmeli: "Geçersiz boy formatı"
- ❌ Doküman kaydedilmemeli

#### **Adım 3: Profil Olmayan Ürün Testi**
1. **Profile Entry** oluştur
2. **Item Code** olarak profil olmayan ürün seç
3. **Kaydet** butonuna tıkla

#### **Beklenen Sonuç:**
- ❌ **Hata mesajı** görülmeli: "Bu ürün profil değil"
- ❌ Doküman kaydedilmemeli

---

### **TEST 5: API Fonksiyonları Testi**

#### **Adım 1: Stok Özeti API Testi**
1. **Console** aç (Developer Tools)
2. Aşağıdaki kodu çalıştır:

```python
frappe.call('uretim_planlama.uretim_planlama.profile_stock_api.get_profile_stock_overview')
```

#### **Beklenen Sonuç:**
- ✅ **Success: true** döndü
- ✅ **Data** objesi mevcut

#### **Adım 2: Stok Yeterlilik Kontrolü API Testi**
1. Console'da aşağıdaki kodu çalıştır:

```python
frappe.call('uretim_planlama.uretim_planlama.profile_stock_api.check_profile_availability', 
            item_code='TEST-PVC-001', 
            required_length=5.0, 
            required_qty=10)
```

#### **Beklenen Sonuç:**
- ✅ **Success: true** döndü
- ✅ **Available** durumu doğru
- ✅ **Data** objesi mevcut

---

### **TEST 6: Entegrasyon Testleri**

#### **Adım 1: Purchase Receipt Entegrasyonu**
1. **Stock** → **Purchase Receipt** → **New**
2. **Supplier**: Test tedarikçi seç
3. **Items** tablosuna satır ekle:
   - **Item**: Test PVC ürünü seç
   - **Qty**: 5
   - **Warehouse**: Test depo seç
   - **Custom Is Profile**: ✅ işaretle
   - **Custom Profile Length (m)**: "5 m" seç
   - **Custom Profile Length Qty**: 5

#### **Beklenen Sonuç:**
- ✅ Doküman kaydedildi
- ✅ Submit sonrası profil stok güncellendi
- ✅ Başarı mesajı görüldü

#### **Adım 2: Delivery Note Entegrasyonu**
1. **Stock** → **Delivery Note** → **New**
2. **Customer**: Test müşteri seç
3. **Items** tablosuna satır ekle:
   - **Item**: Test PVC ürünü seç
   - **Qty**: 2
   - **Warehouse**: Test depo seç
   - **Custom Is Profile**: ✅ işaretle
   - **Custom Profile Length (m)**: "5 m" seç
   - **Custom Profile Length Qty**: 2

#### **Beklenen Sonuç:**
- ✅ Doküman kaydedildi
- ✅ Submit sonrası profil stok azaldı
- ✅ Başarı mesajı görüldü

---

## 📊 **Test Sonuçları Değerlendirme**

### **Başarı Kriterleri:**
- ✅ Tüm dokümanlar başarıyla oluşturuldu
- ✅ Validasyon kontrolleri çalıştı
- ✅ Stok güncellemeleri doğru
- ✅ Hata mesajları anlaşılır
- ✅ API fonksiyonları çalıştı
- ✅ Entegrasyonlar başarılı

### **Hata Durumları:**
- ❌ Doküman oluşturulamadı
- ❌ Validasyon kontrolleri çalışmadı
- ❌ Stok güncellemeleri hatalı
- ❌ Hata mesajları görülmedi
- ❌ API fonksiyonları çalışmadı
- ❌ Entegrasyonlar başarısız

---

## 🔧 **Hata Giderme**

### **Yaygın Hatalar ve Çözümleri:**

#### **1. "Module not found" Hatası**
```bash
bench --site all clear-cache
bench --site all migrate
```

#### **2. "Field not found" Hatası**
- Custom field'ların yüklendiğini kontrol et
- Migration'ın tamamlandığını kontrol et

#### **3. "Permission denied" Hatası**
- Kullanıcı yetkilerini kontrol et
- Administrator olarak giriş yap

#### **4. "Validation failed" Hatası**
- Zorunlu alanların doldurulduğunu kontrol et
- Veri formatlarını kontrol et

---

## 📝 **Test Raporu**

### **Test Tarihi**: _______________
### **Test Eden**: _______________
### **Test Ortamı**: _______________

### **Test Sonuçları:**
- [ ] **TEST 1**: Profile Entry ✅/❌
- [ ] **TEST 2**: Profile Exit ✅/❌  
- [ ] **TEST 3**: Scrap Profile Entry ✅/❌
- [ ] **TEST 4**: Stok Validasyonu ✅/❌
- [ ] **TEST 5**: API Fonksiyonları ✅/❌
- [ ] **TEST 6**: Entegrasyonlar ✅/❌

### **Genel Değerlendirme:**
- [ ] **Başarılı**: Tüm testler geçti
- [ ] **Kısmen Başarılı**: Bazı testler geçti
- [ ] **Başarısız**: Çoğu test başarısız

### **Notlar ve Öneriler:**
_________________________________
_________________________________
_________________________________

---

## 🎯 **Sonraki Adımlar**

Test sonuçlarına göre:
1. **Başarılı**: Sistem production'a hazır
2. **Kısmen Başarılı**: Hatalar düzeltilmeli
3. **Başarısız**: Sistem yeniden gözden geçirilmeli

**Test tamamlandıktan sonra bu rehberi güncelleyin!**
