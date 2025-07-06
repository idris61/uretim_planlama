### Uretim Planlama

ERPNext tabanlı gelişmiş üretim planlama ve uzun vadeli rezerv yönetim sistemi.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app uretim_planlama
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/uretim_planlama
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit

---

## Özellikler ve Geliştirmeler (ERPNext v15 Uyumlu)

### 1. Gerekli Hammaddeler ve Stoklar Tablosu
- **Dinamik Tablo**: Satış Siparişi formunda, siparişe bağlı tüm hammaddelerin ihtiyaç, stok, rezerve, açık miktar, uzun vadeli rezerv ve tedarik durumunu gösteren gerçek zamanlı tablo
- **Otomatik Güncelleme**: BOM ve stok kayıtlarından otomatik veri çekme ve güncelleme
- **Toplu İşlemler**: Eksik hammaddeler için tek tıkla Satınalma Talebi (Material Request) oluşturma
- **Gelişmiş UI**: Kullanıcı dostu uyarılar, renk kodları, scroll bar ve sabit başlık satırı
- **Detay Görüntüleme**: Modal pencereler ile belge detayları ve linkler

### 2. Uzun Vadeli Rezerv Sistemi
- **Otomatik Tespit**: Teslim tarihi 30+ gün sonrası olan satış siparişlerindeki hammaddeler "Uzun Vadeli Rezerv" olarak otomatik tespit
- **Akıllı Öneriler**: Stok açığı olan hammaddeler için uzun vadeli rezervden kullanım önerisi
- **Toplu Kullanım**: Modal pencerede önerilen miktarları görüntüleme ve toplu rezerv kullanımı
- **Kayıt Sistemi**: Kullanımlar "Long Term Reserve Usage" doctype'ında detaylı loglama
- **Güvenlik**: Aynı satış siparişi ve hammadde için birden fazla kez uzun vadeli rezerv kullanımı engelleme
- **Otomatik Temizlik**: Satış siparişi iptal edildiğinde ilgili uzun vadeli rezerv kayıtları otomatik silme
- **Yenileme Sistemi**: Uzun vadeli rezervden kullanılan miktarlar için otomatik satınalma talebi oluşturma

### 3. Parent-Child Sipariş Yönetimi
- **Ana Sipariş Rezervi**: Parent siparişlerde uzun vadeli rezerv oluşturma
- **Child Sipariş Kullanımı**: Alt siparişlerde ana rezervden kullanım ve takip
- **Akıllı Hesaplama**: Child siparişlerde açık miktarın stok durumuna bakılmaksızın ihtiyacın tamamı olarak hesaplanması
- **Özet Görüntüleme**: Ana sipariş ve alt siparişlerdeki rezerv kullanım özeti
- **Temizleme Butonu**: "Kalan Uzun Vadeli Rezervi Temizle" butonu ile manuel temizlik

### 4. Backend Fonksiyonları
- `get_sales_order_raw_materials(sales_order)`: Siparişe bağlı tüm hammaddelerin detaylı stok ve ihtiyaç analizi
- `create_material_request_for_shortages(sales_order)`: Eksik hammaddeler ve rezerv yenilemeleri için toplu satınalma talebi
- `get_long_term_reserve_qty(item_code)`: Uzun vadeli rezerv miktarını hesaplama
- `check_long_term_reserve_availability(sales_order)`: Uzun vadeli rezervden kullanılabilir hammaddeleri ve önerilen miktarları listeleme
- `use_long_term_reserve_bulk(sales_order, usage_data)`: Toplu uzun vadeli rezerv kullanımı, tekrar kullanım engelleme
- `get_long_term_reserve_usage_summary(parent_sales_order)`: Ana sipariş rezerv kullanım özeti
- **Otomatik Temizlik**: Satış siparişi iptalinde ilgili rezerv ve uzun vadeli rezerv kayıtları otomatik silme
- **Stok Hareketi Entegrasyonu**: Stock Entry işlemlerinde rezerv kullanımı otomatik güncelleme

### 5. Frontend (JavaScript) Özellikleri
- **Dinamik Tablo**: Satış Siparişi formunda özel butonlar ve gerçek zamanlı tablo rendering
- **Modal Sistemleri**: "Detayları Gör", "Uzun Vadeli Rezervden Kullan" gibi kullanıcı dostu modal pencereler
- **Akıllı Kontroller**: Tablo ve butonlar sadece kayıtlı siparişlerde aktif, kaydedilmemiş siparişlerde uyarı
- **Otomatik Yenileme**: Tüm işlemlerden sonra tablo otomatik güncelleme
- **Responsive Tasarım**: Scroll bar, sabit başlık satırı ve optimize edilmiş tablo yüksekliği

### 6. Doctype'lar ve Yapılar
- **Long Term Reserve Usage**: Uzun vadeli rezerv kullanım kayıtları
- **Deleted Long Term Reserve**: Silinen rezervler için kalıcı kayıt sistemi
- **Rezerved Raw Materials**: Mevcut rezerv sistemini destekleyen yapı
- **Parent-Child İlişkisi**: Ana sipariş ve alt siparişler arasında rezerv paylaşımı

### 7. Raporlama ve Takip
- **Long Term Reserve Usage Report**: Uzun vadeli rezerv kullanımları için detaylı rapor
- **Dashboard Widget**: Genel durum görüntüleme
- **Kullanım Özeti**: Ana sipariş ve alt siparişlerdeki rezerv kullanım özeti
- **Detaylı Loglama**: Tüm işlemlerin izlenebilir ve raporlanabilir olması

### 8. Güvenlik ve Doğrulama
- **Backend Doğrulama**: Tüm kritik işlemler (rezerv kullanımı, talep oluşturma, silme) backend'de doğrulanır
- **Hata Yönetimi**: Kullanıcı hatalarına karşı uyarı ve engelleme mekanizmaları
- **İzlenebilirlik**: Tüm işlemler loglanır ve raporlanabilir
- **Veri Tutarlılığı**: Parent-child ilişkilerinde veri tutarlılığı kontrolü

### 9. Performans Optimizasyonları
- **SQL Optimizasyonu**: Veritabanı sorgularında performans iyileştirmeleri
- **Bellek Yönetimi**: Büyük veri setlerinde bellek kullanımı optimizasyonu
- **Caching**: Sık kullanılan veriler için önbellekleme
- **Batch İşlemler**: Toplu işlemler için optimize edilmiş algoritmalar

### 10. Kurulum ve Test
- **Standart Kurulum**: Frappe/ERPNext uygulama kurulum adımları
- **Migration Sistemi**: Veritabanı değişiklikleri için otomatik migration
- **Test Suite**: Uzun vadeli rezerv sistemi için kapsamlı testler
- **Örnek Veri**: Test ve demo için örnek veri setleri

### 11. Çeviri Desteği
- **Türkçe Çeviriler**: Tüm kullanıcı arayüzü metinleri Türkçe çevirileri ile
- **Dinamik Çeviri**: Yeni eklenen özellikler için otomatik çeviri desteği
- **Çoklu Dil**: Gelecekte çoklu dil desteği için hazır yapı

---

## Teknik Detaylar

### Sistem Gereksinimleri
- ERPNext v15+
- Python 3.10+
- MariaDB 10.6+
- Node.js 18+

### Veritabanı Yapısı
- Uzun vadeli rezerv hesaplamaları için optimize edilmiş SQL sorguları
- Parent-child ilişkileri için özel indeksler
- Performans için materialized view'lar

### API Endpoints
- RESTful API desteği
- Webhook entegrasyonları
- Third-party sistem entegrasyonları

---

Daha fazla bilgi ve teknik detay için `README_LONG_TERM_RESERVE.md` dosyasına bakınız.
