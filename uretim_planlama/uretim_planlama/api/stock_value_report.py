import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_warehouse_stock_value(item_code: str | None = None,
                              item_group: str | None = None,
                              warehouse: str | None = None) -> dict:
    """
    Depo bazında stok değeri raporu.

    - Kaynak: `Bin` (ERPNext çekirdek stok tablosu)
    - Stok değeri = `Bin.stock_value` (varsa) aksi halde `actual_qty * valuation_rate`
    - Filtreler:
        * item_code  -> Ürün bazında
        * item_group -> Ürün grubu bazında
        * warehouse  -> Depo bazında
    """
    try:
        bin_filters: dict[str, object] = {}
        if item_code:
            bin_filters["item_code"] = item_code
        if warehouse:
            bin_filters["warehouse"] = warehouse

        bins = frappe.get_all(
            "Bin",
            filters=bin_filters,
            fields=[
                "item_code",
                "warehouse",
                "actual_qty",
                "valuation_rate",
                "stock_value",
            ],
            order_by="warehouse, item_code",
            limit=50000,
        )

        if not bins:
            return {"warehouse_summary": [], "items": []}

        # Item bilgilerini tek seferde çek
        item_codes = {row.item_code for row in bins}
        items = frappe.get_all(
            "Item",
            filters={"name": ["in", list(item_codes)]},
            fields=["name", "item_name", "item_group"],
        )
        item_map = {row.name: row for row in items}

        rows: list[dict] = []
        warehouse_totals: dict[str, dict] = {}

        for row in bins:
            item = item_map.get(row.item_code)
            if not item:
                continue

            # Ürün grubu filtresi
            if item_group and item.item_group != item_group:
                continue

            qty = flt(row.actual_qty)
            if not qty:
                continue

            valuation_rate = flt(row.valuation_rate)
            stock_value = flt(row.stock_value) if row.stock_value is not None else qty * valuation_rate

            rows.append(
                {
                    "warehouse": row.warehouse,
                    "item_code": row.item_code,
                    "item_name": item.item_name or row.item_code,
                    "item_group": item.item_group,
                    "qty": qty,
                    "valuation_rate": valuation_rate,
                    "stock_value": stock_value,
                }
            )

            wh = row.warehouse
            if wh not in warehouse_totals:
                warehouse_totals[wh] = {
                    "warehouse": wh,
                    "total_qty": 0.0,
                    "total_stock_value": 0.0,
                }

            warehouse_totals[wh]["total_qty"] += qty
            warehouse_totals[wh]["total_stock_value"] += stock_value

        # Ortalama maliyet
        warehouse_summary = []
        for wh, data in warehouse_totals.items():
            total_qty = data["total_qty"]
            total_value = data["total_stock_value"]
            avg_rate = total_value / total_qty if total_qty else 0
            data["avg_valuation_rate"] = flt(avg_rate)
            warehouse_summary.append(data)

        # Depo adına göre sırala
        warehouse_summary.sort(key=lambda x: x["warehouse"])

        return {
            "warehouse_summary": warehouse_summary,
            "items": rows,
        }

    except Exception as e:
        frappe.log_error(f"get_warehouse_stock_value error: {str(e)}", "Warehouse Stock Value Report")
        return {"error": str(e), "warehouse_summary": [], "items": []}











