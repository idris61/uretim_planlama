# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LongTermReserveUsage(Document):
    def validate(self):
        # Item name'i otomatik doldur
        if self.item_code:
            self.item_name = frappe.db.get_value("Item", self.item_code, "item_name") or ""
        # Açıklama otomatik
        if self.sales_order and not self.description:
            self.description = f"Uzun vadeli rezervten {self.used_qty} adet kullanıldı."

# Yardımcı fonksiyonlar (örnek):
def get_last_usage(sales_order, item_code):
    return frappe.get_all(
        "LongTermReserveUsage",
        filters={"sales_order": sales_order, "item_code": item_code},
        fields=["used_qty"],
        order_by="modified desc",
        limit=1
    ) 