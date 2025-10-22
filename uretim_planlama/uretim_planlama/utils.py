# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
import re
from frappe import _


def parse_length(length_value):
    """
    Boy değerini parse eder (eski fonksiyon - geriye dönük uyumluluk için)
    """
    if length_value is None:
        return None
    normalized = str(length_value).replace(',', '.')
    try:
        float(normalized)
        return normalized
    except ValueError:
        return None

def normalize_length_to_string(length):
    """
    Length değerini string'e normalize eder
    """
    if length is None:
        return None
    if isinstance(length, (int, float)):
        return str(length)
    return str(length)

def normalize_profile_length(length_value):
    """
    Tüm profil boy alanlarında virgülü noktaya çevir
    Türkçe'de 5,2 -> 5.2 şeklinde kullanılan değerleri normalize eder
    
    Args:
        length_value: Boy değeri (string, float, int)
        
    Returns:
        str: Normalize edilmiş boy değeri
    """
    if length_value is None:
        return None
        
    # String'e çevir ve virgülü noktaya çevir
    normalized = str(length_value).replace(',', '.')
    
    # Sayısal değer kontrolü
    try:
        float(normalized)
        return normalized
    except ValueError:
        frappe.log_error(f"Geçersiz boy değeri: {length_value}", "Profile Length Normalize Error")
        return None

def log_profile_operation(operation_type, item_code, length, qty, direction):
    """
    Profil işlemlerini loglar
    """
    try:
        frappe.log_error(
            f"{operation_type}: {item_code} - {length}m x {qty} adet ({direction})",
            f"Profile {operation_type}"
        )
    except:
        pass

def show_operation_result(success_count, error_count, total_length, total_qty, operation):
    """
    İşlem sonucunu kullanıcıya gösterir
    """
    if error_count == 0:
        frappe.msgprint(
            f"✅ Profil {operation.lower()} başarıyla tamamlandı!\n"
            f"📊 Toplam {success_count} satır işlendi\n"
            f"📏 Toplam uzunluk: {total_length:.2f}m\n"
            f"📦 Toplam adet: {total_qty}",
            title=_(f"{operation} Başarılı"),
            indicator="green"
        )
    else:
        frappe.msgprint(
            f"⚠️ Profil {operation.lower()} kısmen başarısız!\n"
            f"✅ Başarılı: {success_count} satır\n"
            f"❌ Hatalı: {error_count} satır",
            title=_(f"{operation} Kısmen Başarısız"),
            indicator="orange"
        )


def parse_and_format_length(length_value, decimals=1):
    """
    Boy değerini yerel ayraçlardan arındırarak sayıya çevirir ve sabit ondalık
    basamakla stringe formatlar. Tüm giriş/çıkış akışlarında standart için kullanın.

    Args:
        length_value: Girdi değer ("6,1", "6.1", 6.1, "6.1 m" vb.)
        decimals (int): Ondalık basamak sayısı (varsayılan 1)

    Returns:
        tuple[float, str]: (numeric_length, formatted_string)
    """
    if length_value is None or str(length_value).strip() == "":
        frappe.throw(_("Boy değeri boş olamaz."))

    # Birim takısı gibi boşluk ve 'm' içeriğini temizle
    raw = str(length_value).replace(' m', '').strip()
    numeric = parse_locale_number(raw)

    if numeric <= 0:
        frappe.throw(_("Geçersiz boy değeri: {0}").format(length_value))

    fmt = f"{numeric:.{decimals}f}"
    return numeric, fmt


def get_or_create_boy_record(length_value):
    """
    Boy kaydını bul veya oluştur. Duplicate kayıtları önler.
    
    Args:
        length_value: Boy değeri (string, float, int)
        
    Returns:
        str: Boy kaydının name'i
    """
    if not length_value:
        return None
        
    # Parse ve format işlemi yap
    try:
        numeric_length, formatted_str = parse_and_format_length(length_value, decimals=1)
    except:
        return None
    
    # Sayısal değere eşit olan kayıtları ara
    existing = frappe.db.sql("""
        SELECT name, length 
        FROM `tabBoy` 
        WHERE CAST(REPLACE(REPLACE(length, ',', '.'), ' m', '') AS DECIMAL(10,2)) = %s
        LIMIT 1
    """, [numeric_length], as_dict=True)
    
    if existing:
        return existing[0].name
    
    # Bulunamadıysa yeni kayıt oluştur
    try:
        boy_doc = frappe.get_doc({
            "doctype": "Boy",
            "length": formatted_str
        })
        boy_doc.insert()
        return boy_doc.name
    except Exception as e:
        frappe.log_error(f"Boy kaydı oluşturulamadı: {str(e)}", "Boy Create Error")
        return None


def normalize_profile_quantity(qty_value):
    """
    Profil adet alanlarında virgülü noktaya çevir
    
    Args:
        qty_value: Adet değeri
        
    Returns:
        str: Normalize edilmiş adet değeri
    """
    if qty_value is None:
        return None
        
    normalized = str(qty_value).replace(',', '.')
    
    try:
        float(normalized)
        return normalized
    except ValueError:
        frappe.log_error(f"Geçersiz adet değeri: {qty_value}", "Profile Quantity Normalize Error")
        return None


# ============================================================================
# PROFİL UTILITY FONKSİYONLARI
# ============================================================================

# Duplicate fonksiyonlar kaldırıldı - yukarıdaki tanımlar kullanılıyor


def get_length_value_from_boy_doctype(length_name):
    """
    Boy DocType'ından length değerini alır ve validate eder.
    
    Args:
        length_name: Boy DocType'ının name'i (Link field değeri)
        
    Returns:
        float: Boy değeri (metre cinsinden)
        
    Raises:
        frappe.throw: Geçersiz boy değeri ise
    """
    if not length_name:
        frappe.throw(_("Boy değeri boş olamaz"))
    
    length_value = frappe.db.get_value("Boy", length_name, "length")
    
    if not length_value:
        frappe.throw(_("Geçersiz boy: {0}. Boy DocType'ında bu değer bulunamadı.").format(length_name))
    
    try:
        return float(length_value)
    except (ValueError, TypeError):
        frappe.throw(_("Geçersiz boy değeri: {0}").format(length_value))


def get_allowed_profile_groups():
    """İzinli profil gruplarını dinamik olarak döner (cache'li)"""
    # Cache kontrolü
    cache_key = "allowed_profile_groups"
    cached_groups = frappe.cache().get_value(cache_key)
    
    if cached_groups is not None:
        return cached_groups
    
    # Veritabanından dinamik olarak profil gruplarını al - SADECE "profil" içeren gruplar
    profile_groups = frappe.db.sql("""
        SELECT DISTINCT name 
        FROM `tabItem Group` 
        WHERE LOWER(name) LIKE '%profil%'
        ORDER BY name
    """, as_list=True)
    
    # List comprehension ile düz liste oluştur
    allowed_groups = [group[0] for group in profile_groups]
    
    # Cache'e kaydet (5 dakika)
    frappe.cache().set_value(cache_key, allowed_groups, expires_in_sec=300)
    
    return allowed_groups


def is_profile_item_group(item_group_name):
    """Bir ürün grubunun profil grubu olup olmadığını kontrol eder"""
    if not item_group_name:
        return False
    
    # Dinamik profil grup listesini al
    allowed_groups = get_allowed_profile_groups()
    
    # Direkt eşleşme kontrolü
    if item_group_name in allowed_groups:
        return True
    
    # Ek kontrol: "profil" kelimesi içeriyor mu?
    if "profil" in item_group_name.lower():
        return True
    
    return False


def validate_profile_item(item_code, idx):
    """Profil ürün doğrulaması (dinamik)"""
    item_group = frappe.db.get_value("Item", item_code, "item_group")
    if not is_profile_item_group(item_group):
        frappe.throw(_("Satır {0}: {1} ürünü profil değildir. Sadece profil gruplarındaki ürünler eklenebilir.").format(
            idx, item_code), title=_("Doğrulama Hatası"))


def calculate_total_length(length, quantity):
    """Toplam uzunluk hesaplar"""
    return round(float(length) * float(quantity), 3)


def validate_warehouse(warehouse=None):
    """Depo bilgisini doğrula ve varsayılan değer ata"""
    if not warehouse:
        default_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
        if default_warehouse:
            return default_warehouse
        else:
            frappe.throw(_("Depo bilgisi belirtilmelidir."), title=_("Doğrulama Hatası"))
    return warehouse


# ============================================================================
# PROFİL HOOK UTILITY FONKSİYONLARI
# ============================================================================

def parse_locale_number(raw_value):
    """Yerel ondalık/rakam ayraçlarını güvenli şekilde sayıya çevir"""
    if raw_value is None or raw_value == "":
        return 0.0
    
    s = str(raw_value).strip()
    if not s:
        return 0.0
    
    # Sadece rakam, nokta ve virgül bırak
    s = re.sub(r'[^0-9.,]', '', s)
    
    # Eğer hem nokta hem virgül varsa: nokta binlik, virgül ondalık varsayımı
    if s.count('.') > 0 and s.count(',') > 0:
        s = s.replace('.', '').replace(',', '.')
    elif s.count(',') > 0:
        # Sadece virgül varsa ondalık ayraç kabul et
        s = s.replace(',', '.')
    
    # Artık sadece ondalık için nokta kalmalı
    try:
        num = float(s)
        return num
    except (ValueError, TypeError):
        return 0.0


def validate_profile_quantities(doc, method):
    """Profil satırlarında miktar doğrulama ve otomatik hesaplama"""
    if not hasattr(doc, 'items') or not doc.items:
        return
    
    for item in doc.items:
        # Profil ürünü kontrolü
        if not getattr(item, "custom_is_profile", 0):
            continue
        
        # Profil boyu ve adet kontrolü
        length_raw = getattr(item, "custom_profile_length_m", None)
        count_raw = getattr(item, "custom_profile_length_qty", None)
        
        if not length_raw or not count_raw:
            continue
        
        # Değerleri parse et
        length = parse_locale_number(length_raw)
        count = int(count_raw) if count_raw else 0
        
        if length <= 0 or count <= 0:
            continue
        
        # Conversion factor
        cf = float(getattr(item, "conversion_factor", 1)) or 1
        
        # Beklenen miktar hesapla
        expected_qty = (length * count) / cf
        expected_stock_qty = expected_qty * cf
        
        # Mevcut değerlerle karşılaştır
        current_qty = float(getattr(item, "qty", 0)) or 0
        current_stock_qty = float(getattr(item, "stock_qty", 0)) or 0
        
        # Sapma varsa otomatik düzelt
        qty_diff = abs(current_qty - expected_qty)
        stock_qty_diff = abs(current_stock_qty - expected_stock_qty)
        
        if qty_diff > 0.001 or stock_qty_diff > 0.001:
            # Otomatik düzeltme
            item.qty = expected_qty
            item.stock_qty = expected_stock_qty
            
            # Kullanıcıya bilgi ver
            frappe.msgprint(
                f"📊 Satır {item.idx}: Profil miktarı otomatik düzeltildi<br>"
                f"Boy: {length} × Adet: {count} = {expected_qty} {item.uom}<br>"
                f"Stok: {expected_stock_qty} {item.stock_uom}",
                title="Profil Miktar Düzeltildi",
                indicator="green"
            )


def before_save(doc, method):
    """
    Belge kaydedilmeden önce:
    1. Profil miktarlarını doğrula
    2. Print format için description'ları güncelle
    """
    validate_profile_quantities(doc, method)
    
    # Print format için description güncelle
    from .print_format_manager import PrintFormatManager
    PrintFormatManager.update_item_descriptions_for_print(doc)


def validate(doc, method):
    """Belge validasyon sırasında profil miktarlarını kontrol et"""
    validate_profile_quantities(doc, method)


# ============================================================================
# PROFİL STOK QUERY FONKSİYONLARI
# ============================================================================

def get_profile_stock(item_code, length, is_scrap_piece=0):
    """
    Belirli profil boyunda mevcut stok miktarını döner.
    
    Args:
        item_code (str): Ürün kodu
        length (str/float): Boy değeri
        is_scrap_piece (int): Hurda parça mı? (0 veya 1)
        
    Returns:
        float: Stok miktarı
    """
    from frappe.utils import flt
    
    existing = frappe.get_all(
        "Profile Stock Ledger",
        filters={
            "item_code": item_code,
            "length": length,
            "is_scrap_piece": is_scrap_piece
        },
        fields=["qty"],
        limit=1
    )
    
    return flt(existing[0].qty) if existing else 0

