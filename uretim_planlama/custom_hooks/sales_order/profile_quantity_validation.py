# -*- coding: utf-8 -*-
"""
Sales Order profil miktar doğrulama ve otomatik hesaplama
"""

import frappe
import re


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
    if not doc.items:
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
    """Sales Order kaydedilmeden önce profil miktarlarını doğrula"""
    validate_profile_quantities(doc, method)


def validate(doc, method):
    """Sales Order validasyon sırasında profil miktarlarını kontrol et"""
    validate_profile_quantities(doc, method)
