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
    warehouse_totals = {}
    for row in backend_result.get("items", []):
        warehouse = row.get("warehouse")
        item_group = row.get("item_group")
        stock_value = row.get("stock_value") or 0

        # PVC ve Camlar ürün gruplarını tamamen hariç tut (liste, grafik ve toplamlar)
        if item_group in ("PVC", "Camlar"):
            continue

        data.append(
            {
                "warehouse": warehouse,
                "item_code": row.get("item_code"),
                "item_name": row.get("item_name"),
                "item_group": item_group,
                "qty": row.get("qty"),
                "valuation_rate": row.get("valuation_rate"),
                "stock_value": stock_value,
            }
        )

        # Depo bazında toplam stok değeri (grafik için)
        if warehouse:
            warehouse_totals.setdefault(warehouse, 0)
            warehouse_totals[warehouse] += stock_value

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

    total_qty = sum((row.get("qty") or 0) for row in data) if data else 0
    total_value = sum((row.get("stock_value") or 0) for row in data) if data else 0

    # Sistem varsayılan para birimi (ör. TRY)
    default_currency = frappe.defaults.get_global_default("currency")

    report_summary = [
        {
            "value": total_value,
            "label": _("Toplam Stok Değeri"),
            "indicator": "green",
            "datatype": "Currency",
            "currency": default_currency,
        }
    ]

    # Grafik: Depo bazında toplam stok değeri
    chart = None
    if warehouse_totals:
        labels = list(warehouse_totals.keys())
        values = [warehouse_totals[w] for w in labels]

        chart = {
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "name": _("Stok Değeri"),
                        "values": values,
                    }
                ],
            },
            "type": "bar",
        }

    return columns, data, None, chart, report_summary, False


