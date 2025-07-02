import frappe

def execute():
    """Satış Siparişi formuna özel HTML alanı ekler (varsa tekrar eklemez)."""
    field_exists = frappe.db.exists(
        "Custom Field", {"dt": "Sales Order", "fieldname": "custom_raw_materials_html"}
    )
    if not field_exists:
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Sales Order",
            "fieldname": "custom_raw_materials_html",
            "label": "Gerekli Hammaddeler ve Stoklar",
            "fieldtype": "HTML",
            "insert_after": "items",
            "read_only": 1
        }).insert(ignore_permissions=True)
        frappe.db.commit() 