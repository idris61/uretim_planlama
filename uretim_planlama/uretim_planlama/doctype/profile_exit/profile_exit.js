// Copyright (c) 2025, idris and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Profile Exit", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Profile Exit Item', {
    output_quantity: function(frm, cdt, cdn) {
        calculate_total_length_exit(frm, cdt, cdn);
    },
    length: function(frm, cdt, cdn) {
        calculate_total_length_exit(frm, cdt, cdn);
    }
});

function calculate_total_length_exit(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    var length = parseFloat((row.length + '').replace(' m', '').replace(',', '.')) || 0;
    var qty = row.output_quantity || 0;
    row.total_length = Math.round(length * qty * 1000) / 1000;
    frm.fields_dict.items.grid.refresh();
}
