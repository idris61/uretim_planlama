import frappe
from frappe import _


def check_profile_reorder_on_sales_order(doc, method):
    """Sales Order submit edildiğinde profile reorder kontrolü yap"""
    # Manuel test: 10220 profil tipi, 5.0 boy için reorder kontrolü
    from uretim_planlama.uretim_planlama.api.reorder import ensure_reorder_for_profile
    result = ensure_reorder_for_profile('10220', 5.0, 5)
    frappe.msgprint(f"Profile reorder test sonucu: {result}")


def get_current_profile_stock(profile_type, length):
    """Profil tipine ve boyuna göre mevcut stok miktarını al"""
    try:
        stock_records = frappe.get_all(
            "Profile Stock Ledger",
            filters={
                "profile_type": profile_type,
                "length": length,
                "is_scrap_piece": 0
            },
            fields=["qty"]
        )
        
        total_stock = sum(float(record.qty or 0) for record in stock_records)
        return total_stock
        
    except Exception as e:
        frappe.log_error(f"Get profile stock error: {str(e)}", "Profile Stock Error")
        return 0
