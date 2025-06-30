# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
	return [
		{
			"module_name": "Uretim Planlama",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Uretim Planlama")
		},
		{
			"module_name": "Long Term Reserve Usage",
			"color": "orange",
			"icon": "octicon octicon-clock",
			"type": "list",
			"label": _("Uzun Vadeli Rezerv Kullanımı"),
			"link": "List/Long Term Reserve Usage"
		},
		{
			"module_name": "Long Term Reserve Usage Report",
			"color": "blue",
			"icon": "octicon octicon-graph",
			"type": "report",
			"label": _("Uzun Vadeli Rezerv Raporu"),
			"link": "query-report/Long Term Reserve Usage Report"
		}
	] 