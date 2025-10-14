// Copyright (c) 2025, idris and contributors
// For license information, please see license.txt

frappe.ui.form.on('Profile Exit Item', {
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Item',
					filters: { name: row.item_code },
					fieldname: ['item_name', 'item_group']
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value(cdt, cdn, 'item_name', r.message.item_name);
						frm.set_value(cdt, cdn, 'item_group', r.message.item_group);
					}
				}
			});
		}
	}
});


