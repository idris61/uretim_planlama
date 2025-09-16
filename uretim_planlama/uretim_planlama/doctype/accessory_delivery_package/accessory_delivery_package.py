# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AccessoryDeliveryPackage(Document):
	def validate(self):
		pass

	def on_submit(self):
		so_item_doc = self._find_so_item_doc()
		if so_item_doc.delivered:
			frappe.throw(
				frappe._(
					"These items are already delivered, please change Opti or Sales Order"
				)
			)
		so_item_doc.delivered = 1
		so_item_doc.save(ignore_permissions=True)

		opti_doc = self._find_opti_doc()
		all_delivered = all(item.delivered for item in opti_doc.sales_orders)
		if all_delivered:
			opti_doc.delivered = 1
		opti_doc.save(ignore_permissions=True)

	def on_cancel(self):
		so_item_doc = self._find_so_item_doc()
		so_item_doc.delivered = 0
		so_item_doc.save(ignore_permissions=True)

		opti_doc = self._find_opti_doc()
		if opti_doc.delivered != 0:
			opti_doc.delivered = 0
			opti_doc.save(ignore_permissions=True)

	def _find_opti_doc(self):
		try:
			opti_doc = frappe.get_doc("Opti", self.opti)
		except frappe.DoesNotExistError:
			frappe.throw(frappe._("Opti [{0}] not found").format(self.opti))
		except Exception as e:
			frappe.log_error(f"Opti document error: {str(e)}", "Accessory Delivery Package Error")
			frappe.throw(frappe._("An error occured"))

		return opti_doc

	def _find_so_item_doc(self):
		try:
			so_item_doc = frappe.get_doc(
				"Opti SO Item", {"parent": self.opti, "sales_order": self.sales_order}
			)
		except frappe.DoesNotExistError:
			frappe.throw(
				frappe._("Sales Order [{0}] in Opti [{1}] not found").format(
					self.sales_order,
					self.opti,
				)
			)
		except Exception as e:
			frappe.log_error(f"Sales Order Item error: {str(e)}", "Accessory Delivery Package Error")
			frappe.throw(frappe._("An error occured"))

		return so_item_doc
