import frappe

def execute():
    # 1. Check field: is_long_term_child
    if not frappe.db.exists("Custom Field", {"dt": "Sales Order", "fieldname": "is_long_term_child"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Sales Order",
            "fieldname": "is_long_term_child",
            "label": "Uzun vadeli ana siparişin parçası mı?",
            "fieldtype": "Check",
            "insert_after": "order_type",
            "description": "Bu satış siparişi, uzun vadeli bir ana siparişin parçası mı?"
        }).insert()
    # 2. Link field: parent_sales_order
    if not frappe.db.exists("Custom Field", {"dt": "Sales Order", "fieldname": "parent_sales_order"}):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Sales Order",
            "fieldname": "parent_sales_order",
            "label": "Ana Satış Siparişi",
            "fieldtype": "Link",
            "options": "Sales Order",
            "insert_after": "is_long_term_child",
            "depends_on": "eval:doc.is_long_term_child==1",
            "description": "Bu satış siparişi hangi ana satış siparişine bağlı?"
        }).insert() 