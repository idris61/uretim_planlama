// Unified UOM filtering for multiple buying/selling forms using items child table
// Applies to: Purchase Order, Sales Order, Delivery Note, Purchase Receipt

(function () {
	function bind_uom_query(frm) {
		if (!frm || !frm.fields_dict || !frm.fields_dict.items) return;
		frm.fields_dict.items.grid.get_field("uom").get_query = function (doc, cdt, cdn) {
			const row = locals[cdt][cdn];
			const allowed = frm._item_uoms && row && row.item_code ? frm._item_uoms[row.item_code] || [] : [];
			if (!allowed.length) return { filters: [] };
			return { filters: [["UOM", "name", "in", allowed]] };
		};
	}

	async function populateItemUOMs(frm, row) {
		if (!row || !row.item_code) return;
		frm._item_uoms = frm._item_uoms || {};
		try {
			const item = await frappe.db.get_doc("Item", row.item_code);
			const uoms = [];
			(item.uoms || []).forEach((d) => {
				if (d.uom && !uoms.includes(d.uom)) uoms.push(d.uom);
			});
			if (item.stock_uom && !uoms.includes(item.stock_uom)) uoms.push(item.stock_uom);
			if (item.purchase_uom && !uoms.includes(item.purchase_uom)) uoms.push(item.purchase_uom);
			frm._item_uoms[row.item_code] = uoms;
			if (!row.uom) {
				row.uom = item.purchase_uom || item.stock_uom || row.uom;
			}
			bind_uom_query(frm);
			frm.refresh_field("items");
		} catch (e) {
			console.error("[UOM Filter] Item fetch error:", e);
		}
	}

	function addParentBindings(parentDoctype) {
		frappe.ui.form.on(parentDoctype, {
			setup(frm) {
				bind_uom_query(frm);
			},
			onload(frm) {
				bind_uom_query(frm);
			},
			refresh(frm) {
				bind_uom_query(frm);
			},
			items_on_form_rendered(frm) {
				bind_uom_query(frm);
			},
		});
	}

	function addChildBindings(childDoctype) {
		frappe.ui.form.on(childDoctype, {
			items_add(frm, cdt, cdn) {
				frm._item_uoms = frm._item_uoms || {};
				const row = locals[cdt][cdn];
				if (row.item_code && !frm._item_uoms[row.item_code]) frm._item_uoms[row.item_code] = [];
				bind_uom_query(frm);
			},
			async item_code(frm, cdt, cdn) {
				const row = locals[cdt][cdn];
				await populateItemUOMs(frm, row);
			},
		});
	}

	// Register for all relevant parents/children
	addParentBindings("Purchase Order");
	addChildBindings("Purchase Order Item");

	addParentBindings("Sales Order");
	addChildBindings("Sales Order Item");

	addParentBindings("Delivery Note");
	addChildBindings("Delivery Note Item");

	addParentBindings("Purchase Receipt");
	addChildBindings("Purchase Receipt Item");

	// Stock Entry
	addParentBindings("Stock Entry");
	addChildBindings("Stock Entry Detail");

	// Purchase Invoice
	addParentBindings("Purchase Invoice");
	addChildBindings("Purchase Invoice Item");

	// Sales Invoice
	addParentBindings("Sales Invoice");
	addChildBindings("Sales Invoice Item");

	// Material Request
	addParentBindings("Material Request");
	addChildBindings("Material Request Item");
})();


