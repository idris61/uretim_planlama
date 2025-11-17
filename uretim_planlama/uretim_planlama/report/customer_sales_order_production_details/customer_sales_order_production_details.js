/* Kod Yorumları: Türkçe */

frappe.query_reports["Customer Sales Order Production Details"] = {
	filters: [
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
			reqd: 1,
			on_change: function () {
				// Müşteri değiştiğinde Sales Order filtresini temizle ve sorgusunu müşteri ile kısıtla
				const customer = frappe.query_report.get_filter_value("customer");
				frappe.query_report.set_filter_value("sales_order", "");

				// Sales Order query'sini müşteri bazlı yap
				const so_filter = frappe.query_report.get_filter("sales_order");
				if (so_filter) {
					so_filter.get_query = () => {
						return {
							filters: {
								customer: customer,
								docstatus: 1,
								status: ["!=", "Closed"],
							},
						};
					};
				}
			},
		},
		{
			fieldname: "sales_order",
			label: __("Sales Order"),
			fieldtype: "Link",
			options: "Sales Order",
			depends_on: "eval:doc.customer",
			reqd: 1,
			get_query: function () {
				// İlk yüklemede de müşteri bazlı kısıt olsun
				const customer = frappe.query_report.get_filter_value("customer");
				return {
					filters: {
						customer: customer,
						docstatus: 1,
						status: ["!=", "Closed"],
					},
				};
			},
		}
	],
	formatter: function (value, row, column, data, default_formatter) {
		// Varsayılan format
		let formatted = default_formatter(value, row, column, data);

		// Satış Siparişi Durumu: Türkçe + renkli
		if (column.fieldname === "sales_order_status" && value) {
			const map = {
				"Draft": { label: __("Taslak"), color: "gray" },
				"To Deliver and Bill": { label: __("Teslim ve Faturalandırılacak"), color: "orange" },
				"To Deliver": { label: __("Teslim Edilecek"), color: "orange" },
				"To Bill": { label: __("Faturalandırılacak"), color: "orange" },
				"Completed": { label: __("Tamamlandı"), color: "green" },
				"Closed": { label: __("Kapalı"), color: "blue" },
				"Cancelled": { label: __("İptal"), color: "red" },
				// Türkçe değerler için doğrudan eşleşme
				"Taslak": { label: __("Taslak"), color: "gray" },
				"Teslim ve Faturalandırılacak": { label: __("Teslim ve Faturalandırılacak"), color: "orange" },
				"Teslim Edilecek": { label: __("Teslim Edilecek"), color: "orange" },
				"Faturalandırılacak": { label: __("Faturalandırılacak"), color: "orange" },
				"Tamamlandı": { label: __("Tamamlandı"), color: "green" },
				"Kapalı": { label: __("Kapalı"), color: "blue" },
				"İptal": { label: __("İptal"), color: "red" },
				"Onaylandı": { label: __("Onaylandı"), color: "green" },
			};
			const m = map[value] || { label: value, color: "gray" };
			formatted = `<span class="indicator ${m.color}">${m.label}</span>`;
		}

		// İş Emri Durumu: Türkçe + renkli
		if (column.fieldname === "wo_status" && value) {
			const map = {
				"Not Started": { label: __("Başlamadı"), color: "gray" },
				"In Progress": { label: __("Devam Ediyor"), color: "orange" },
				"Stopped": { label: __("Durduruldu"), color: "red" },
				"Completed": { label: __("Tamamlandı"), color: "green" },
				"Cancelled": { label: __("İptal"), color: "red" },
				// Türkçe değerler
				"Başlamadı": { label: __("Başlamadı"), color: "gray" },
				"Devam Ediyor": { label: __("Devam Ediyor"), color: "orange" },
				"Durduruldu": { label: __("Durduruldu"), color: "red" },
				"Tamamlandı": { label: __("Tamamlandı"), color: "green" },
				"İptal": { label: __("İptal"), color: "red" },
			};
			const m = map[value] || { label: value, color: "gray" };
			formatted = `<span class="indicator ${m.color}">${m.label}</span>`;
		}

		return formatted;
	},
};


