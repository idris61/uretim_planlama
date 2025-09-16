import frappe
from uretim_planlama.uretim_planlama.utils import (
    normalize_profile_length,
    normalize_profile_quantity,
    parse_and_format_length,
    get_or_create_boy_record,
)


def _build_profile_exit_from_dn(doc):
    """Delivery Note içindeki profil satırlarından Profile Exit dokümanı oluşturur (kaydetmez)."""
    items = []
    for item in getattr(doc, "items", []) or []:
        if not getattr(item, "custom_is_profile", 0):
            continue

        # custom_profile_length_m Link field'ından Boy doctype'ındaki length değerini al
        length_link = getattr(item, "custom_profile_length_m", None)
        qty = getattr(item, "custom_profile_length_qty", None)

        if not length_link or not qty:
            continue

        try:
            # DN üzerindeki değer her durumda parse edilerek kullanılacak (tek kaynak gerçeklik)
            numeric, fixed = parse_and_format_length(length_link, decimals=1)
            length_float = numeric

            qty_int = int(float(normalize_profile_quantity(qty)))
        except Exception as e:
            frappe.log_error(f"Profile length/qty parse error: {e}", "DN Profile Parse Error")
            continue

        # Boy kaydını bul/oluştur ve Link olarak kullan
        boy_name = get_or_create_boy_record(fixed)
        if not boy_name:
            frappe.log_error(f"Boy not found/created for length {fixed}", "DN Profile Boy Error")
            continue

        items.append({
            "item_code": item.item_code,
            "length": boy_name,              # Link to Boy
            "output_quantity": qty_int,
            "total_length": length_float * qty_int,
        })

    if not items:
        return None

    pe = frappe.get_doc({
        "doctype": "Profile Exit",
        "date": doc.posting_date,
        "customer": getattr(doc, "customer", None),
        "warehouse": getattr(doc, "set_warehouse", None),
        "remarks": f"Delivery Note: {doc.name}",
        "items": items,
    })

    return pe


def on_submit(doc, method=None):
    """Delivery Note on_submit: profil satırları için otomatik Profile Exit oluştur ve submit et."""
    try:
        pe = _build_profile_exit_from_dn(doc)
        if not pe:
            return
        pe.insert()
        pe.submit()
    except Exception as e:
        frappe.log_error(f"Delivery Note -> Profile Exit on_submit error: {str(e)}", "DN Profile Exit Error")


def on_cancel(doc, method=None):
    """Delivery Note on_cancel: ilgili Profile Exit kaydını iptal et (varsa)."""
    try:
        # DN kaynaklı oluşturduklarımızı Remarks üzerinden bulalım
        exits = frappe.get_all(
            "Profile Exit",
            filters={"remarks": ["like", f"%Delivery Note: {doc.name}%"], "docstatus": 1},
            fields=["name"],
            limit=10,
        )
        for ex in exits:
            ex_doc = frappe.get_doc("Profile Exit", ex.name)
            ex_doc.cancel()
    except Exception as e:
        frappe.log_error(f"Delivery Note -> Profile Exit on_cancel error: {str(e)}", "DN Profile Exit Cancel Error")


