// Copyright (c) 2025, idris and contributors
// For license information, please see license.txt

frappe.query_reports["CRM Çalışma Raporu"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("Başlangıç Tarihi"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("Bitiş Tarihi"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "user",
			label: __("Kullanıcı"),
			fieldtype: "Link",
			options: "User",
		},
	],
};


