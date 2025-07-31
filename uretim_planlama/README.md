# Accessory Delivery Package (Aksesuar Teslimat Paketi)

## Amaç & Akış Özeti
Bu modül, üretim veya satış siparişi bazlı olarak depo personelinin ilgili hammaddeleri ya da aksesuarları kolayca görüp teslimat işlemleri yapmasını sağlar. Sipariş veya üretim planı onaylandığında otomatik rezerve edilen hammaddeler, iş emri tamamlandığında veya stok hareketlerinde güncellenir/silinir. Kod geliştirmeleri clean code prensipleriyle ve ERPNext'ın temel yapısına sadık kalınarak yürütülür.

**Kısaca iş akışı:**
1. Satış/Sipariş onayında: Sipariş için gerekli hammaddeler BOM'dan belirlenir, her birine rezerv kaydı oluşturulur.
2. İş emri veya üretim tamamlanınca: Harcanan hammaddeler miktarınca rezerv kayıtlarından düşülür, kalan sıfır/negatif rezervler arka planda temizlenir.
3. Tüm işlemler veritabanı gerçek miktarlarıyla (float/decimal olarak) yapılır, yuvarlama veya tolerans uygulanmaz.


## Özellikler
- OpTi No veya Sales Order ile sorgulama
- MLY dosyasından malzeme listesi çekme (API ile entegre edilecek)
- Malzemelerle teslimat paketi oluşturma
- Teslim edilen kişi, teslim eden kullanıcı ve tarih kaydı
- Not ekleyebilme

## Doctype'lar
### Accessory Delivery Package
- **opti_no**: Link (Production Plan)
- **sales_order**: Link (Sales Order)
- **item_list**: Child Table (Accessory Delivery Package Item)
- **delivered_to**: Data (veya ileride Link)
- **delivered_by**: Link (User, otomatik session user)
- **delivery_date**: Datetime (otomatik now)
- **notes**: Text

### Accessory Delivery Package Item (Child Table)
- **item_code**: Link (Item)
- **item_name**: Data
- **qty**: Float
- **uom**: Link (UOM)

## Kurulum
1. Doctype JSON dosyalarını yükleyin veya migrate edin.
2. Gerekirse çevirileri `translations/tr.csv` dosyasına ekleyin.
3. Backend fonksiyonları ve özel sayfa için ilgili dosyaları oluşturun.

## Geliştirme Notları
- Tüm geliştirmeler `uretim_planlama` app'i içinde yapılmalıdır.
- Kodlar clean code prensiplerine uygun olmalı, gereksiz method eklenmemelidir.
- ERPNext/Frappe core fonksiyonları override edilmemelidir.

## Çeviri
Alan ve doctype isimlerinin Türkçe karşılıkları `translations/tr.csv` dosyasına eklenmelidir.

---
Daha fazla bilgi için proje yöneticisine veya geliştiriciye danışınız. 