# Purchase Order - Material Request Child Item Filtreleme

## 🎯 Genel Bakış

Purchase Order oluştururken Material Request'ten ürün getirirken **generic child item filtreleme** desteği.

## ❌ Önceki Sorun

ERPNext'in standart implementasyonunda:
- ✅ "Malzeme Talebi Kalemi Seçimi" checkbox'ı VAR
- ✅ Alt tabloda itemlar görünüyor
- ❌ **Ancak filtreler stabil çalışmıyor!**
- ❌ Ürün grubu seçilince **tüm ürünler** geliyor

### Teknik Sebep:
```python
# ERPNext Standard (material_request.py)
def select_item(d):
    filtered_items = args.get("filtered_children", [])  # ← Boş geliyor!
    child_filter = d.name in filtered_children if filtered_items else True  # ← Her zaman True
    return qty < d.stock_qty and child_filter  # ← Filtre uygulanmıyor
```

## ✅ Çözüm: Generic Filtreleme Sistemi

### Backend
`purchase_order_material_request.py` - `make_purchase_order_with_filters()`
- Frappe'ın filtre formatını parse eder: `{'item_group': ['=', 'Montaj']}`
- Tüm Material Request Item fieldları filtrelenebilir
- 10 operatör desteği

### Frontend
`fixtures/purchase_order_client_script.json`
- `make_purchase_order` çağrılarını intercept eder
- Custom backend metodumuzu kullanır

## 📋 Kullanım

### Adım Adım:

1. **Purchase Order** → **"Öğeleri Burdan Al > Malzeme Talebi"**
2. Modal açılır
3. ✅ **"Malzeme Talebi Kalemi Seçimi"** checkbox'ını işaretle
4. 📊 Alt tabloda **tüm itemlar** görünür
5. **Filtre ekle**:
   - **"+ Yeni Filtre"** butonuna tıkla
   - Örnek: `Ürün Grubu (Malzeme Talebi Kalemi)` = `Montaj ve İzolasyon`
   - Tablo otomatik filtrelenir ✅
6. Material Request'leri seç
7. **"Ürünleri Getir"** tıkla
8. ✅ **Sadece filtrelenmiş ürünler gelir!**

### Filtre Örnekleri:

| Filtre | Operatör | Değer | Sonuç |
|--------|----------|-------|-------|
| Ürün Grubu | `=` | Montaj ve İzolasyon | Sadece bu gruptaki ürünler |
| Ürün Kodu | `like` | 102 | 102 içeren ürünler |
| Miktar | `>` | 100 | 100'den fazla olanlar |
| Ürün Grubu | `=` | PVC | Sadece PVC ürünleri |

### Birden Fazla Filtre:
```
Filtre 1: Ürün Grubu = "Montaj ve İzolasyon"
VE
Filtre 2: Miktar > 50
VE
Filtre 3: Tedarikçi = "ABC Ltd"
```

## 🔄 Karşılaştırma: Öncesi vs Sonrası

| Özellik | ERPNext Standard | Bizim Çözüm |
|---------|------------------|-------------|
| Checkbox | ✅ | ✅ |
| Alt tablo | ✅ | ✅ |
| Item seçimi | ✅ | ✅ |
| **Filtre çalışıyor** | ❌ **Stabil değil** | ✅ **%100 stabil** |
| Sadece `item_group` | ❌ | ✅ Tüm fieldlar |
| 10 operatör | ❌ | ✅ |
| Birden fazla filtre | ❌ | ✅ |

## 🛠️ Teknik Detaylar

### Desteklenen Operatörler:
- `=` - Eşittir
- `!=` - Eşit değildir
- `like` - İçerir (case-insensitive)
- `not like` - İçermez
- `in` - Listede var
- `not in` - Listede yok
- `>` - Büyüktür
- `<` - Küçüktür
- `>=` - Büyük eşittir
- `<=` - Küçük eşittir

### Filtrelenebilir Fieldlar:
Tüm Material Request Item fieldları:
- `item_code`, `item_name`, `item_group`
- `qty`, `stock_qty`, `ordered_qty`
- `warehouse`, `supplier`
- `description`, `brand`
- ... ve custom fieldlar

## 🧪 Test

### Test 1: Tek Filtre
```
1. Purchase Order aç
2. "Öğeleri Burdan Al > Malzeme Talebi"
3. Checkbox işaretle
4. Filtre: Ürün Grubu = "Montaj ve İzolasyon"
5. Material Request seç → "Ürünleri Getir"
✅ Sadece "Montaj ve İzolasyon" ürünleri gelir
```

### Test 2: İki Filtre
```
Filtre 1: Ürün Grubu = "Montaj ve İzolasyon"
Filtre 2: Miktar > 100
✅ Her iki filtreyi DE geçen ürünler gelir
```

### Test 3: Like Operatörü
```
Filtre: Ürün Kodu içerir "102"
✅ Ürün kodunda "102" geçen tüm ürünler gelir
```

## 📦 Kurulum

```bash
# Client Script import et
bench --site ozerpan.com import-doc apps/uretim_planlama/uretim_planlama/fixtures/purchase_order_client_script.json

# Cache temizle
bench clear-cache

# Tarayıcıda hard refresh
Ctrl + Shift + R
```

## 🔍 Troubleshooting

### Filtre hala çalışmıyor

1. Client Script enabled mi?
```bash
bench --site ozerpan.com console
>>> frappe.get_doc("Client Script", "Purchase Order-Material Request Filter Override").enabled
```

2. Cache temizle:
```bash
bench clear-cache
```

3. Tarayıcıda:
   - Hard refresh: `Ctrl + Shift + R`
   - Console açın (F12) - hata var mı?

### Test komutu:
```bash
bench --site ozerpan.com console
>>> from uretim_planlama.purchase_order_material_request import make_purchase_order_with_filters
>>> # Fonksiyon import ediliyorsa çalışıyor
```

## ✅ ERPNext Uyumluluğu

- ✅ ERPNext çekirdek dosyaları **değiştirilmedi**
- ✅ Standart `get_mapped_doc` kullanılıyor
- ✅ Tüm validations ve hooks korunuyor
- ✅ ERPNext upgrade'lerde sorun çıkmaz

## 📝 Notlar

- Stock Entry için de aynı çözüm uygulandı
- İki DocType'da da **aynı mantık** çalışıyor
- Tek fark: `make_stock_entry` vs `make_purchase_order`
- Kod tabanı temiz ve maintainable

---

**Artık Purchase Order'da da filtreleme %100 stabil çalışıyor!** 🎉


