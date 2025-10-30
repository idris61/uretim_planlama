# Stock Entry - Material Request Child Item Filtreleme

## Genel Bakış

Bu özellik, Stock Entry oluştururken Material Request'ten ürün getirirken child item filtreleme (örn: Product Group) desteği ekler.

ERPNext'in standart işleyişi child item filtrelerini desteklemediği için, bu çözüm:
- ✅ ERPNext çekirdek kodlarına **dokunmaz**
- ✅ Standart `get_mapped_doc` yapısını kullanır
- ✅ Frontend'de `map_current_doc` fonksiyonunu wrap eder
- ✅ Backend'de filtreleme mantığını uygular

## Mimari

### Frontend (Client Script)
**Dosya:** `fixtures/client_script.json`

ERPNext'in `erpnext.utils.map_current_doc` fonksiyonunu wrap eder:
- Sadece Material Request → Stock Entry işlemlerini intercept eder
- Custom backend metodumuzu çağırır
- Child item filtreleme parametrelerini ekler

```javascript
// Material Request -> Stock Entry işlemini yakalar
if (opts.method === "erpnext.stock.doctype.material_request.material_request.make_stock_entry") {
    opts.method = "uretim_planlama.stock_entry_material_request.make_stock_entry_with_filters";
    opts.allow_child_item_selection = true;
}
```

### Backend (Python)
**Dosya:** `stock_entry_material_request.py`

ERPNext'in standart `make_stock_entry` fonksiyonunu taklit eder:
- `get_mapped_doc` kullanarak ERPNext standartlarına uygun çalışır
- `condition` fonksiyonu ile filtreleme yapar
- Tüm ERPNext validations ve hooks'ları korur

```python
def should_include_item(doc):
    # Kalan miktar kontrolü (ERPNext standard)
    if flt(doc.ordered_qty) >= flt(doc.stock_qty):
        return False
    
    # Filtre kontrolü (bizim eklememiz)
    if filter_field and filter_value:
        if getattr(doc, filter_field) != filter_value:
            return False
    
    return True
```

## Kullanım

### 📋 **"Malzeme Talebi Kalemi Seçimi" Checkbox'ı**

Stock Entry → "Get Items From > Material Request" dialog'unda artık **Purchase Order ile aynı** özellikler var:

1. Stock Entry sayfasında **"Get Items From > Material Request"** butonuna tıklayın
2. Dialog açılır, "İşlem" olarak **"Malzeme Transferi"** seçin
3. ✅ **"Malzeme Talebi Kalemi Seçimi"** checkbox'ını işaretleyin
   - Bu checkbox işaretlenince alt tabloda **Material Request itemları** görünür
   - Her item için: `Item Code`, `Item Name`, `Item Group`, `Qty`, `UOM` gösterilir
4. **Filtre uygulayın** (opsiyonel):
   - **"+ Yeni Filtre"** butonuna tıklayın
   - Örnek: `Ürün Grubu (Malzeme Talebi Kalemi)` = `Montaj ve İzolasyon`
   - Tablo otomatik olarak filtrelenir
5. İstediğiniz Material Request'leri veya belirli itemları seçin
6. **"Ürünleri Getir"** butonuna tıklayın
7. ✅ Sadece seçili/filtrelenmiş ürünler Stock Entry'e eklenecektir

### 🔄 **Purchase Order ile Karşılaştırma**

| Özellik | Purchase Order | Stock Entry (Bizim Çözüm) |
|---------|----------------|---------------------------|
| "Malzeme Talebi Kalemi Seçimi" checkbox | ✅ | ✅ |
| Alt tabloda item listesi | ✅ | ✅ |
| Item bazında seçim | ✅ | ✅ |
| Filtre desteği | ✅ | ✅ **+ 10 operatör** |
| Birden fazla filtre | ❌ | ✅ |
| Generic filtreleme | ❌ | ✅ |

## Desteklenen Filtreler

✅ **Tüm Material Request Item fieldları filtrelenebilir!**

Sistem **generic** olarak tasarlandı. Frappe'ın MultiSelectDialog'unda uyguladığınız herhangi bir filtre otomatik olarak çalışır:

### Örnek Filtreler:

| Alan | Operatör | Örnek Değer | Kullanım |
|------|----------|-------------|----------|
| `item_group` | `=` | `Montaj ve İzolasyon` | Belirli ürün grubu |
| `item_code` | `like` | `102` | İçeren ürün kodu |
| `item_name` | `like` | `Montaj` | İçeren ürün adı |
| `supplier` | `=` | `ABC Ltd` | Belirli tedarikçi |
| `qty` | `>` | `100` | Miktarı büyük olanlar |
| `qty` | `<` | `50` | Miktarı küçük olanlar |
| `warehouse` | `=` | `Depo 1` | Belirli depo |

### Desteklenen Operatörler:

| Operatör | Açıklama | Örnek |
|----------|----------|-------|
| `=` | Eşittir | Ürün Grubu = "Montaj" |
| `!=` | Eşit değildir | Ürün Grubu != "PVC" |
| `like` | İçerir (case-insensitive) | Ürün Kodu içerir "102" |
| `not like` | İçermez | Ürün Adı içermez "Test" |
| `in` | Listede var | Depo in ["Depo 1", "Depo 2"] |
| `not in` | Listede yok | Ürün Grubu not in ["X", "Y"] |
| `>` | Büyüktür | Miktar > 100 |
| `<` | Küçüktür | Miktar < 50 |
| `>=` | Büyük eşittir | Miktar >= 100 |
| `<=` | Küçük eşittir | Miktar <= 50 |

### Birden Fazla Filtre (VE Mantığı):

```
Filtre 1: Ürün Grubu = "Montaj ve İzolasyon"
VE
Filtre 2: Miktar > 100
VE
Filtre 3: Depo = "ÜRETİM DEPO"
```

Tüm filtreler **VE** mantığı ile uygulanır. Bir item'ın dahil edilmesi için **tüm filtreleri** geçmesi gerekir.

## ERPNext Uyumluluğu

Bu çözüm ERPNext'in çekirdek işleyişini **bozmaz**:

| Özellik | ERPNext Standard | Bizim Çözüm |
|---------|------------------|-------------|
| get_mapped_doc kullanımı | ✅ | ✅ |
| Validation hooks | ✅ | ✅ |
| Field mapping | ✅ | ✅ |
| Warehouse logic | ✅ | ✅ |
| Qty calculations | ✅ | ✅ |
| **Child item filtering** | ❌ | ✅ |

## Test Senaryoları

### Test 1: Tek Filtre (Ürün Grubu)
```bash
# 1. Stock Entry aç
# 2. "Get Items From > Material Request"
# 3. Filtre: Ürün Grubu (Malzeme Talebi Kalemi) = "Montaj ve İzolasyon"
# 4. Material Request seç → "Ürünleri Getir"
# ✅ Sonuç: Sadece "Montaj ve İzolasyon" ürünleri gelir
```

### Test 2: İki Filtre (Ürün Grubu + Miktar)
```bash
# 1. Stock Entry aç
# 2. "Get Items From > Material Request"
# 3. Filtre 1: Ürün Grubu = "Montaj ve İzolasyon"
# 4. Filtre 2: Miktar (Malzeme Talebi Kalemi) > 100
# 5. Material Request seç → "Ürünleri Getir"
# ✅ Sonuç: "Montaj ve İzolasyon" VE Miktar > 100 olan ürünler gelir
```

### Test 3: Like Operatörü (Ürün Kodu)
```bash
# 1. Stock Entry aç
# 2. "Get Items From > Material Request"
# 3. Filtre: Ürün Kodu (Malzeme Talebi Kalemi) içerir "102"
# 4. Material Request seç → "Ürünleri Getir"
# ✅ Sonuç: Ürün kodunda "102" geçen tüm ürünler gelir
```

### Test 4: Sayısal Karşılaştırma
```bash
# 1. Stock Entry aç
# 2. "Get Items From > Material Request"
# 3. Filtre: Miktar (Malzeme Talebi Kalemi) < 50
# 4. Material Request seç → "Ürünleri Getir"
# ✅ Sonuç: Miktarı 50'den küçük ürünler gelir
```

### Kurulum ve Test:
```bash
# Client Script'i import et
bench --site ozerpan.com import-doc apps/uretim_planlama/uretim_planlama/fixtures/client_script.json

# Cache'i temizle
bench clear-cache

# Tarayıcıda hard refresh
# Ctrl + Shift + R
```

## Troubleshooting

### Filtre çalışmıyor
1. Client Script'in enabled olduğunu kontrol edin:
   ```bash
   bench --site ozerpan.com console
   >>> frappe.get_doc("Client Script", "Stock Entry-Material Request Filter Override").enabled
   ```

2. Cache'i temizleyin:
   ```bash
   bench clear-cache
   ```

3. Tarayıcıda hard refresh yapın: `Ctrl + Shift + R`

### Backend hatası
Python kodunu kontrol edin:
```bash
bench --site ozerpan.com console
>>> from uretim_planlama.stock_entry_material_request import make_stock_entry_with_filters
```

## Bakım

- ✅ ERPNext upgrade'lerinde kontrol edilmeli
- ✅ `erpnext.utils.map_current_doc` signature değişirse güncellenmeli
- ✅ Yeni filtre tipleri eklenebilir

## Katkıda Bulunanlar

- Ozerpan ERP Team
- Tarih: 2025-10-30

