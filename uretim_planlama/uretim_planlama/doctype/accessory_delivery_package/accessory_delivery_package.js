// Copyright (c) 2025, idris and contributors
// For license information, please see license.txt

frappe.ui.form.on("Accessory Delivery Package", {
	refresh(frm) {
		// Sales Order filtreleme (isteğe göre eklenebilir)
	},

	sales_order(frm) {
		clear_tables(frm);
		
		if (frm.doc.sales_order) {
			load_sales_order_details(frm);
			// Otomatik malzeme yükle
			load_materials(frm);
		} else {
			clear_sales_order_data(frm);
		}
	},
	
	get_materials(frm) {
		// Get Materials butonu
		load_materials(frm);
	}
});

// Sales Order detaylarını yükle
function load_sales_order_details(frm) {
	frappe.db.get_value("Sales Order", frm.doc.sales_order, 
		["customer", "custom_end_customer"]
	).then(r => {
		if (r.message) {
			frm.set_value("dealer", r.message.customer);
			frm.set_value("end_customer", r.message.custom_end_customer);
		}
	});
}

// Malzeme listesini yükle
function load_materials(frm) {
	if (!frm.doc.sales_order) {
		frappe.msgprint(__("Lütfen Satış Siparişi seçiniz"));
		return;
	}
	
	frappe.call({
		method: "uretim_planlama.uretim_planlama.doctype.accessory_delivery_package.accessory_delivery_package.get_materials",
		args: {
			sales_order: frm.doc.sales_order
		},
		callback: (r) => {
			if (!r.message) return;
			
			const { materials, ppi_items } = r.message;
			
			// Production Plan Item'ları doldur
			if (ppi_items && ppi_items.length > 0) {
				frm.clear_table("assembly_items");
				ppi_items.forEach(row => {
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
						produced_qty: row.produced_qty
					});
				});
				frm.refresh_field("assembly_items");
			}
			
			// Aksesuar/İzolasyon malzemelerini doldur
			if (materials && materials.length > 0) {
				frm.clear_table("item_list");
				materials.forEach(row => {
					frm.add_child("item_list", {
						item_code: row.item_code,
						item_name: row.item_name,
						item_group: row.item_group,
						qty: row.qty,
						uom: row.uom
					});
				});
				frm.refresh_field("item_list");
			}
		}
	});
}

// Tabloları temizle
function clear_tables(frm) {
	frm.clear_table("item_list");
	frm.refresh_field("item_list");
	
	frm.clear_table("assembly_items");
	frm.refresh_field("assembly_items");
}

// Sales Order verilerini temizle
function clear_sales_order_data(frm) {
	frm.set_value("dealer", null);
	frm.set_value("end_customer", null);
}
