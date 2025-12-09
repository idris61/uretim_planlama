# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
CRM Çalışma Raporu Test Script
Test verisi oluşturur ve raporu test eder.
"""

import frappe
from frappe.utils import nowdate, add_days
from datetime import datetime


def create_test_data():
	"""Test verisi oluşturur."""
	
	# Mevcut kullanıcıları al
	users = frappe.get_all("User", filters={"enabled": 1, "name": ["!=", "Guest"]}, limit=3, fields=["name"])
	
	if not users:
		frappe.throw("Test için en az bir aktif kullanıcı gerekli")
	
	# Test Lead'leri oluştur
	lead_count = 0
	for i, user in enumerate(users):
		for j in range(3):  # Her kullanıcı için 3 Lead
			try:
				lead = frappe.get_doc({
					"doctype": "Lead",
					"lead_name": f"Test Lead {i+1}-{j+1}",
					"company_name": f"Test Company {i+1}-{j+1}",
					"status": "Open",
					"source": "Website",
				})
				lead.flags.ignore_permissions = True
				lead.insert()
				
				# Owner'ı değiştir
				frappe.db.set_value("Lead", lead.name, "owner", user.name)
				frappe.db.set_value("Lead", lead.name, "creation", add_days(nowdate(), -j))
				lead_count += 1
			except Exception as e:
				print(f"Lead oluşturma hatası: {e}")
	
	# Test Opportunity'leri oluştur
	opp_count = 0
	for i, user in enumerate(users):
		for j in range(2):  # Her kullanıcı için 2 Opportunity
			try:
				opp = frappe.get_doc({
					"doctype": "Opportunity",
					"opportunity_from": "Lead",
					"party_name": f"Test Lead {i+1}-{j+1}",
					"opportunity_type": "Sales",
					"status": "Open",
				})
				opp.flags.ignore_permissions = True
				opp.insert()
				
				# Owner'ı değiştir
				frappe.db.set_value("Opportunity", opp.name, "owner", user.name)
				frappe.db.set_value("Opportunity", opp.name, "creation", add_days(nowdate(), -j))
				opp_count += 1
			except Exception as e:
				print(f"Opportunity oluşturma hatası: {e}")
	
	frappe.db.commit()
	
	return {
		"leads_created": lead_count,
		"opportunities_created": opp_count,
		"users": [u.name for u in users]
	}


def test_report():
	"""Raporu test eder."""
	from uretim_planlama.crm.report.crm_calisma_raporu.crm_calisma_raporu import execute
	
	filters = {
		"from_date": add_days(nowdate(), -30),
		"to_date": nowdate()
	}
	
	columns, data = execute(filters)
	
	return {
		"columns_count": len(columns),
		"data_rows": len(data),
		"columns": [col.get("label") for col in columns],
		"sample_data": data[:3] if data else []
	}


if __name__ == "__main__":
	# Test verisi oluştur
	print("Test verisi oluşturuluyor...")
	test_data = create_test_data()
	print(f"Oluşturulan Lead sayısı: {test_data['leads_created']}")
	print(f"Oluşturulan Opportunity sayısı: {test_data['opportunities_created']}")
	print(f"Kullanılan kullanıcılar: {', '.join(test_data['users'])}")
	
	# Raporu test et
	print("\nRapor test ediliyor...")
	report_result = test_report()
	print(f"Kolon sayısı: {report_result['columns_count']}")
	print(f"Veri satırı sayısı: {report_result['data_rows']}")
	print(f"Kolonlar: {', '.join(report_result['columns'])}")
	
	if report_result['sample_data']:
		print("\nÖrnek veri:")
		for row in report_result['sample_data']:
			print(row)


