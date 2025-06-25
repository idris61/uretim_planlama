# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProfileStockLedger(Document):
	pass

def update_profile_stock(profile_type, length, qty, action, is_scrap_piece=0):
    """
    Profil stoklarını günceller. action: 'in' (giriş) veya 'out' (çıkış)
    """
    filters = {"profile_type": profile_type, "length": length, "is_scrap_piece": is_scrap_piece}
    stock = frappe.get_all("Profile Stock Ledger", filters=filters, fields=["name", "qty", "total_length"])
    if stock:
        doc = frappe.get_doc("Profile Stock Ledger", stock[0].name)
        if action == "in":
            doc.qty += qty
        elif action == "out":
            doc.qty -= qty
            if doc.qty < 0:
                frappe.throw(f"Yetersiz stok: {profile_type} {length}m profilden çıkış yapılamaz.")
        doc.total_length = doc.qty * doc.length
        if doc.qty == 0:
            doc.delete()
        else:
            doc.save()
    else:
        if action == "in":
            doc = frappe.new_doc("Profile Stock Ledger")
            doc.profile_type = profile_type
            doc.length = length
            doc.qty = qty
            doc.is_scrap_piece = is_scrap_piece
            doc.total_length = qty * length
            doc.insert()
        else:
            frappe.throw(f"Stokta olmayan profilden çıkış yapılamaz: {profile_type} {length}m")

def get_profile_stock(profile_type=None):
    """
    Profil stoklarını (boy ve adet bazında) listeler.
    """
    filters = {}
    if profile_type:
        filters["profile_type"] = profile_type
    return frappe.get_all(
        "Profile Stock Ledger",
        filters=filters,
        fields=["profile_type", "length", "qty", "total_length"],
        order_by="profile_type, length"
    )
