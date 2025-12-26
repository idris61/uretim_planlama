import frappe
from frappe import _


def execute(filters=None):
    """
    Depo Bazında Stok Değeri raporu.

    Kaynak: Bin tablosu (ERPNext çekirdek stok)
    """
    filters = filters or {}

    item_code = filters.get("item_code")
    item_group = filters.get("item_group")
    warehouse = filters.get("warehouse")

    backend_result = frappe.call(
        "uretim_planlama.uretim_planlama.api.stock_value_report.get_warehouse_stock_value",
        item_code=item_code,
        item_group=item_group,
        warehouse=warehouse,
    )

    data = []
    for row in backend_result.get("items", []):
        data.append(
            {
                "warehouse": row.get("warehouse"),
                "item_code": row.get("item_code"),
                "item_name": row.get("item_name"),
                "item_group": row.get("item_group"),
                "qty": row.get("qty"),
                "valuation_rate": row.get("valuation_rate"),
                "stock_value": row.get("stock_value"),
            }
        )

    columns = [
        {
            "fieldname": "warehouse",
            "label": _("Depo"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 180,
        },
        {
            "fieldname": "item_code",
            "label": _("Ürün Kodu"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 160,
        },
        {
            "fieldname": "item_name",
            "label": _("Ürün Adı"),
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "fieldname": "item_group",
            "label": _("Ürün Grubu"),
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 160,
        },
        {
            "fieldname": "qty",
            "label": _("Miktar"),
            "fieldtype": "Float",
            "width": 110,
        },
        {
            "fieldname": "valuation_rate",
            "label": _("Maliyet"),
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "fieldname": "stock_value",
            "label": _("Stok Değeri"),
            "fieldtype": "Currency",
            "width": 140,
        },
    ]

    # Özet satırı için toplamlar
    total_qty = sum((row.get("qty") or 0) for row in data) if data else 0
    total_value = sum((row.get("stock_value") or 0) for row in data) if data else 0

    report_summary = [
        {
            "value": total_qty,
            "label": _("Toplam Miktar"),
            "indicator": "blue",
        },
        {
            "value": total_value,
            "label": _("Toplam Stok Değeri"),
            "indicator": "green",
        },
    ]

    return columns, data, None, None, report_summary, False











