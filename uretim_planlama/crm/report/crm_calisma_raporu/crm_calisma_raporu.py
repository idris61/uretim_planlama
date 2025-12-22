# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
CRM Çalışma Raporu
Kullanıcıların ne kadar Lead ve Opportunity oluşturduğunu gösterir.
"""

import frappe
from frappe import _
from frappe.utils import getdate, flt


def execute(filters=None):
	"""
	Raporu çalıştırır ve kullanıcı bazında CRM çalışma istatistiklerini döndürür.
	
	Args:
		filters: Filtreler (from_date, to_date, user vb.)
	
	Returns:
		tuple: (columns, data)
	"""
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	"""Rapor kolonlarını tanımlar."""
	return [
		{
			"fieldname": "kullanici",
			"label": _("Kullanıcı"),
			"fieldtype": "Link",
			"options": "User",
			"width": 200,
		},
		{
			"fieldname": "kullanici_adi",
			"label": _("Kullanıcı Adı"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "lead_sayisi",
			"label": _("Müşteri Adayı Sayısı"),
			"fieldtype": "Int",
			"width": 150,
		},
		{
			"fieldname": "firsat_sayisi",
			"label": _("Fırsat Sayısı"),
			"fieldtype": "Int",
			"width": 150,
		},
		{
			"fieldname": "toplam_calisma",
			"label": _("Toplam Çalışma"),
			"fieldtype": "Int",
			"width": 150,
		},
		{
			"fieldname": "son_lead_tarihi",
			"label": _("Son Lead Tarihi"),
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"fieldname": "son_firsat_tarihi",
			"label": _("Son Fırsat Tarihi"),
			"fieldtype": "Date",
			"width": 120,
		},
	]


def get_data(filters):
	"""
	Rapor verilerini getirir.
	
	Args:
		filters: Filtreler
	
	Returns:
		list: Rapor verileri
	"""
	# Filtreleri hazırla
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	user_filter = filters.get("user")
	
	# Tarih filtreleri için SQL koşulları
	date_conditions = []
	params = {}
	
	if from_date:
		date_conditions.append("creation >= %(from_date)s")
		params["from_date"] = from_date
	if to_date:
		date_conditions.append("creation <= %(to_date)s")
		params["to_date"] = f"{to_date} 23:59:59"
	
	date_sql = " AND " + " AND ".join(date_conditions) if date_conditions else ""
	
	# Kullanıcı filtresi
	user_condition = ""
	if user_filter:
		user_condition = " AND owner = %(user_filter)s"
		params["user_filter"] = user_filter
	
	# Lead verilerini getir
	lead_query = """
		SELECT 
			owner,
			COUNT(*) as lead_count,
			MAX(creation) as last_lead_date
		FROM `tabLead`
		WHERE docstatus = 0
		{date_conditions}
		{user_condition}
		GROUP BY owner
	""".format(
		date_conditions=date_sql,
		user_condition=user_condition
	)
	
	lead_data = frappe.db.sql(lead_query, params, as_dict=True)
	
	# Opportunity verilerini getir
	opp_query = """
		SELECT 
			owner,
			COUNT(*) as opp_count,
			MAX(creation) as last_opp_date
		FROM `tabOpportunity`
		WHERE docstatus = 0
		{date_conditions}
		{user_condition}
		GROUP BY owner
	""".format(
		date_conditions=date_sql,
		user_condition=user_condition
	)
	
	opp_data = frappe.db.sql(opp_query, params, as_dict=True)
	
	# Verileri birleştir
	user_stats = {}
	
	# Lead verilerini ekle
	for row in lead_data:
		user = row.owner
		if user not in user_stats:
			user_stats[user] = {
				"kullanici": user,
				"kullanici_adi": get_user_full_name(user),
				"lead_sayisi": 0,
				"firsat_sayisi": 0,
				"toplam_calisma": 0,
				"son_lead_tarihi": None,
				"son_firsat_tarihi": None,
			}
		user_stats[user]["lead_sayisi"] = row.lead_count
		# Tarihi string'e çevir
		if row.last_lead_date:
			user_stats[user]["son_lead_tarihi"] = getdate(row.last_lead_date).strftime("%Y-%m-%d")
	
	# Opportunity verilerini ekle
	for row in opp_data:
		user = row.owner
		if user not in user_stats:
			user_stats[user] = {
				"kullanici": user,
				"kullanici_adi": get_user_full_name(user),
				"lead_sayisi": 0,
				"firsat_sayisi": 0,
				"toplam_calisma": 0,
				"son_lead_tarihi": None,
				"son_firsat_tarihi": None,
			}
		user_stats[user]["firsat_sayisi"] = row.opp_count
		# Tarihi string'e çevir
		if row.last_opp_date:
			user_stats[user]["son_firsat_tarihi"] = getdate(row.last_opp_date).strftime("%Y-%m-%d")
	
	# Toplam çalışmayı hesapla
	for user in user_stats:
		user_stats[user]["toplam_calisma"] = (
			user_stats[user]["lead_sayisi"] + user_stats[user]["firsat_sayisi"]
		)
	
	# Listeye dönüştür ve sırala (toplam çalışmaya göre azalan)
	result = list(user_stats.values())
	result.sort(key=lambda x: x["toplam_calisma"], reverse=True)
	
	# Toplam satırı ekle
	if result:
		total_row = {
			"kullanici": "",
			"kullanici_adi": _("TOPLAM"),
			"lead_sayisi": sum(row["lead_sayisi"] for row in result),
			"firsat_sayisi": sum(row["firsat_sayisi"] for row in result),
			"toplam_calisma": sum(row["toplam_calisma"] for row in result),
			"son_lead_tarihi": None,
			"son_firsat_tarihi": None,
		}
		result.append(total_row)
	
	return result


def get_user_full_name(user):
	"""Kullanıcının tam adını getirir."""
	if not user:
		return ""
	
	try:
		full_name = frappe.db.get_value("User", user, "full_name")
		return full_name or user
	except:
		return user

