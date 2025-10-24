frappe.query_reports["Profil Boy Stok Ozeti"] = {
    filters: [
        {
            fieldname: "item_code",
            label: __("Ürün Kodu"),
            fieldtype: "Link",
            options: "Item",
            reqd: 0,
            default: "",
            get_query: function() {
                return {
                    filters: {
                        "item_group": ["like", "%profil%"]
                    }
                };
            }
        },
        {
            fieldname: "item_group",
            label: __("Ürün Grubu"),
            fieldtype: "Link",
            options: "Item Group",
            reqd: 0,
            default: ""
        },
        {
            fieldname: "length",
            label: __("Boy (m)"),
            fieldtype: "Link",
            options: "Boy",
            reqd: 0,
            default: ""
        }
    ]
};



