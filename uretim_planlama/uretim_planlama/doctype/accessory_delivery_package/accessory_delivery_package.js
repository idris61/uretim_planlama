// Copyright (c) 2025, idris and contributors
// For license information, please see license.txt

frappe.ui.form.on("Accessory Delivery Package", {
	onload: function (frm) {
		console.log("-- Loaded --");
	},
	refresh: function (frm) {
		// opti_no alanı için {label, value} kullanılabilir
		console.log("-- Refreshed --");

		if (
			frm.fields_dict.opti_no &&
			frm.fields_dict.opti_no.df.fieldtype === "Select"
		) {
			frm.set_df_property("opti_no", "options", []);
			frappe.call({
				method: "uretim_planlama.uretim_planlama.api.get_approved_opti_nos",
				callback: function (r) {
					let options = [{ label: "", value: "" }];
					(r.message || []).forEach(function (row) {
						if (row.custom_opti_no && row.name) {
							// options.push({ label: row.custom_opti_no, value: row.name });
							options.push({
								label: row.custom_opti_no,
								value: row.custom_opti_no,
							});
						}
					});
					frm.set_df_property("opti_no", "options", options);
					console.log("[DEBUG] opti_no options:", options);
				},
			});
		}

		// sales_order alanı için dinamik filtre (set_query)
		frm.set_query("sales_order", function () {
			if (frm.doc.opti_no) {
				return {
					filters: [["name", "in", frm.sales_orders_for_opti || []]],
				};
			}
		});
	},

	get_materials: function (frm) {
		if (!frm.doc.opti_no || !frm.doc.sales_order) {
			frappe.throw(__("Please select Opti No and Sales Order"));
		}

		frappe.call({
			method: "uretim_planlama.uretim_planlama.api.get_materials",
			args: {
				opti_no: frm.doc.opti_no,
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
	},

	opti_no: function (frm) {
		console.log("[DEBUG] opti_no seçildi, value:", frm.doc.opti_no);
		// opti_no değişince sales_order alanını temizle
		frm.set_value("sales_order", "");
		// opti_no'ya bağlı sales_order'ları çekip form objesine ata
		if (frm.doc.opti_no) {
			frappe.call({
				method: "uretim_planlama.uretim_planlama.api.get_sales_orders_by_opti",
				args: { opti_no: frm.doc.opti_no },
				callback: function (r) {
					frm.sales_orders_for_opti = r.message || [];
					console.log(
						"[DEBUG] sales_orders_for_opti:",
						frm.sales_orders_for_opti,
					);
				},
			});
		} else {
			frm.sales_orders_for_opti = [];
		}
	},
	sales_order: function (frm) {
		console.log("[DEBUG] sales_order seçildi, value:", frm.doc.sales_order);
	},
});
