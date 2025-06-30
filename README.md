### Uretim Planlama

Uretim Planlama Sayfası

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
- Satış Siparişi formunda, siparişe bağlı tüm hammaddelerin ihtiyaç, stok, rezerve, açık miktar, uzun vadeli rezerv ve tedarik durumunu gösteren dinamik bir tablo sunar.
- Tablo, BOM ve stok kayıtlarından gerçek zamanlı verilerle otomatik güncellenir.
- Eksik hammaddeler için tek tıkla Satınalma Talebi (Material Request) oluşturulabilir.
- Kullanıcı dostu uyarılar, renk kodları ve profesyonel tablo tasarımı içerir.

### 2. Uzun Vadeli Rezerv Sistemi
- Teslim tarihi 30+ gün sonrası olan satış siparişlerindeki hammaddeler "Uzun Vadeli Rezerv" olarak otomatik tespit edilir.
- Stok açığı olan hammaddeler için uzun vadeli rezervden kullanım önerisi sunulur.
- Kullanıcı, önerilen miktarları modal pencerede görebilir ve toplu olarak rezervden kullanabilir.
- Kullanımlar "Long Term Reserve Usage" doctype'ında loglanır ve raporlanabilir.
- Aynı satış siparişi ve hammadde için birden fazla kez uzun vadeli rezerv kullanımı engellenir.
- Satış siparişi iptal edildiğinde ilgili uzun vadeli rezerv kayıtları otomatik silinir.
- Uzun vadeli rezervden kullanılan miktarlar için otomatik yenileme satınalma talebi oluşturulabilir.

### 3. Backend Fonksiyonları
- `get_sales_order_raw_materials(sales_order)`: Siparişe bağlı tüm hammaddelerin detaylı stok ve ihtiyaç analizini döner.
- `create_material_request_for_shortages(sales_order)`: Eksik hammaddeler ve rezerv yenilemeleri için toplu satınalma talebi oluşturur.
- `get_long_term_reserve_qty(item_code)`: Uzun vadeli rezerv miktarını hesaplar.
- `check_long_term_reserve_availability(sales_order)`: Uzun vadeli rezervden kullanılabilir hammaddeleri ve önerilen miktarları listeler.
- `use_long_term_reserve_bulk(sales_order, usage_data)`: Toplu uzun vadeli rezerv kullanımı yapar, tekrar kullanım engellenir.
- Satış siparişi iptalinde ilgili rezerv ve uzun vadeli rezerv kayıtları otomatik silinir.

### 4. Frontend (JS) Özellikleri
- Satış Siparişi formunda özel butonlar ve dinamik tablo rendering.
- "Detayları Gör" ve "Uzun Vadeli Rezervden Kullan" gibi kullanıcı dostu modal ve aksiyonlar.
- Tablo ve butonlar sadece kayıtlı siparişlerde aktif olur, kaydedilmemiş siparişlerde uyarı gösterir.
- Tüm işlemlerden sonra tablo otomatik güncellenir.

### 5. Raporlama ve Takip
- Uzun vadeli rezerv kullanımları ve yenilemeleri için özel rapor ve dashboard widget'ı.
- "Long Term Reserve Usage Report" ile geçmiş rezerv kullanımlarının detaylı analizi.

### 6. Güvenlik ve Doğrulama
- Tüm kritik işlemler (rezerv kullanımı, talep oluşturma, silme) backend'de doğrulanır.
- Kullanıcı hatalarına karşı uyarı ve engelleme mekanizmaları.
- Tüm işlemler izlenebilir ve raporlanabilir.

### 7. Kurulum ve Test
- Standart Frappe/ERPNext uygulama kurulum adımları geçerlidir.
- Uzun vadeli rezerv sistemi için özel testler ve örnek veri setleri mevcuttur.

---

Daha fazla bilgi ve teknik detay için `README_LONG_TERM_RESERVE.md` dosyasına bakınız.
