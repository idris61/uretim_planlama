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
		tuple: (columns, data, message, chart, report_summary, skip_total_row)
	"""
	# Önce veriyi al, sonra kullanılan statülere göre kolonları oluştur
	data = get_data(filters)
	columns = get_columns(filters)
	# skip_total_row=True çünkü manuel olarak toplam satırı ekliyoruz
	return columns, data, None, None, None, True


def get_columns(filters=None):
	"""Rapor kolonlarını tanımlar."""
	columns = [
		{
			"fieldname": "kullanici",
			"label": _("Kullanıcı"),
			"fieldtype": "Link",
			"options": "User",
			"width": 180,
		},
		{
			"fieldname": "kullanici_adi",
			"label": _("Kullanıcı Adı"),
			"fieldtype": "Data",
			"width": 150,
		},
	]
	
	# Sadece kullanılan statüleri göster (filtrelerle önceden kontrol et)
	# Önce veriyi alıp hangi statülerin kullanıldığını tespit et
	used_lead_statuses, used_opp_statuses = get_used_statuses(filters)
	
	# Lead statü kolonları (sadece kullanılanlar)
	for status in used_lead_statuses:
		fieldname = f"lead_{frappe.scrub(status)}"
		label = get_lead_status_label(status)
		# Sütun genişliğini etiket uzunluğuna göre ayarla
		width = max(120, min(180, len(label) * 8 + 20))
		columns.append({
			"fieldname": fieldname,
			"label": label,
			"fieldtype": "Int",
			"width": width,
		})
	
	# Opportunity statü kolonları (sadece kullanılanlar)
	for status in used_opp_statuses:
		fieldname = f"opp_{frappe.scrub(status)}"
		label = get_opportunity_status_label(status)
		# Sütun genişliğini etiket uzunluğuna göre ayarla
		width = max(120, min(180, len(label) * 8 + 20))
		columns.append({
			"fieldname": fieldname,
			"label": label,
			"fieldtype": "Int",
			"width": width,
		})
	
	# Toplam kolonları
	columns.extend([
		{
			"fieldname": "lead_toplam",
			"label": _("Müşteri Adayı Toplam"),
			"fieldtype": "Int",
			"width": 160,
		},
		{
			"fieldname": "opp_toplam",
			"label": _("Fırsat Toplam"),
			"fieldtype": "Int",
			"width": 140,
		},
		{
			"fieldname": "toplam_calisma",
			"label": _("Toplam Çalışma"),
			"fieldtype": "Int",
			"width": 140,
		},
	])
	
	return columns


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
	
	# Lead verilerini statü bazında getir
	lead_statuses = get_lead_statuses()
	lead_query = """
		SELECT 
			owner,
			status,
			COUNT(*) as lead_count
		FROM `tabLead`
		WHERE docstatus = 0
		{date_conditions}
		{user_condition}
		GROUP BY owner, status
	""".format(
		date_conditions=date_sql,
		user_condition=user_condition
	)
	
	lead_data = frappe.db.sql(lead_query, params, as_dict=True)
	
	# Opportunity verilerini statü bazında getir
	opp_statuses = get_opportunity_statuses()
	opp_query = """
		SELECT 
			owner,
			status,
			COUNT(*) as opp_count
		FROM `tabOpportunity`
		WHERE docstatus = 0
		{date_conditions}
		{user_condition}
		GROUP BY owner, status
	""".format(
		date_conditions=date_sql,
		user_condition=user_condition
	)
	
	opp_data = frappe.db.sql(opp_query, params, as_dict=True)
	
	# Kullanılan statüleri tespit et
	used_lead_statuses = sorted(set([row.status for row in lead_data if row.status]))
	used_opp_statuses = sorted(set([row.status for row in opp_data if row.status]))
	
	# Verileri birleştir
	user_stats = {}
	
	# Lead verilerini ekle
	for row in lead_data:
		user = row.owner
		status = row.status or "Unknown"
		
		if user not in user_stats:
			user_stats[user] = initialize_user_stats(user, used_lead_statuses, used_opp_statuses)
		
		fieldname = f"lead_{frappe.scrub(status)}"
		user_stats[user][fieldname] = row.lead_count
		user_stats[user]["lead_toplam"] = user_stats[user].get("lead_toplam", 0) + row.lead_count
	
	# Opportunity verilerini ekle
	for row in opp_data:
		user = row.owner
		status = row.status or "Unknown"
		
		if user not in user_stats:
			user_stats[user] = initialize_user_stats(user, used_lead_statuses, used_opp_statuses)
		
		fieldname = f"opp_{frappe.scrub(status)}"
		user_stats[user][fieldname] = row.opp_count
		user_stats[user]["opp_toplam"] = user_stats[user].get("opp_toplam", 0) + row.opp_count
	
	# Toplam çalışmayı hesapla
	for user in user_stats:
		lead_total = user_stats[user].get("lead_toplam", 0)
		opp_total = user_stats[user].get("opp_toplam", 0)
		user_stats[user]["toplam_calisma"] = lead_total + opp_total
	
	# Listeye dönüştür ve sırala (toplam çalışmaya göre azalan)
	result = list(user_stats.values())
	result.sort(key=lambda x: x.get("toplam_calisma", 0), reverse=True)
	
	# Toplam satırı ekle
	if result:
		# Kullanılan statüleri tespit et
		used_lead_statuses = sorted(set([row.status for row in lead_data if row.status]))
		used_opp_statuses = sorted(set([row.status for row in opp_data if row.status]))
		
		total_row = initialize_user_stats("", used_lead_statuses, used_opp_statuses)
		total_row["kullanici_adi"] = _("TOPLAM")
		
		# Lead statüleri toplamı
		for status in used_lead_statuses:
			fieldname = f"lead_{frappe.scrub(status)}"
			total_row[fieldname] = sum(row.get(fieldname, 0) for row in result)
		
		# Opportunity statüleri toplamı
		for status in used_opp_statuses:
			fieldname = f"opp_{frappe.scrub(status)}"
			total_row[fieldname] = sum(row.get(fieldname, 0) for row in result)
		
		total_row["lead_toplam"] = sum(row.get("lead_toplam", 0) for row in result)
		total_row["opp_toplam"] = sum(row.get("opp_toplam", 0) for row in result)
		total_row["toplam_calisma"] = sum(row.get("toplam_calisma", 0) for row in result)
		
		result.append(total_row)
	
	return result


def initialize_user_stats(user, used_lead_statuses=None, used_opp_statuses=None):
	"""Kullanıcı istatistikleri için başlangıç dict'i oluşturur."""
	stats = {
		"kullanici": user,
		"kullanici_adi": get_user_full_name(user) if user else "",
		"lead_toplam": 0,
		"opp_toplam": 0,
		"toplam_calisma": 0,
	}
	
	# Sadece kullanılan statüleri başlat
	if used_lead_statuses is None:
		used_lead_statuses = get_lead_statuses()
	if used_opp_statuses is None:
		used_opp_statuses = get_opportunity_statuses()
	
	# Lead statü kolonlarını başlat
	for status in used_lead_statuses:
		fieldname = f"lead_{frappe.scrub(status)}"
		stats[fieldname] = 0
	
	# Opportunity statü kolonlarını başlat
	for status in used_opp_statuses:
		fieldname = f"opp_{frappe.scrub(status)}"
		stats[fieldname] = 0
	
	return stats


def get_lead_statuses():
	"""Lead statülerini getirir."""
	# ERPNext'teki standart Lead statüleri
	default_statuses = [
		"Lead",
		"Open",
		"Replied",
		"Opportunity",
		"Quotation",
		"Lost Quotation",
		"Interested",
		"Converted",
		"Do Not Contact",
	]
	
	# Veritabanındaki mevcut statüleri al
	try:
		existing_statuses = frappe.db.sql(
			"SELECT DISTINCT status FROM `tabLead` WHERE status IS NOT NULL AND status != '' ORDER BY status",
			as_dict=True
		)
		db_statuses = [s.status for s in existing_statuses]
		
		# Hem default hem de veritabanındaki statüleri birleştir
		all_statuses = list(set(default_statuses + db_statuses))
		# Sıralamayı koru
		ordered_statuses = [s for s in default_statuses if s in all_statuses]
		ordered_statuses.extend([s for s in all_statuses if s not in ordered_statuses])
		
		return ordered_statuses
	except:
		return default_statuses


def get_opportunity_statuses():
	"""Opportunity statülerini getirir."""
	# ERPNext'teki standart Opportunity statüleri
	default_statuses = [
		"Open",
		"Quotation",
		"Converted",
		"Lost",
		"Replied",
		"Closed",
	]
	
	# Veritabanındaki mevcut statüleri al
	try:
		existing_statuses = frappe.db.sql(
			"SELECT DISTINCT status FROM `tabOpportunity` WHERE status IS NOT NULL AND status != '' ORDER BY status",
			as_dict=True
		)
		db_statuses = [s.status for s in existing_statuses]
		
		# Hem default hem de veritabanındaki statüleri birleştir
		all_statuses = list(set(default_statuses + db_statuses))
		# Sıralamayı koru
		ordered_statuses = [s for s in default_statuses if s in all_statuses]
		ordered_statuses.extend([s for s in all_statuses if s not in ordered_statuses])
		
		return ordered_statuses
	except:
		return default_statuses


def get_user_full_name(user):
	"""Kullanıcının tam adını getirir."""
	if not user:
		return ""
	
	try:
		full_name = frappe.db.get_value("User", user, "full_name")
		return full_name or user
	except:
		return user


def get_lead_status_label(status):
	"""Lead statüsü için Türkçe etiket döndürür."""
	status_map = {
		"Lead": _("Müşteri Adayı"),
		"Open": _("Müşteri Adayı: Açık"),
		"Replied": _("Müşteri Adayı: Yanıtlandı"),
		"Opportunity": _("Müşteri Adayı: Fırsat"),
		"Quotation": _("Müşteri Adayı: Teklif"),
		"Lost Quotation": _("Müşteri Adayı: Teklif Kaybedildi"),
		"Interested": _("Müşteri Adayı: İlgilenildi"),
		"Converted": _("Müşteri Adayı: Dönüştürüldü"),
		"Do Not Contact": _("Müşteri Adayı: İletişime Geçmeyin"),
	}
	return status_map.get(status, _("Müşteri Adayı: {0}").format(status))


def get_opportunity_status_label(status):
	"""Opportunity statüsü için Türkçe etiket döndürür."""
	status_map = {
		"Open": _("Fırsat: Açık"),
		"Quotation": _("Fırsat: Teklif"),
		"Converted": _("Fırsat: Dönüştürüldü"),
		"Lost": _("Fırsat: Kaybedildi"),
		"Replied": _("Fırsat: Yanıtlandı"),
		"Closed": _("Fırsat: Kapatıldı"),
	}
	return status_map.get(status, _("Fırsat: {0}").format(status))


def get_used_statuses(filters):
	"""Filtrelere göre kullanılan statüleri tespit eder."""
	# Filtreleri hazırla
	from_date = filters.get("from_date") if filters else None
	to_date = filters.get("to_date") if filters else None
	user_filter = filters.get("user") if filters else None
	
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
	
	# Kullanılan Lead statülerini al
	lead_query = """
		SELECT DISTINCT status
		FROM `tabLead`
		WHERE docstatus = 0
		AND status IS NOT NULL
		AND status != ''
		{date_conditions}
		{user_condition}
	""".format(
		date_conditions=date_sql,
		user_condition=user_condition
	)
	
	lead_statuses = frappe.db.sql(lead_query, params, as_dict=True)
	used_lead_statuses = sorted([s.status for s in lead_statuses])
	
	# Kullanılan Opportunity statülerini al
	opp_query = """
		SELECT DISTINCT status
		FROM `tabOpportunity`
		WHERE docstatus = 0
		AND status IS NOT NULL
		AND status != ''
		{date_conditions}
		{user_condition}
	""".format(
		date_conditions=date_sql,
		user_condition=user_condition
	)
	
	opp_statuses = frappe.db.sql(opp_query, params, as_dict=True)
	used_opp_statuses = sorted([s.status for s in opp_statuses])
	
	return used_lead_statuses, used_opp_statuses

