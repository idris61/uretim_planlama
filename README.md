# Üretim Planlama (Uretim Planlama)

ERPNext tabanlı üretim planlama uygulaması

## 🚀 **YENİ ÖZELLİK: PROFESYONEL PROFİL STOK YÖNETİMİ**

### **Genel Bakış**
Bu uygulama, profil ürünlerinin hem ERPNext orijinal stok takibinde (mtül) hem de özel boy bazında stok takibinde senkronize olarak yönetilmesini sağlar.

### **Temel Özellikler**
- ✅ **Merkezi Profil Stok Yönetimi**: Tüm profil stok işlemleri tek yerden yönetilir
- ✅ **ERPNext Stok Senkronizasyonu**: Orijinal ERPNext stok sistemi ile tam uyumlu
- ✅ **Boy Bazında Detaylı Takip**: Her profil boy için ayrı stok takibi
- ✅ **Çoklu Doküman Desteği**: Tüm ERPNext dokümanlarında profil stok yönetimi
- ✅ **Otomatik Stok Güncelleme**: Giriş/çıkış işlemlerinde otomatik stok güncelleme
- ✅ **Hata Yönetimi ve Loglama**: Kapsamlı hata takibi ve loglama sistemi

### **Desteklenen Dokümanlar**
| Doküman Türü | Stok Girişi | Stok Çıkışı | Rezervasyon | Doğrulama |
|---------------|--------------|-------------|-------------|-----------|
| **Alış İrsaliyesi** | ✅ | ✅ (İptal) | - | ✅ |
| **Satınalma Faturası** | ✅ | - | - | ✅ |
| **Stok Girişi** | ✅ | - | - | ✅ |
| **Satış Siparişi** | - | - | ✅ | ✅ |
| **Sevk İrsaliyesi** | ✅ (İptal) | ✅ | - | ✅ |
| **Satış Faturası** | ✅ (İptal) | ✅ | - | ✅ |
| **Stok Çıkışı** | ✅ (İptal) | ✅ | - | ✅ |
| **Malzeme Talebi** | - | - | ✅ | ✅ |

### **Teknik Mimari**

#### **1. Merkezi Profil Stok Yönetici (`profile_stock_manager.py`)**
- Profil ürün kontrolü
- MTÜL hesaplama
- ERPNext stok güncelleme
- Profile Stock Ledger güncelleme
- Hata yönetimi ve loglama

#### **2. Event Handler'lar (`doctype_events.py`)**
- Tüm dokümanlar için profil stok event'leri
- Giriş/çıkış işlemleri
- İptal işlemleri
- Doğrulama işlemleri

#### **3. API Fonksiyonları (`profile_stock_api.py`)**
- Stok özeti
- Boy bazında stok bilgisi
- Stok yeterlilik kontrolü
- Hareket geçmişi
- Stok uyarıları

### **Kullanım Senaryoları**

#### **Alış İşlemi (Stok Girişi)**
1. Alış irsaliyesi oluşturulur
2. Profil ürünler için `custom_is_profile` işaretlenir
3. `custom_profile_length_m` (boy) ve `custom_profile_length_qty` (adet) girilir
4. Doküman onaylandığında:
   - ERPNext stok sistemi güncellenir (mtül)
   - Profile Stock Ledger güncellenir (boy bazında)
   - Her iki sistem senkronize olur

#### **Satış İşlemi (Stok Çıkışı)**
1. Sevk irsaliyesi oluşturulur
2. Profil ürünler için boy ve adet bilgileri girilir
3. Doküman onaylandığında:
   - ERPNext stok sistemi güncellenir (mtül)
   - Profile Stock Ledger güncellenir (boy bazında)
   - Stok yeterliliği kontrol edilir

#### **Stok Kontrolü**
- API fonksiyonları ile gerçek zamanlı stok kontrolü
- Boy bazında stok yeterliliği
- Düşük stok uyarıları
- Hareket geçmişi takibi

### **Kurulum ve Konfigürasyon**

#### **1. Custom Field'lar**
Aşağıdaki custom field'lar otomatik olarak yüklenir:
- `custom_is_profile`: Profil ürün kontrolü
- `custom_profile_length_m`: Boy bilgisi
- `custom_profile_length_qty`: Adet bilgisi

#### **2. Event Hook'ları**
`hooks.py` dosyasında tüm gerekli event hook'ları tanımlanmıştır.

#### **3. Profil Ürün Grupları**
Varsayılan olarak `PVC` ve `Camlar` ürün grupları profil olarak kabul edilir.

### **API Kullanımı**

#### **Stok Özeti**
```python
import frappe
result = frappe.call('uretim_planlama.uretim_planlama.profile_stock_api.get_profile_stock_overview')
```

#### **Stok Yeterlilik Kontrolü**
```python
result = frappe.call('uretim_planlama.uretim_planlama.profile_stock_api.check_profile_availability', 
                    item_code='PROFIL-001', 
                    required_length=5.0, 
                    required_qty=10)
```

#### **Hareket Geçmişi**
```python
result = frappe.call('uretim_planlama.uretim_planlama.profile_stock_api.get_profile_transaction_history',
                    profile_type='PROFIL-001',
                    from_date='2025-01-01',
                    to_date='2025-12-31')
```

### **Hata Yönetimi**
- Tüm işlemler try-catch blokları ile korunur
- Hatalar `frappe.log_error` ile loglanır
- Kullanıcıya anlaşılır hata mesajları gösterilir
- İşlem başarısı/başarısızlığı detaylı olarak raporlanır

### **Performans Optimizasyonu**
- Gereksiz veritabanı sorguları minimize edilir
- Batch işlemler için optimize edilmiş fonksiyonlar
- Cache mekanizmaları ile hızlı erişim
- Asenkron işlem desteği

### **Güvenlik**
- Tüm API fonksiyonları `@frappe.whitelist()` ile korunur
- Kullanıcı yetki kontrolü
- SQL injection koruması
- Veri doğrulama ve sanitizasyon

### **Test ve Doğrulama**
- Her doküman türü için ayrı test senaryoları
- Stok tutarlılığı kontrolü
- Hata durumları test edilir
- Performans testleri

### **Gelecek Geliştirmeler**
- [ ] Dashboard widget'ları
- [ ] E-posta uyarıları
- [ ] Mobil uygulama desteği
- [ ] Gelişmiş raporlama
- [ ] API rate limiting
- [ ] Webhook desteği

---

## 📋 **Genel Uygulama Özellikleri**

### **Üretim Planlama Paneli**
- Haftalık üretim planı görünümü
- Opti numarası bazında planlama
- Kaynak yönetimi ve iş yükü dağılımı

### **Üretim Takip Sistemi**
- Gerçek zamanlı üretim durumu
- İş emri takibi
- Performans metrikleri

### **Stok Yönetimi**
- Hammadde rezervasyonu
- Stok yeterlilik analizi
- Profil stok takibi (boy bazında)

### **Entegrasyon**
- ERPNext ile tam uyumluluk
- REST API desteği
- Webhook entegrasyonları

## 🛠️ **Kurulum**

```bash
# Uygulamayı yükle
bench get-app uretim_planlama

# Uygulamayı kur
bench install-app uretim_planlama

# Migrate
bench migrate
```

## 📚 **Dokümantasyon**

Detaylı dokümantasyon için [Wiki](https://github.com/idris/uretim_planlama/wiki) sayfasını ziyaret edin.

## 🤝 **Katkıda Bulunma**

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 **Lisans**

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `license.txt` dosyasına bakın.

## 📞 **İletişim**

- **Geliştirici**: idris
- **E-posta**: idris.gemici61@gmail.com
- **Proje Linki**: [GitHub Repository](https://github.com/idris/uretim_planlama)
