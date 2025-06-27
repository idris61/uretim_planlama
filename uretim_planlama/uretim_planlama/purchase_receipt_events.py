import frappe

def on_submit(doc, method=None):
    # Her bir satırı kontrol et
    for item in doc.items:
        # Sadece profil ürünleri için (is_profile işaretli ise)
        if getattr(item, "is_profile", 0):
            length = str(getattr(item, "profile_length", "")).replace(",", ".")
            qty = int(getattr(item, "profile_length_qty", 0))
            if not length or qty < 1:
                continue
            # Profile Entry oluştur
            profile_entry = frappe.get_doc({
                "doctype": "Profile Entry",
                "date": doc.posting_date,
                "supplier": doc.supplier,
                "remarks": f"Purchase Receipt: {doc.name}",
                "items": [
                    {
                        "item_code": item.item_code,
                        "length": length,
                        "received_quantity": qty,
                        "total_length": float(length.replace(",", ".")) * qty,
                        "purchase_receipt": doc.name
                    }
                ]
            })
            profile_entry.insert()
            profile_entry.submit() 