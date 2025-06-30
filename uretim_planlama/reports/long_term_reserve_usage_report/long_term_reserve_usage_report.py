# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "sales_order",
			"label": _("Satış Siparişi"),
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 120
		},
		{
			"fieldname": "customer",
			"label": _("Müşteri"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 120
		},
		{
			"fieldname": "item_code",
			"label": _("Hammadde"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 100
		},
		{
			"fieldname": "item_name",
			"label": _("Hammadde Adı"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "used_qty",
			"label": _("Kullanılan Miktar"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "usage_date",
			"label": _("Kullanım Tarihi"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "status",
			"label": _("Durum"),
			"fieldtype": "Data",
			"width": 80
		},
		{
			"fieldname": "description",
			"label": _("Açıklama"),
			"fieldtype": "Data",
			"width": 200
		}
	]

def get_data(filters):
	conditions = "1=1"
	
	if filters.get("sales_order"):
		conditions += f" AND ltr.sales_order = '{filters.sales_order}'"
	
	if filters.get("item_code"):
		conditions += f" AND ltr.item_code = '{filters.item_code}'"
	
	if filters.get("status"):
		conditions += f" AND ltr.status = '{filters.status}'"
	
	if filters.get("from_date"):
		conditions += f" AND ltr.usage_date >= '{filters.from_date}'"
	
	if filters.get("to_date"):
		conditions += f" AND ltr.usage_date <= '{filters.to_date}'"
	
	query = f"""
		SELECT 
			ltr.sales_order,
			so.customer,
			ltr.item_code,
			ltr.item_name,
			ltr.used_qty,
			ltr.usage_date,
			ltr.status,
			ltr.description
		FROM `tabLong Term Reserve Usage` ltr
		LEFT JOIN `tabSales Order` so ON ltr.sales_order = so.name
		WHERE {conditions}
		ORDER BY ltr.usage_date DESC, ltr.creation DESC
	"""
	
	return frappe.db.sql(query, as_dict=True) 