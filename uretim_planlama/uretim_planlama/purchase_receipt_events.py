import frappe

def on_submit(doc, method=None):
    for item in doc.items:
        if getattr(item, "custom_is_profile", 0):
            length = getattr(item, "custom_profile_length_m", None)
            qty = getattr(item, "custom_profile_length_qty", None)
            if not length or not qty or float(qty) < 1:
                continue
            profile_entry = frappe.get_doc({
                "doctype": "Profile Entry",
                "date": doc.posting_date,
                "supplier": doc.supplier,
                "remarks": f"Purchase Receipt: {doc.name}",
                "items": [
                    {
                        "item_code": item.item_code,
                        "lenght": length,  # fieldname düzeltildi
                        "received_quantity": qty,
                        "total_length": float(length) * float(qty),
                        "purchase_receipt": doc.name
                    }
                ]
            })
            profile_entry.insert()
            profile_entry.submit() 