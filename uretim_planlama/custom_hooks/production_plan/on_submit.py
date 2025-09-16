import frappe


def on_submit(doc, method):
	# Uretim Plani - Production Plan - On Submit (START)

	existing_opti_doc = frappe.db.exists("Opti", doc.custom_opti_no)
	if existing_opti_doc:
		frappe.throw(
			frappe._("Opti No [{0}] is already in use").format(str(existing_opti_doc))
		)

	so_items = []

	for so in doc.sales_orders:
		so_items.append({"sales_order": so.sales_order})

	opti_doc = frappe.new_doc("Opti")
	opti_doc.update({"opti_no": doc.custom_opti_no, "production_plan": doc.name})
	opti_doc.set("sales_orders", so_items)
	opti_doc.save(ignore_permissions=True)

	# Uretim Plani - Production Plan - On Submit (END)
