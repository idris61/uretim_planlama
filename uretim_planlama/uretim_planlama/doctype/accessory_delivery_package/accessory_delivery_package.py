# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


@frappe.whitelist()
def get_sales_orders_for_opti(opti):
	"""Opti için teslim edilmemiş Sales Order'ları döndür"""
	if not opti:
		return []
	
	# Opti SO Item child table'dan sales_order'ları çek
	sales_orders = frappe.db.get_all(
		"Opti SO Item",
		filters={
			"parent": opti,
			"delivered": 0
		},
		fields=["sales_order"],
		pluck="sales_order"
	)
	
	return sales_orders or []


class AccessoryDeliveryPackage(Document):
	"""Aksesuar Teslimat Paketi - Opti bazlı teslimat yönetimi"""
	
	def validate(self):
		"""Doküman validasyonu - Opti ve Sales Order kontrolü"""
		# Opti kontrolü
		if not self.opti:
			frappe.throw(frappe._("Opti numarası zorunludur"))
		
		# Sales Order kontrolü
		if not self.sales_order:
			frappe.throw(frappe._("Satış Siparişi zorunludur"))
		
		# Opti ve SO kombinasyonu geçerli mi?
		if not self._validate_opti_sales_order():
			frappe.throw(
				frappe._("Satış Siparişi [{0}], Opti [{1}] içinde bulunamadı").format(
					self.sales_order, self.opti
				)
			)

	def on_submit(self):
		"""Submit - Teslimat durumunu güncelle"""
		# SO Item teslimat durumu kontrol ve güncelleme
		if self._is_already_delivered():
			frappe.throw(
				frappe._("Bu ürünler zaten teslim edilmiş. Lütfen Opti veya Sipariş değiştirin")
			)
		
		self._mark_so_item_delivered()
		self._update_opti_delivery_status()

	def on_cancel(self):
		"""Cancel - Teslimat durumunu geri al"""
		self._mark_so_item_undelivered()
		self._update_opti_delivery_status_on_cancel()

	def _validate_opti_sales_order(self):
		"""Opti ve Sales Order kombinasyonunu kontrol et"""
		return frappe.db.exists(
			"Opti SO Item",
			{"parent": self.opti, "sales_order": self.sales_order}
		)

	def _is_already_delivered(self):
		"""SO Item zaten teslim edilmiş mi?"""
		delivered = frappe.db.get_value(
			"Opti SO Item",
			{"parent": self.opti, "sales_order": self.sales_order},
			"delivered"
		)
		return delivered == 1

	def _mark_so_item_delivered(self):
		"""SO Item'ı teslim edildi olarak işaretle"""
		frappe.db.set_value(
			"Opti SO Item",
			{"parent": self.opti, "sales_order": self.sales_order},
			"delivered",
			1
		)

	def _mark_so_item_undelivered(self):
		"""SO Item'ın teslimat durumunu geri al"""
		frappe.db.set_value(
			"Opti SO Item",
			{"parent": self.opti, "sales_order": self.sales_order},
			"delivered",
			0
		)

	def _update_opti_delivery_status(self):
		"""Opti teslimat durumunu güncelle - Tüm SO'lar teslim edildiyse Opti'yi işaretle"""
		# Opti'deki tüm SO itemları teslim edildi mi?
		undelivered_count = frappe.db.count(
			"Opti SO Item",
			{"parent": self.opti, "delivered": 0}
		)
		
		# Tümü teslim edildiyse Opti'yi işaretle
		if undelivered_count == 0:
			frappe.db.set_value("Opti", self.opti, "delivered", 1)

	def _update_opti_delivery_status_on_cancel(self):
		"""İptal durumunda Opti teslimat durumunu güncelle"""
		# Opti delivered ise sıfırla (bir SO iptal edildi)
		opti_delivered = frappe.db.get_value("Opti", self.opti, "delivered")
		if opti_delivered == 1:
			frappe.db.set_value("Opti", self.opti, "delivered", 0)
