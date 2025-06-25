import frappe

def execute():
    # Alan zaten varsa tekrar ekleme
    if not frappe.db.exists("Custom Field", {"dt": "Sales Order", "fieldname": "custom_raw_materials_html"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Sales Order",
            "fieldname": "custom_raw_materials_html",
            "label": "Gerekli Hammaddeler ve Stoklar",
            "fieldtype": "HTML",
            "insert_after": "items",  # veya istediğin başka bir alan
            "read_only": 1
        }).insert(ignore_permissions=True)
        frappe.db.commit() 