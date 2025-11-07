// Copyright (c) 2025, idris and contributors
// For license information, please see license.txt

frappe.ui.form.on("Accessory Delivery Package", {
	refresh(frm) {
		// Teslim edilmemiş Opti'leri filtrele
		frm.set_query("opti", () => ({
			filters: { delivered: 0 }
		}));

		// Opti'ye ait Sales Order'ları filtrele
		frm.set_query("sales_order", () => {
			if (!frm.doc.opti) return {};
			
			// Opti'ye ait sales order'ları backend'den al
			return {
				query: "uretim_planlama.uretim_planlama.doctype.accessory_delivery_package.accessory_delivery_package.get_sales_orders_for_opti",
				filters: { opti: frm.doc.opti }
			};
		});
	},

	opti(frm) {
		if (frm.doc.opti) {
			// Opti değiştiğinde Sales Order'ı temizle
			frm.set_value("sales_order", null);
			load_sales_orders_for_opti(frm);
		} else {
			clear_form_data(frm);
		}
	},

	sales_order(frm) {
		if (frm.doc.sales_order) {
			load_sales_order_details(frm);
		} else {
			clear_sales_order_data(frm);
		}
	}
});

// Opti için Sales Order listesini yükle
function load_sales_orders_for_opti(frm) {
	frappe.db.get_list("Opti SO Item", {
		filters: {
			parent: frm.doc.opti,
			delivered: 0
		},
		fields: ["sales_order"],
		pluck: "sales_order"
	}).then(orders => {
		frm.sales_orders_for_opti = orders || [];
		
		// Tek sipariş varsa otomatik seç
		if (orders && orders.length === 1) {
			frm.set_value("sales_order", orders[0]);
		}
	});
}

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

// Form verilerini temizle
function clear_form_data(frm) {
	frm.set_value("sales_order", null);
	clear_sales_order_data(frm);
	frm.sales_orders_for_opti = [];
}

// Sales Order verilerini temizle
function clear_sales_order_data(frm) {
	frm.set_value("dealer", null);
	frm.set_value("end_customer", null);
}
