import frappe
from frappe import _


def execute(filters=None):
    """
    Profil Boy Stok Özeti raporu.
    Profile Stock Ledger + Profile Entry/Exit + Profile Reorder Rule verilerini
    boy (length) ve profil bazında özetler. ERPNext Stok Özeti benzeri kolonlar üretir.
    """
    filters = filters or {}

    columns = get_columns()
    data, message = get_data(filters)

    return columns, data, None, message


def get_columns():
    return [
        {"label": _("Profile"), "fieldname": "profile_type", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": _("Profile Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Length (m)"), "fieldname": "length", "fieldtype": "Float", "width": 110},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "precision": 3, "width": 90},
        {"label": _("Total (mtül)"), "fieldname": "total_length", "fieldtype": "Float", "precision": 3, "width": 110},
        {"label": _("Is Scrap"), "fieldname": "is_scrap_piece", "fieldtype": "Check", "width": 90},
        {"label": _("Min Qty"), "fieldname": "min_qty", "fieldtype": "Float", "width": 90},
        {"label": _("Reorder Qty"), "fieldname": "reorder_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Shortage"), "fieldname": "shortage", "fieldtype": "Float", "width": 100},
        {"label": _("To Order"), "fieldname": "to_order", "fieldtype": "Float", "width": 100},
        {"label": _("Last Updated"), "fieldname": "modified", "fieldtype": "Datetime", "width": 150},
    ]


def get_data(filters):
    where = {}
    if filters.get("profile_type"):
        where["profile_type"] = filters.get("profile_type")
    if filters.get("length"):
        where["length"] = filters.get("length")
    if filters.get("is_scrap_piece") is not None:
        where["is_scrap_piece"] = int(filters.get("is_scrap_piece"))

    stocks = frappe.get_all(
        "Profile Stock Ledger",
        filters=where,
        fields=[
            "profile_type", "length", "qty", "total_length", "is_scrap_piece", "modified"
        ],
        order_by="profile_type, length"
    )

    # Item adları
    item_names = {}
    result = []

    # Reorder kurallarını indeksle: (profile_type, length, warehouse) -> rule
    rules = get_reorder_rules(index=True)

    # Boy eşlemesi: Boy.name -> numeric length, hızlı lookup
    boy_map = get_boy_length_map()

    for row in stocks:
        if row.profile_type not in item_names:
            item_names[row.profile_type] = frappe.db.get_value("Item", row.profile_type, "item_name") or row.profile_type

        # Rule key'i boy uzunluğuna göre eşle
        rule = rules.get((row.profile_type, float(row.length)))

        min_qty = (rule or {}).get("min_qty") or 0
        reorder_qty = (rule or {}).get("reorder_qty") or 0

        shortage = 0
        to_order = 0
        if min_qty and row.qty is not None:
            shortage = float(min_qty) - float(row.qty)
            shortage = shortage if shortage > 0 else 0
            if shortage and reorder_qty:
                to_order = max(reorder_qty, shortage)
            elif shortage:
                to_order = shortage

        result.append({
            "profile_type": row.profile_type,
            "item_name": item_names[row.profile_type],
            "length": row.length,
            "qty": row.qty,
            "total_length": row.total_length,
            "is_scrap_piece": row.is_scrap_piece,
            "min_qty": min_qty,
            "reorder_qty": reorder_qty,
            "shortage": shortage,
            "to_order": to_order,
            "modified": row.modified,
        })

    message = None
    if not result:
        message = _("Kayıt bulunamadı.")

    return result, message


def get_reorder_rules(index=False):
    rules = frappe.get_all(
        "Profile Reorder Rule",
        filters={"active": 1},
        fields=[
            "profile_type", "length", "min_qty", "reorder_qty"
        ]
    )
    if not index:
        return rules
    # Boy name -> numeric length map
    boy_map = get_boy_length_map()
    indexed = {}
    for r in rules:
        boy_len_str = boy_map.get(r.length)
        try:
            boy_len = float(boy_len_str) if boy_len_str is not None else None
        except Exception:
            boy_len = None
        if boy_len is None:
            # Boy bulunamazsa bu kuralı atla
            continue
        key = (r.profile_type, boy_len)
        indexed[key] = r
    return indexed


def get_boy_length_map():
    """Boy.name -> Boy.length (string) haritası"""
    boys = frappe.get_all("Boy", fields=["name", "length"], limit_page_length=10000)
    return {b.name: b.length for b in boys}


