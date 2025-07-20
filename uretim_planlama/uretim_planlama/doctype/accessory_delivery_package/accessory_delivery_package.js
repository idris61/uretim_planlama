// Copyright (c) 2025, idris and contributors
// For license information, please see license.txt

frappe.ui.form.on("Accessory Delivery Package", {
	refresh: function (frm) {
		frm.set_query("opti", function () {
			return {
				filters: {
					delivered: false,
				},
			};
		});

		frm.set_query("sales_order", function () {
			if (frm.doc.opti) {
				return {
					filters: [["name", "in", frm.sales_orders_for_opti || []]],
				};
			}
		});
	},

	opti: function (frm) {
		handle_opti_no_change(frm);
		clear_tables(frm);
	},

	sales_order: function (frm) {
		clear_tables(frm);
		handle_sales_order_change(frm);
		if (frm.doc.sales_order) {
			handle_get_materials_button_click(frm);
		}
	},

	get_materials: function (frm) {
		handle_get_materials_button_click(frm);
	},
});

// |||||||||| HANDLERS ||||||||||

function handle_opti_no_change(frm) {
	if (frm.doc.sales_order) {
		frm.set_value("sales_order", "");
	}
	if (frm.doc.opti) {
		frappe.call({
			method: "uretim_planlama.uretim_planlama.api.get_sales_orders_by_opti",
			args: { opti: frm.doc.opti },
			callback: function (r) {
				if (!r.message) return;
				frm.sales_orders_for_opti = r.message || [];
				if (frm.sales_orders_for_opti.length == 1) {
					frm.set_value("sales_order", frm.sales_orders_for_opti[0]);
				}
			},
		});
	} else {
		frm.sales_orders_for_opti = [];
	}
}

function handle_sales_order_change(frm) {
	if (!frm.doc.sales_order) {
		frm.set_value("dealer", "");
		frm.set_value("end_customer", "");
		return;
	}

	frappe.call({
		method: "uretim_planlama.uretim_planlama.api.get_sales_order_details",
		args: { order_no: frm.doc.sales_order },
		callback: function (r) {
			if (!r.message) return;
			const sales_order = r.message;
			frm.set_value("dealer", sales_order.customer);
			frm.set_value("end_customer", sales_order.custom_end_customer);
		},
	});
}

function handle_get_materials_button_click(frm) {
	if (!frm.doc.opti || !frm.doc.sales_order) {
		frappe.throw(__("Please select Opti No and Sales Order"));
	}

	frappe.call({
		method: "uretim_planlama.uretim_planlama.api.get_materials",
		args: {
			opti_no: frm.doc.opti,
			sales_order: frm.doc.sales_order,
		},
		callback: function (r) {
			if (!r.message) return;

			const { materials, ppi_items } = r.message;

			if (ppi_items) {
				frm.clear_table("assembly_items");
				ppi_items.forEach((row) => {
					frm.add_child("assembly_items", {
						item_code: row.item_code,
						bom_no: row.bom_no,
						custom_mtul_per_piece: row.custom_mtul_per_piece,
						custom_serial: row.custom_serial,
						custom_color: row.custom_color,
						custom_workstation: row.custom_workstation,
						planned_qty: row.planned_qty,
						stock_uom: row.stock_uom,
						warehouse: row.warehouse,
						planned_start_date: row.planned_start_date,
						pending_qty: row.pending_qty,
						ordered_qty: row.ordered_qty,
						produced_qty: row.produced_qty,
					});
				});
				frm.refresh_field("assembly_items");
			}

			if (materials) {
				frm.clear_table("item_list");
				materials.forEach((row) => {
					frm.add_child("item_list", {
						item_code: row.item_code,
						item_name: row.item_name,
						qty: row.qty,
						uom: row.uom,
					});
				});
				frm.refresh_field("item_list");
			}
		},
	});
}

function clear_tables(frm) {
	frm.clear_table("item_list");
	frm.refresh_field("item_list");

	frm.clear_table("assembly_items");
	frm.refresh_field("assembly_items");
}
