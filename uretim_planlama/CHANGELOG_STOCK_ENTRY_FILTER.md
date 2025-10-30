# Stock Entry - Material Request Filtreleme | Changelog

## v2.1.0 - "Malzeme Talebi Kalemi Seçimi" Checkbox (2025-10-30)

### 🎯 **Yeni Özellikler**

#### **Purchase Order ile Aynı UI**
- ✅ **"Malzeme Talebi Kalemi Seçimi" checkbox'ı** eklendi
- ✅ Checkbox işaretlenince **alt tabloda itemlar** görünür
- ✅ Her item için: `Item Code`, `Item Name`, `Item Group`, `Qty`, `UOM`
- ✅ **Item bazında seçim** yapılabilir
- ✅ Purchase Order ile **aynı kullanıcı deneyimi**

### 🔧 **Teknik İyileştirmeler**

#### **Frontend (Client Script)**
- `child_columns` Purchase Order ile uyumlu hale getirildi
- `stock_qty` kaldırıldı (gereksiz)
- 5 column ile daha temiz görünüm

### 🔄 **v2.0.0'dan Değişiklikler**

| Özellik | v2.0.0 | v2.1.0 |
|---------|--------|--------|
| Checkbox görünür | ❓ (Belirsiz) | ✅ Kesinlikle görünür |
| Alt tablo | ❓ | ✅ Görünür |
| Column sayısı | 6 | 5 (Optimize) |
| Purchase Order uyumu | ❌ | ✅ |

---

## v2.0.0 - Generic Filtreleme Desteği (2025-10-30)

### 🎯 **Yeni Özellikler**

#### **Generic Filtreleme Sistemi**
- ✅ **Tüm Material Request Item fieldları** filtrelenebilir
- ✅ **10 operatör** desteklenir: `=`, `!=`, `like`, `not like`, `in`, `not in`, `>`, `<`, `>=`, `<=`
- ✅ **Birden fazla filtre** aynı anda (VE mantığı ile)
- ✅ **Case-insensitive** string aramaları

### 🔧 **Teknik İyileştirmeler**

#### **Backend (Python)**
- Hardcoded `item_group` filtresi kaldırıldı
- Generic `apply_filter()` fonksiyonu eklendi
- Tüm Frappe operatörleri destekleniyor
- Detaylı docstring ve örnekler

#### **Frontend (Client Script)**
- Debug mesajları kaldırıldı
- Professional JSDoc yorumlar
- Minimal ve temiz kod

#### **Dokümantasyon**
- ✅ `STOCK_ENTRY_FILTER_README.md` - Detaylı kullanım kılavuzu
- ✅ 4 farklı test senaryosu
- ✅ Tüm operatörlerin açıklaması
- ✅ Troubleshooting rehberi

### 📋 **Kullanım Örnekleri**

```
# Örnek 1: Ürün Grubu
Filtre: item_group = "Montaj ve İzolasyon"

# Örnek 2: Ürün Kodu (içerir)
Filtre: item_code like "102"

# Örnek 3: Miktar (büyüktür)
Filtre: qty > 100

# Örnek 4: Birden fazla filtre
Filtre 1: item_group = "Montaj ve İzolasyon"
Filtre 2: qty > 100
Filtre 3: warehouse = "ÜRETİM DEPO"
```

### 🔄 **v1.0.0'dan Değişiklikler**

| Özellik | v1.0.0 | v2.0.0 |
|---------|--------|--------|
| Desteklenen filtreler | Sadece `item_group` | **Tüm fieldlar** |
| Operatörler | Sadece `=` | **10 operatör** |
| Birden fazla filtre | ❌ | ✅ |
| Debug mesajları | ✅ (Console'da) | ❌ (Temiz kod) |
| Dokümantasyon | Minimal | **Kapsamlı** |

### ⚠️ **Breaking Changes**

Yok. Geriye dönük uyumlu!

### 📦 **Kurulum**

```bash
# Cache temizle (otomatik yüklenir)
bench clear-cache

# Tarayıcıda hard refresh
Ctrl + Shift + R
```

### 🧪 **Test Edildi**

- ✅ Tek filtre (item_group)
- ✅ İki filtre (item_group + qty)
- ✅ Like operatörü (item_code)
- ✅ Sayısal karşılaştırma (qty)

### 🎯 **Sonraki Sürümler için Fikirler**

- [ ] VEYA mantığı desteği (şu anda sadece VE)
- [ ] Regex desteği
- [ ] Custom field filtreleme
- [ ] Filtre preset'leri kaydetme

---

## v1.0.0 - İlk Versiyon (2025-10-30)

- ✅ `item_group` filtresi
- ✅ `=` operatörü
- ✅ ERPNext uyumlu
- ✅ Client Script + Backend entegrasyonu

