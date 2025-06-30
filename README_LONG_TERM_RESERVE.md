# Uzun Vadeli Rezerv Kullanımı - Üretim Planlama

## Genel Bakış

Bu özellik, ERPNext tabanlı üretim planlama uygulamasında uzun vadeli rezervlerin (30+ gün teslim süreli siparişler) kısa vadeli üretim ihtiyaçları için kullanılmasını sağlar.

## Özellikler

### 1. Uzun Vadeli Rezerv Tespiti
- Teslim tarihi 30+ gün sonrası olan satış siparişlerindeki rezervler otomatik tespit edilir
- Bu rezervler "Uzun Vadeli Rezerv" sütununda gri renkle gösterilir

### 2. Kullanılabilirlik Kontrolü
- Stok açığı olan hammaddeler için uzun vadeli rezerv kullanımı önerilir
- Sistem otomatik olarak kullanılabilir miktarları hesaplar
- Kullanıcıya modal ile detaylı bilgi sunulur

### 3. Toplu Kullanım
- Birden fazla hammadde için aynı anda uzun vadeli rezerv kullanımı yapılabilir
- Kullanılan miktarlar otomatik olarak loglanır
- LongTermReserveUsage doctype'ında takip edilir

### 4. Otomatik Yenileme
- Uzun vadeli rezervden kullanılan miktarlar için otomatik satınalma talebi oluşturulur
- Material Request'te "Uzun vadeli rezervten kullanılan X adet Y malzeme yerine yenileme" açıklaması eklenir

## Kullanım

### Sales Order Formunda

1. **Gerekli Hammaddeler ve Stoklar** butonuna tıklayın
2. Tabloda "Uzun Vadeli Rezerv" ve "Kullanılan Rezerv" sütunlarını kontrol edin
3. Eğer açık miktar varsa ve uzun vadeli rezerv kullanılabilirse uyarı görünür
4. **Uzun Vadeli Rezerv Kontrolü** butonuna tıklayın
5. Modal'da kullanılacak miktarları belirleyin
6. **Uzun Vadeli Rezervden Kullan** butonuna tıklayın

### Takip ve Raporlama

1. **Long Term Reserve Usage** listesinden kullanımları takip edin
2. **Long Term Reserve Usage Report** raporundan detaylı analiz yapın
3. Dashboard widget'ından genel durumu görün

## Teknik Detaylar

### Backend Fonksiyonlar

- `get_long_term_reserve_qty(item_code)`: Uzun vadeli rezerv miktarını hesaplar
- `check_long_term_reserve_availability(sales_order)`: Kullanılabilirliği kontrol eder
- `use_long_term_reserve_bulk(sales_order, usage_data)`: Toplu kullanım yapar
- `create_material_request_for_shortages(sales_order)`: Otomatik yenileme talebi oluşturur

### Doctype'lar

- **LongTermReserveUsage**: Kullanım kayıtlarını tutar
- **Rezerved Raw Materials**: Mevcut rezerv sistemini destekler

### Hook'lar

- Sales Order submit/cancel: Rezerv oluşturma/silme
- Purchase Receipt submit: Uzun vadeli rezerv yenileme

## Güvenlik ve Doğrulama

- Kullanılan miktarlar otomatik loglanır
- Aynı eksik için tekrar kullanım yapılmaz
- Satınalma talebi karşılandığında otomatik yenileme yapılır
- Tüm işlemler izlenebilir ve raporlanabilir

## Kurulum

1. Uygulamayı yükleyin: `bench --site [site] install-app uretim_planlama`
2. Migrate edin: `bench --site [site] migrate`
3. Desk'te "Uretim Planlama" modülünü kontrol edin

## Test

```bash
bench --site [site] run-tests --module uretim_planlama.tests.test_long_term_reserve
```

## Destek

Herhangi bir sorun yaşarsanız lütfen geliştirici ile iletişime geçin. 