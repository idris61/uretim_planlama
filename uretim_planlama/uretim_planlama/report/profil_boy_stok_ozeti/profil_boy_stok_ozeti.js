frappe.query_reports["Profil Boy Stok Özeti"] = {
    filters: [
        {
            fieldname: "profile_type",
            label: __("Profile"),
            fieldtype: "Link",
            options: "Item",
            reqd: 0
        },
        {
            fieldname: "length",
            label: __("Length (m)"),
            fieldtype: "Link",
            options: "Boy"
        },
        {
            fieldname: "warehouse",
            label: __("Warehouse"),
            fieldtype: "Link",
            options: "Warehouse"
        },
        {
            fieldname: "is_scrap_piece",
            label: __("Only Scrap Pieces"),
            fieldtype: "Check",
            default: 0
        }
    ]
};


