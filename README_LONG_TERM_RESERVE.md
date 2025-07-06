# Uzun Vadeli Rezerv Kullanımı - Üretim Planlama

## Genel Bakış

Bu özellik, ERPNext tabanlı üretim planlama uygulamasında uzun vadeli rezervlerin (30+ gün teslim süreli siparişler) kısa vadeli üretim ihtiyaçları için kullanılmasını sağlar. Sistem, parent-child sipariş ilişkilerini destekleyerek ana siparişlerdeki rezervlerin alt siparişlerde kullanılmasına olanak tanır.

## Özellikler

### 1. Uzun Vadeli Rezerv Tespiti
- Teslim tarihi 30+ gün sonrası olan satış siparişlerindeki rezervler otomatik tespit edilir
- Bu rezervler "Uzun Vadeli Rezerv" sütununda gri renkle gösterilir
- Parent-child ilişkilerinde ana sipariş rezervleri alt siparişlerde kullanılabilir

### 2. Kullanılabilirlik Kontrolü
- Stok açığı olan hammaddeler için uzun vadeli rezerv kullanımı önerilir
- Sistem otomatik olarak kullanılabilir miktarları hesaplar
- Kullanıcıya modal ile detaylı bilgi sunulur
- Parent-child ilişkilerinde ana rezervden kullanım önceliği

### 3. Toplu Kullanım
- Birden fazla hammadde için aynı anda uzun vadeli rezerv kullanımı yapılabilir
- Kullanılan miktarlar otomatik olarak loglanır
- LongTermReserveUsage doctype'ında takip edilir
- Parent-child ilişkilerinde parent_sales_order referansı eklenir

### 4. Otomatik Yenileme
- Uzun vadeli rezervden kullanılan miktarlar için otomatik satınalma talebi oluşturulur
- Material Request'te "Uzun vadeli rezervten kullanılan X adet Y malzeme yerine yenileme" açıklaması eklenir
- Satınalma fişi karşılandığında otomatik rezerv yenileme

### 5. Parent-Child Sipariş Yönetimi
- Ana siparişlerde uzun vadeli rezerv oluşturma
- Alt siparişlerde ana rezervden kullanım ve takip
- Akıllı hesaplama: Child siparişlerde açık miktarın stok durumuna bakılmaksızın ihtiyacın tamamı olarak hesaplanması
- Özet görüntüleme: Ana sipariş ve alt siparişlerdeki rezerv kullanım özeti
- Temizleme butonu: "Kalan Uzun Vadeli Rezervi Temizle" butonu ile manuel temizlik

## Kullanım

### Sales Order Formunda

1. **Gerekli Hammaddeler ve Stoklar** butonuna tıklayın
2. Tabloda "Uzun Vadeli Rezerv" ve "Kullanılan Rezerv" sütunlarını kontrol edin
3. Eğer açık miktar varsa ve uzun vadeli rezerv kullanılabilirse uyarı görünür
4. **Uzun Vadeli Rezerv Kontrolü** butonuna tıklayın
5. Modal'da kullanılacak miktarları belirleyin
6. **Uzun Vadeli Rezervden Kullan** butonuna tıklayın

### Parent-Child Sipariş Yönetimi

1. Ana siparişte uzun vadeli rezerv oluşturulur
2. Alt siparişlerde ana rezervden kullanım yapılır
3. Kullanım özeti modal'ında detaylar görüntülenir
4. Gerektiğinde manuel temizlik yapılabilir

### Takip ve Raporlama

1. **Long Term Reserve Usage** listesinden kullanımları takip edin
2. **Long Term Reserve Usage Report** raporundan detaylı analiz yapın
3. Dashboard widget'ından genel durumu görün
4. Ana sipariş özet modal'ından parent-child kullanımları takip edin

## Teknik Detaylar

### Backend Fonksiyonlar

- `get_long_term_reserve_qty(item_code)`: Uzun vadeli rezerv miktarını hesaplar
- `check_long_term_reserve_availability(sales_order)`: Kullanılabilirliği kontrol eder
- `use_long_term_reserve_bulk(sales_order, usage_data)`: Toplu kullanım yapar
- `create_material_request_for_shortages(sales_order)`: Otomatik yenileme talebi oluşturur
- `get_long_term_reserve_usage_summary(parent_sales_order)`: Ana sipariş rezerv kullanım özeti
- `upsert_long_term_reserve_usage(sales_order, item_code, qty, is_long_term_child, parent_sales_order)`: Kullanım kaydı ekler/günceller
- `release_reservations_on_stock_entry(doc, method)`: Stok hareketlerinde rezerv kullanımı
- `delete_long_term_reserve_usage_on_cancel(doc, method)`: İptal edilen siparişlerde temizlik

### Doctype'lar

- **LongTermReserveUsage**: Kullanım kayıtlarını tutar
  - sales_order: Satış Siparişi
  - parent_sales_order: Ana Satış Siparişi (child siparişler için)
  - item_code: Hammadde
  - used_qty: Kullanılan Miktar
  - usage_date: Kullanım Tarihi
  - status: Durum (Aktif/Yenilendi)
- **Deleted Long Term Reserve**: Silinen rezervler için kalıcı kayıt
  - sales_order: Satış Siparişi
  - item_code: Hammadde
  - quantity: Miktar
  - deleted_by: Silen
  - deleted_at: Silinme Tarihi
  - reason: Sebep
- **Rezerved Raw Materials**: Mevcut rezerv sistemini destekler

### Hook'lar

- Sales Order submit/cancel: Rezerv oluşturma/silme
- Purchase Receipt submit: Uzun vadeli rezerv yenileme
- Stock Entry submit: Rezerv kullanımı güncelleme

### Veritabanı Yapısı

```sql
-- Uzun vadeli rezerv hesaplama
SELECT SUM(rrm.quantity)
FROM `tabRezerved Raw Materials` rrm
INNER JOIN `tabSales Order` so ON rrm.sales_order = so.name
WHERE rrm.item_code = %s AND so.delivery_date >= %s

-- Kullanım detayları
SELECT ltru.sales_order, ltru.used_qty, ltru.usage_date, 
       so.customer, IFNULL(so.custom_end_customer, '') as custom_end_customer
FROM `tabLong Term Reserve Usage` ltru
INNER JOIN `tabSales Order` so ON ltru.sales_order = so.name
WHERE ltru.item_code = %s
```

## Güvenlik ve Doğrulama

- Kullanılan miktarlar otomatik loglanır
- Aynı eksik için tekrar kullanım yapılmaz
- Satınalma talebi karşılandığında otomatik yenileme yapılır
- Tüm işlemler izlenebilir ve raporlanabilir
- Parent-child ilişkilerinde veri tutarlılığı kontrolü
- Stok hareketlerinde rezerv kullanımı otomatik güncelleme

## Performans Optimizasyonları

- SQL sorgularında indeks kullanımı
- Büyük veri setlerinde batch işlemler
- Bellek kullanımı optimizasyonu
- Caching mekanizmaları

## Hata Yönetimi

- UnboundLocalError düzeltmeleri
- Eksik veri kontrolü
- Kullanıcı dostu hata mesajları
- Detaylı loglama

## Kurulum

1. Uygulamayı yükleyin: `bench --site [site] install-app uretim_planlama`
2. Migrate edin: `bench --site [site] migrate`
3. Desk'te "Uretim Planlama" modülünü kontrol edin
4. Gerekli izinleri ayarlayın

## Test

```bash
bench --site [site] run-tests --module uretim_planlama.tests.test_long_term_reserve
```

## Çeviri Desteği

Tüm kullanıcı arayüzü metinleri Türkçe çevirileri ile desteklenir:
- Doctype alanları
- Modal pencereler
- Hata mesajları
- Rapor başlıkları
- Buton metinleri

## Destek

Herhangi bir sorun yaşarsanız lütfen geliştirici ile iletişime geçin. 

## Gelecek Geliştirmeler

- Parent-child ilişkisi olmayan bağımsız siparişlerde rezerv kullanımı
- Gelişmiş raporlama özellikleri
- API entegrasyonları
- Mobil uygulama desteği 