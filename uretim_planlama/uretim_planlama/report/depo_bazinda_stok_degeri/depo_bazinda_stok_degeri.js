frappe.query_reports["Depo Bazında Stok Değeri"] = {
    filters: [
        {
            fieldname: "item_code",
            label: __("Ürün Kodu"),
            fieldtype: "Link",
            options: "Item",
        },
        {
            fieldname: "item_group",
            label: __("Ürün Grubu"),
            fieldtype: "Link",
            options: "Item Group",
        },
        {
            fieldname: "warehouse",
            label: __("Depo"),
            fieldtype: "Link",
            options: "Warehouse",
        },
    ],
};




