/**
 * Material Request Item - Otomatik Supplier Eşleme
 * Item seçildiğinde supplier_items child table'ından supplier bilgisini çeker
 */

frappe.ui.form.on('Material Request Item', {
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		
		if (row.item_code) {
			// Item'ın supplier_items child table'ından ilk supplier'ı çek
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Item',
					name: row.item_code,
					filters: {
						name: row.item_code
					}
				},
				callback: function(r) {
					if (r.message && r.message.supplier_items && r.message.supplier_items.length > 0) {
						// İlk supplier'ı al
						let first_supplier = r.message.supplier_items[0].supplier;
						frappe.model.set_value(cdt, cdn, 'supplier', first_supplier);
					}
				}
			});
		}
	}
});

