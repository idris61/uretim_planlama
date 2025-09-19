frappe.query_reports["Profil Boy Stok Ozeti"] = {
    filters: [
        {
            fieldname: "profile_type",
            label: __("Profil"),
            fieldtype: "Link",
            options: "Item",
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
        },
        {
            fieldname: "is_scrap_piece",
            label: __("Sadece Hurda Parçalar"),
            fieldtype: "Check",
            default: 0
        }
    ]
};



