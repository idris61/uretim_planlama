# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


@frappe.whitelist()
def get_materials(sales_order):
    """
    Sales Order için aksesuar/izolasyon malzemelerini ve Production Plan Item'larını döndürür
    """
    if not sales_order:
        return {"ppi_items": [], "materials": []}
    
    # Production Plan Item'ları çek
    ppi_items = frappe.db.sql("""
        SELECT ppi.*
        FROM `tabProduction Plan Item` ppi
        WHERE ppi.sales_order = %(sales_order)s
    """, {"sales_order": sales_order}, as_dict=1)
    
    # Montaj ve İzolasyon, PVC Kolları, PVC Montaj Aksesuarları malzemelerini çek
    # Case-insensitive karşılaştırma ile tüm varyantları yakala
    materials = frappe.db.sql("""
        SELECT
            bi.item_code,
            bi.item_name,
            SUM((bi.qty / bom.quantity) * ppi.planned_qty) AS qty,
            i.item_group,
            ig.parent_item_group,
            i.stock_uom AS uom
        FROM `tabProduction Plan Item` ppi
        INNER JOIN `tabBOM` bom ON ppi.bom_no = bom.name
        INNER JOIN `tabBOM Item` bi ON bi.parent = bom.name
        INNER JOIN `tabItem` i ON i.item_code = bi.item_code
        INNER JOIN `tabItem Group` ig ON i.item_group = ig.name
        WHERE ppi.sales_order = %(sales_order)s
        AND (
            LOWER(i.item_group) IN ('montaj ve izolasyon', 'pvc kolları', 'pvc montaj aksesuarları')
            OR LOWER(ig.parent_item_group) IN ('montaj ve izolasyon', 'pvc kolları', 'pvc montaj aksesuarları')
        )
        GROUP BY bi.item_code, i.item_group, ig.parent_item_group, i.stock_uom
        ORDER BY i.item_group, bi.item_code
    """, {"sales_order": sales_order}, as_dict=1)
    
    return {"ppi_items": ppi_items, "materials": materials}


class AccessoryDeliveryPackage(Document):
    """Aksesuar Teslimat Paketi - Sales Order bazlı teslimat yönetimi"""
    
    def validate(self):
        """Doküman validasyonu - Sales Order kontrolü"""
        # Sales Order kontrolü
        if not self.sales_order:
            frappe.throw(frappe._("Satış Siparişi zorunludur"))
