# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
import re
from frappe import _


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

def parse_length(length_str):
    """Boy string'ini float'a çevirir"""
    try:
        return float(str(length_str).replace(' m', '').replace(',', '.'))
    except ValueError:
        frappe.throw(_("Geçersiz boy formatı: {0}").format(length_str))


def get_allowed_profile_groups():
    """İzinli profil gruplarını döner"""
    return [
        'PVC', 'Camlar', 
        'Pvc Hat1 Ana Profiller', 'Pvc Hat2 Ana Profiller', 'Destek Sacı, Profiller',
        'Pvc Destek Sacları', 'Pvc Hat1 Destek Sacları', 'Pvc Hat1 Yardımcı Profiller',
        'Pvc Hat2 Yardımcı Profiller', 'Yardımcı Profiller'
    ]


def validate_profile_item(item_code, idx):
    """Profil ürün doğrulaması"""
    item_group = frappe.db.get_value("Item", item_code, "item_group")
    if item_group not in get_allowed_profile_groups():
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


def log_profile_operation(operation_type, item_code, length, quantity, action="in"):
    """Profil operasyon log kaydı"""
    action_text = "girişi" if action == "in" else "çıkışı"
    frappe.logger().info(f"Profile {operation_type}: {item_code} {length}m {quantity}adet stok {action_text} yapıldı")


def show_operation_result(success_count, error_count, total_length, total_qty, operation_type):
    """Operasyon sonuç mesajını göster"""
    if error_count == 0:
        frappe.msgprint(
            f"✅ Profil stokları başarıyla güncellendi!\n"
            f"📊 Toplam {success_count} satır işlendi\n"
            f"📏 Toplam uzunluk: {total_length:.3f} m\n"
            f"📦 Toplam adet: {total_qty}",
            title=_("Stok Güncelleme Başarılı"),
            indicator="green"
        )
    else:
        frappe.msgprint(
            f"⚠️ Profil stok güncellemesi kısmen başarısız!\n"
            f"✅ Başarılı: {success_count} satır\n"
            f"❌ Hatalı: {error_count} satır\n"
            f"📋 Hata detayları için logları kontrol edin",
            title=_("Stok Güncelleme Kısmen Başarısız"),
            indicator="orange"
        )


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
    """Belge kaydedilmeden önce profil miktarlarını doğrula"""
    validate_profile_quantities(doc, method)


def validate(doc, method):
    """Belge validasyon sırasında profil miktarlarını kontrol et"""
    validate_profile_quantities(doc, method)

