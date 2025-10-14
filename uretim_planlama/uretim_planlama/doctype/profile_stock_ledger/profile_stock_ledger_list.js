// Show Boy (m) with 1 decimal place in list view
frappe.listview_settings["Profile Stock Ledger"] = {
    formatters: {
        length(val) {
            if (!val) return "";
            const num = parseFloat(val);
            if (Number.isNaN(num)) return val;
            return num.toFixed(1);
        },
    },
};


