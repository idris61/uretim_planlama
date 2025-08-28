import frappe

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

