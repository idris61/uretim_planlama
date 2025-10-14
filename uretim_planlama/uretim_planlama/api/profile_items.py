# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_profile_items_filter(doctype, txt, searchfield, start, page_len, filters):
    """Dinamik profil ürün filtreleme API'si - Frappe get_query format"""
    try:
        # SQL query ile filtreleme - sadece profil ürünleri
        search_txt = f"%{txt}%" if txt else "%"
        
        query = """
            SELECT name, item_name, item_group
            FROM `tabItem`
            WHERE LOWER(item_group) LIKE %(profil_filter)s
            AND (name LIKE %(txt)s OR item_name LIKE %(txt)s)
            AND (disabled = 0 OR disabled IS NULL)
            ORDER BY name
            LIMIT %(start)s, %(page_len)s
        """
        
        results = frappe.db.sql(query, {
            'profil_filter': '%profil%',
            'txt': search_txt,
            'start': int(start),
            'page_len': int(page_len)
        }, as_list=True)
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Profile items filter error: {str(e)}", "Profile Items Filter Error")
        return []


@frappe.whitelist()
def get_profile_groups():
    """Dinamik profil gruplarını döner (debug/test için)"""
    try:
        from uretim_planlama.uretim_planlama.utils import get_allowed_profile_groups
        
        groups = get_allowed_profile_groups()
        
        return {
            "success": True,
            "groups": groups,
            "count": len(groups)
        }
        
    except Exception as e:
        frappe.log_error(f"Profile groups error: {str(e)}", "Profile Groups Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def refresh_profile_groups_cache():
    """Profil grupları cache'ini yenile - cache_utils'e yönlendirme"""
    from uretim_planlama.uretim_planlama.api.cache_utils import clear_profile_groups_cache
    from uretim_planlama.uretim_planlama.utils import get_allowed_profile_groups
    
    try:
        # Cache'i temizle
        clear_result = clear_profile_groups_cache()
        
        if clear_result.get("success"):
            # Yeni grupları al
            groups = get_allowed_profile_groups()
            return {
                "success": True,
                "message": f"Cache refreshed. Found {len(groups)} profile groups",
                "groups": groups
            }
        else:
            return clear_result
        
    except Exception as e:
        frappe.log_error(f"Cache refresh error: {str(e)}", "Profile Groups Cache Error")
        return {
            "success": False,
            "error": str(e)
        }