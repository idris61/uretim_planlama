import frappe


def on_cancel(doc, method):
	# Uretim Plani - Production Plan - On Cancel (START)

	existing_opti_name = frappe.db.exists("Opti", doc.custom_opti_no)
	if not existing_opti_name:
		return
	else:
		frappe.delete_doc("Opti", existing_opti_name)

	# Uretim Plani - Production Plan - On Cancel (END)
