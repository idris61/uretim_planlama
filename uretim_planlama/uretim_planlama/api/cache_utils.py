# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def clear_profile_groups_cache(doc=None, method=None):
    """Profil grupları cache'ini temizle"""
    try:
        cache_key = "allowed_profile_groups"
        frappe.cache().delete_value(cache_key)
        
        return {
            "success": True,
            "message": "Profile groups cache cleared successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Cache clear error: {str(e)}", "Profile Groups Cache Clear Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_cache_info():
    """Cache bilgilerini döner"""
    try:
        cache_key = "allowed_profile_groups"
        
        # Cache'de var mı kontrol et
        cached_data = frappe.cache().get_value(cache_key)
        
        return {
            "success": True,
            "cache_key": cache_key,
            "has_cached_data": cached_data is not None,
            "cached_groups_count": len(cached_data) if cached_data else 0,
            "cached_groups": cached_data if cached_data else []
        }
        
    except Exception as e:
        frappe.log_error(f"Cache info error: {str(e)}", "Profile Groups Cache Info Error")
        return {
            "success": False,
            "error": str(e)
        }
