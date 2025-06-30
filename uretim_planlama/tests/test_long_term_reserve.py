# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.utils import nowdate, add_days
from uretim_planlama.sales_order_hooks.raw_materials import (
	get_long_term_reserve_qty,
	use_long_term_reserve_bulk,
	check_long_term_reserve_availability
)

class TestLongTermReserve(unittest.TestCase):
	def setUp(self):
		# Test verilerini hazırla
		self.create_test_data()
	
	def create_test_data(self):
		# Test item oluştur
		if not frappe.db.exists("Item", "TEST-ITEM-001"):
			item = frappe.new_doc("Item")
			item.item_code = "TEST-ITEM-001"
			item.item_name = "Test Hammadde 1"
			item.item_group = "Raw Material"
			item.stock_uom = "Nos"
			item.insert(ignore_permissions=True)
		
		# Test Sales Order oluştur
		if not frappe.db.exists("Sales Order", "TEST-SO-001"):
			so = frappe.new_doc("Sales Order")
			so.customer = frappe.db.get_value("Customer", {"customer_name": "Test Customer"}) or "Test Customer"
			so.delivery_date = add_days(nowdate(), 45)  # 45 gün sonra
			so.append("items", {
				"item_code": "TEST-ITEM-001",
				"qty": 100,
				"rate": 10
			})
			so.insert(ignore_permissions=True)
			so.submit()
	
	def test_get_long_term_reserve_qty(self):
		# Uzun vadeli rezerv miktarını test et
		qty = get_long_term_reserve_qty("TEST-ITEM-001")
		self.assertIsInstance(qty, (int, float))
	
	def test_use_long_term_reserve_bulk(self):
		# Toplu uzun vadeli rezerv kullanımını test et
		usage_data = [{"item_code": "TEST-ITEM-001", "qty": 10}]
		result = use_long_term_reserve_bulk("TEST-SO-001", usage_data)
		self.assertTrue(result["success"])
	
	def test_check_long_term_reserve_availability(self):
		# Uzun vadeli rezerv kullanılabilirliğini test et
		recommendations = check_long_term_reserve_availability("TEST-SO-001")
		self.assertIsInstance(recommendations, list)
	
	def tearDown(self):
		# Test verilerini temizle
		pass

if __name__ == "__main__":
	unittest.main() 