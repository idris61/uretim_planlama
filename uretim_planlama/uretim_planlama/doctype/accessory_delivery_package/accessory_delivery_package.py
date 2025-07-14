# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AccessoryDeliveryPackage(Document):
	def validate(self):
		frappe.log_error("AccessoryDeliveryPackage validate çalıştı", "DEBUG")
		print("AccessoryDeliveryPackage validate çalıştı")
		if self.sales_order and not self.item_list:
			frappe.log_error(f"Sales Order: {self.sales_order}, Item List Length: {len(self.item_list) if self.item_list else 0}", "DEBUG")
			print(f"Sales Order: {self.sales_order}, Item List Length: {len(self.item_list) if self.item_list else 0}")
			
			items = frappe.call('uretim_planlama.uretim_planlama.api.get_bom_materials_by_sales_order', sales_order=self.sales_order)
			frappe.log_error(f"API'den gelen malzeme sayısı: {len(items) if items else 0}", "DEBUG")
			print(f"API'den gelen malzeme sayısı: {len(items) if items else 0}")
			
			if items:
				frappe.log_error("Malzemeleri tabloya eklemeye başlıyorum...", "DEBUG")
				print("Malzemeleri tabloya eklemeye başlıyorum...")
				
				for i, item in enumerate(items):
					try:
						row = self.append('item_list', {})
						row.item_code = item.get('item_code')
						row.item_name = item.get('item_name')
						row.qty = item.get('qty')
						row.uom = item.get('uom')
						frappe.log_error(f"Malzeme {i+1} eklendi: {item.get('item_code')}", "DEBUG")
						print(f"Malzeme {i+1} eklendi: {item.get('item_code')}")
					except Exception as e:
						frappe.log_error(f"Malzeme eklenirken hata: {str(e)}", "DEBUG")
						print(f"Malzeme eklenirken hata: {str(e)}")
				
				frappe.log_error(f"Toplam {len(items)} malzeme eklendi", "DEBUG")
				print(f"Toplam {len(items)} malzeme eklendi")
			else:
				frappe.log_error("API'den malzeme gelmedi", "DEBUG")
				print("API'den malzeme gelmedi")
