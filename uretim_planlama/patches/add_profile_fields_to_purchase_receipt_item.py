import frappe

def execute():
    custom_fields = {
        "Purchase Receipt Item": [
            {
                "fieldname": "is_profile",
                "label": "Is Profile",
                "fieldtype": "Check",
                "insert_after": "item_code",
                "description": "Profil ürünü mü?"
            },
            {
                "fieldname": "profile_length",
                "label": "Profile Length (m)",
                "fieldtype": "Select",
                "options": "5\n6\n6,5",
                "insert_after": "is_profile",
                "description": "Profil boyu",
                "depends_on": "eval:doc.is_profile"
            },
            {
                "fieldname": "profile_length_qty",
                "label": "Profile Length Qty",
                "fieldtype": "Int",
                "insert_after": "profile_length",
                "description": "Bu boydan kaç adet var?",
                "depends_on": "eval:doc.is_profile"
            }
        ]
    }
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(custom_fields) 