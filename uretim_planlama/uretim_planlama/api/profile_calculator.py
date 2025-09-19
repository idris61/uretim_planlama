# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_boy_length(boy_name):
    """
    Boy DocType'ından length değerini getirir
    
    Args:
        boy_name (str): Boy kaydının name'i
        
    Returns:
        dict: {"length": float_value} veya {"error": "message"}
    """
    try:
        if not boy_name:
            return {"error": "Boy name boş olamaz"}
            
        # Boy kaydını bul
        boy_doc = frappe.get_doc("Boy", boy_name)
        if not boy_doc:
            return {"error": f"Boy kaydı bulunamadı: {boy_name}"}
            
        # Length değerini normalize et
        length_str = str(boy_doc.length).replace(',', '.')
        length_value = float(length_str)
        
        if length_value <= 0:
            return {"error": f"Geçersiz boy değeri: {length_value}"}
            
        return {"length": length_value}
        
    except frappe.DoesNotExistError:
        return {"error": f"Boy kaydı bulunamadı: {boy_name}"}
    except (ValueError, TypeError) as e:
        frappe.log_error(f"Boy length parse error: {str(e)}", "Profile Calculator Error")
        return {"error": f"Boy değeri parse edilemedi: {boy_name}"}
    except Exception as e:
        frappe.log_error(f"Boy length get error: {str(e)}", "Profile Calculator Error")
        return {"error": "Boy değeri alınırken hata oluştu"}


@frappe.whitelist()
def calculate_profile_quantity(boy_name, profile_qty, conversion_factor=1.0):
    """
    Profil miktar hesaplama
    
    Args:
        boy_name (str): Boy kaydının name'i
        profile_qty (int): Profil adedi
        conversion_factor (float): Çevrim faktörü
        
    Returns:
        dict: {"qty": float, "stock_qty": float} veya {"error": "message"}
    """
    try:
        # Boy length'ini al
        boy_result = get_boy_length(boy_name)
        if "error" in boy_result:
            return boy_result
            
        length = boy_result["length"]
        qty = int(profile_qty)
        cf = float(conversion_factor)
        
        if qty <= 0:
            return {"error": "Profil adedi 0'dan büyük olmalıdır"}
            
        if cf <= 0:
            return {"error": "Çevrim faktörü 0'dan büyük olmalıdır"}
            
        # Hesaplama
        calculated_qty = (length * qty) / cf
        stock_qty = calculated_qty * cf
        
        return {
            "qty": calculated_qty,
            "stock_qty": stock_qty,
            "length": length,
            "profile_qty": qty,
            "conversion_factor": cf,
            "calculation": f"{length}m × {qty} adet ÷ {cf} = {calculated_qty:.2f}"
        }
        
    except (ValueError, TypeError) as e:
        return {"error": f"Hesaplama hatası: {str(e)}"}
    except Exception as e:
        frappe.log_error(f"Profile calculation error: {str(e)}", "Profile Calculator Error")
        return {"error": "Hesaplama sırasında hata oluştu"}

