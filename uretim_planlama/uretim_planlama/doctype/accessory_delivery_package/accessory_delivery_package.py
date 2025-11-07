# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_sales_orders_for_opti(doctype, txt, searchfield, start, page_len, filters):
    """
    Opti için teslim edilmemiş Sales Order'ları döndür
    Frappe query fonksiyonu için standart signature
    """
    # filters dict'inden opti bilgisini al
    opti = filters.get("opti") if isinstance(filters, dict) else None
    
    if not opti:
        return []
    
    # Opti SO Item child table'dan sales_order'ları çek
    return frappe.db.sql("""
        SELECT DISTINCT sales_order
        FROM `tabOpti SO Item`
        WHERE parent = %(opti)s
        AND delivered = 0
        AND sales_order LIKE %(txt)s
        ORDER BY sales_order
        LIMIT %(start)s, %(page_len)s
    """, {
        "opti": opti,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })


@frappe.whitelist()
def get_materials(opti_no, sales_order):
    """
    Opti ve Sales Order için aksesuar/izolasyon malzemelerini ve Production Plan Item'larını döndürür
    """
    if not opti_no or not sales_order:
        return {"ppi_items": [], "materials": []}
    
    # Production Plan Item'ları çek
    ppi_items = frappe.db.sql("""
        SELECT ppi.*
        FROM `tabProduction Plan Item` ppi
        INNER JOIN `tabProduction Plan` pp ON ppi.parent = pp.name
        WHERE pp.custom_opti_no = %(opti_no)s
        AND ppi.sales_order = %(sales_order)s
    """, {"opti_no": opti_no, "sales_order": sales_order}, as_dict=1)
    
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
        INNER JOIN `tabProduction Plan` pp ON ppi.parent = pp.name
        INNER JOIN `tabBOM` bom ON ppi.bom_no = bom.name
        INNER JOIN `tabBOM Item` bi ON bi.parent = bom.name
        INNER JOIN `tabItem` i ON i.item_code = bi.item_code
        INNER JOIN `tabItem Group` ig ON i.item_group = ig.name
        WHERE pp.custom_opti_no = %(opti_no)s
        AND ppi.sales_order = %(sales_order)s
        AND (
            LOWER(i.item_group) IN ('montaj ve i̇zolasyon', 'pvc kollar', 'pvc kolları', 'pvc montaj aksesuarları')
            OR LOWER(ig.parent_item_group) IN ('montaj ve i̇zolasyon', 'pvc kollar', 'pvc kolları', 'pvc montaj aksesuarları')
        )
        GROUP BY bi.item_code, i.item_group, ig.parent_item_group, i.stock_uom
        ORDER BY i.item_group, bi.item_code
    """, {"opti_no": opti_no, "sales_order": sales_order}, as_dict=1)
    
    return {"ppi_items": ppi_items, "materials": materials}


class AccessoryDeliveryPackage(Document):
    """Aksesuar Teslimat Paketi - Opti bazlı teslimat yönetimi"""
    
    def validate(self):
        """Doküman validasyonu - Opti ve Sales Order kontrolü"""
        # Opti kontrolü
        if not self.opti:
            frappe.throw(frappe._("Opti numarası zorunludur"))
        
        # Sales Order kontrolü
        if not self.sales_order:
            frappe.throw(frappe._("Satış Siparişi zorunludur"))
        
        # Opti ve SO kombinasyonu geçerli mi?
        if not self._validate_opti_sales_order():
            frappe.throw(
                frappe._("Satış Siparişi [{0}], Opti [{1}] içinde bulunamadı").format(
                    self.sales_order, self.opti
                )
            )

    def on_submit(self):
        """Submit - Teslimat durumunu güncelle"""
        # SO Item teslimat durumu kontrol ve güncelleme
        if self._is_already_delivered():
            frappe.throw(
                frappe._("Bu ürünler zaten teslim edilmiş. Lütfen Opti veya Sipariş değiştirin")
            )
        
        self._mark_so_item_delivered()
        self._update_opti_delivery_status()

    def on_cancel(self):
        """Cancel - Teslimat durumunu geri al"""
        self._mark_so_item_undelivered()
        self._update_opti_delivery_status_on_cancel()

    def _validate_opti_sales_order(self):
        """Opti ve Sales Order kombinasyonunu kontrol et"""
        return frappe.db.exists(
            "Opti SO Item",
            {"parent": self.opti, "sales_order": self.sales_order}
        )

    def _is_already_delivered(self):
        """SO Item zaten teslim edilmiş mi?"""
        delivered = frappe.db.get_value(
            "Opti SO Item",
            {"parent": self.opti, "sales_order": self.sales_order},
            "delivered"
        )
        return delivered == 1

    def _mark_so_item_delivered(self):
        """SO Item'ı teslim edildi olarak işaretle"""
        frappe.db.set_value(
            "Opti SO Item",
            {"parent": self.opti, "sales_order": self.sales_order},
            "delivered",
            1
        )

    def _mark_so_item_undelivered(self):
        """SO Item'ın teslimat durumunu geri al"""
        frappe.db.set_value(
            "Opti SO Item",
            {"parent": self.opti, "sales_order": self.sales_order},
            "delivered",
            0
        )

    def _update_opti_delivery_status(self):
        """Opti teslimat durumunu güncelle - Tüm SO'lar teslim edildiyse Opti'yi işaretle"""
        # Opti'deki tüm SO itemları teslim edildi mi?
        undelivered_count = frappe.db.count(
            "Opti SO Item",
            {"parent": self.opti, "delivered": 0}
        )
        
        # Tümü teslim edildiyse Opti'yi işaretle
        if undelivered_count == 0:
            frappe.db.set_value("Opti", self.opti, "delivered", 1)

    def _update_opti_delivery_status_on_cancel(self):
        """İptal durumunda Opti teslimat durumunu güncelle"""
        # Opti delivered ise sıfırla (bir SO iptal edildi)
        opti_delivered = frappe.db.get_value("Opti", self.opti, "delivered")
        if opti_delivered == 1:
            frappe.db.set_value("Opti", self.opti, "delivered", 0)
