# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def get_profile_stock_panel(profil=None, depo=None, scrap=0):
	"""
	Profil Stok Paneli verilerini döner.

	İş kuralları:
	- Depo Bazında Toplam Profil Stoku  -> ERPNext çekirdek stok verisinden (Bin)
	- Boy Bazında Profil Stok Detayı   -> Profile Stock Ledger (özel belge)
	- Parça Profil Kayıtları (scrap)   -> Profile Stock Ledger (is_scrap_piece = 1)
	- Hammadde Rezervleri              -> Rezerved Raw Materials
	"""
	try:
		scrap = int(scrap or 0)

		# 1) Depo bazında stoklar (çekirdek ERPNext stok verisi)
		depo_stoklari = _get_depo_bazinda_stoklar(profil=profil, depo=depo)

		# 2) Boy bazında ve scrap profiller (Profile Stock Ledger)
		boy_bazinda_stok, scrap_profiller, ledger_stats = _get_profile_ledger_stoklar(
			profil=profil,
			scrap=scrap,
		)

		# 3) Hammadde rezervleri
		hammadde_rezervleri = _get_hammadde_rezervleri(profil=profil)

		return {
			"depo_stoklari": depo_stoklari,
			"boy_bazinda_stok": boy_bazinda_stok,
			"scrap_profiller": scrap_profiller,
			"hammadde_rezervleri": hammadde_rezervleri,
			# Genel istatistikler (Profile Stock Ledger bazlı)
			"total_items": ledger_stats["total_items"],
			"total_qty": ledger_stats["total_qty"],
			"total_length": ledger_stats["total_length"],
		}

	except Exception as e:
		frappe.log_error(f"get_profile_stock_panel error: {str(e)}", "Profile Stock Panel Error")
		return {"error": str(e)}


def _get_depo_bazinda_stoklar(profil: str | None, depo: str | None):
	"""
	ERPNext çekirdek stok verisinden (Bin) depo bazında fiziki stok miktarlarını getirir.

	- Ürün kartındaki Stok Seviyeleri ve Stok Özeti raporundaki dağılımla uyumlu olmalı.
	- Profil seçilmemişse, depo bazında profil bilgisi gösterilmez (boş döner).
	"""
	# Profil seçili değilse bu tabloyu boş bırakıyoruz
	if not profil:
		return []

	depo_stoklari = []

	item_name = frappe.db.get_value("Item", profil, "item_name") or profil

	bin_filters = {"item_code": profil}
	if depo:
		bin_filters["warehouse"] = depo

	bins = frappe.get_all(
		"Bin",
		filters=bin_filters,
		fields=["warehouse", "actual_qty"],
		order_by="warehouse",
	)

	for row in bins:
		actual_qty = flt(row.actual_qty)
		if not actual_qty:
			continue

		depo_stoklari.append(
			{
				"depo": row.warehouse,
				"profil": profil,
				"profil_adi": item_name,
				"toplam_stok_mtul": actual_qty,
			}
		)

	return depo_stoklari


def _get_profile_ledger_stoklar(profil: str | None, scrap: int):
	"""
	Profile Stock Ledger'dan boy bazında stok ve scrap verilerini çeker.

	- Boy Bazında Profil Stok Detayı tablosu için temel kaynaktır.
	- Scrap = 1 iken parça profiller listesi de oluşturulur.
	"""
	filters = {"is_scrap_piece": scrap}
	if profil:
		filters["item_code"] = profil

	# Performans: Profil seçilmeden tüm kayıtları çekmek çok yavaş olabilir
	# Bu nedenle limit ekliyoruz. İş kuralı gereği daha fazla kayıt gerekiyorsa
	# sayfalama veya farklı bir yaklaşım düşünülebilir.
	# Limit'i artırdık ama yine de sınırlı tutuyoruz
	limit = 5000 if not profil else None

	# Performans optimizasyonu: Sadece qty > 0 olan kayıtları çek
	# frappe.get_all filters dict'inde list kullanarak operatör belirtiyoruz
	filters["qty"] = [">", 0]
	
	stocks = frappe.get_all(
		"Profile Stock Ledger",
		filters=filters,
		fields=["item_code", "length", "qty", "total_length", "modified"],
		order_by="item_code, length",
		limit=limit,
	)
	
	# Python tarafında da filtreleme yap (qty > 0)
	# Çünkü frappe.get_all'da ["qty", ">", 0] formatı çalışmayabilir
	stocks = [s for s in stocks if flt(s.qty) > 0]

	if not stocks:
		return [], [], {"total_items": 0, "total_qty": 0, "total_length": 0}

	# Ürün isimlerini tek sorguda al (N+1 sorgu yerine)
	item_codes = {row.item_code for row in stocks}
	item_names = {
		row.item_code: (row.item_name or row.item_code)
		for row in frappe.get_all(
			"Item",
			filters={"item_code": ["in", list(item_codes)]},
			fields=["item_code", "item_name"],
		)
	}

	boy_bazinda_stok = []
	scrap_profiller = []

	for stock in stocks:
		item_name = item_names.get(stock.item_code, stock.item_code)

		# Boy bazında stok detayı
		boy_bazinda_stok.append(
			{
				"profil": stock.item_code,
				"profil_adi": item_name,
				"boy": stock.length or 0,
				"adet": stock.qty or 0,
				"mtul": stock.total_length or 0,
				"guncelleme": stock.modified,
			}
		)

		# Scrap profiller (eğer scrap=1 ise)
		if scrap:
			scrap_profiller.append(
				{
					"profil": stock.item_code,
					"profil_adi": item_name,
					"boy": stock.length or 0,
					"adet": stock.qty or 0,
					"mtul": stock.total_length or 0,
					"aciklama": _("Hurda profil"),
					"tarih": stock.modified,
					"guncelleme": stock.modified,
				}
			)

	stats = {
		"total_items": len(stocks),
		"total_qty": sum(flt(stock.qty) for stock in stocks),
		"total_length": sum(flt(stock.total_length) for stock in stocks),
	}

	return boy_bazinda_stok, scrap_profiller, stats


def _get_hammadde_rezervleri(profil: str | None):
	"""Hammadde rezervlerini tek seferde ve performanslı şekilde döner."""
	rezerv_filters = {}
	if profil:
		rezerv_filters["item_code"] = profil
	
	# Sadece quantity > 0 olan kayıtları çek
	# frappe.get_all'da ["quantity", ">", 0] formatı çalışmayabilir, Python tarafında filtreleyeceğiz

	try:
		rezervler = frappe.get_all(
			"Rezerved Raw Materials",
			filters=rezerv_filters,
			fields=["item_code", "quantity", "sales_order"],
			order_by="item_code",
			limit=10000 if not profil else None,  # Profil seçilmeden limit ekle
		)
		
		# Python tarafında quantity > 0 filtrele
		rezervler = [r for r in rezervler if flt(r.quantity) > 0]
	except Exception as e:
		frappe.log_error(f"Hammadde rezervleri çekme hatası: {str(e)}")
		return []

	if not rezervler:
		return []

	item_codes = {row.item_code for row in rezervler}
	item_names = {
		row.item_code: (row.item_name or row.item_code)
		for row in frappe.get_all(
			"Item",
			filters={"item_code": ["in", list(item_codes)]},
			fields=["item_code", "item_name"],
		)
	}

	hammadde_rezervleri = []
	for rezerv in rezervler:
		item_name = item_names.get(rezerv.item_code, rezerv.item_code)
		hammadde_rezervleri.append(
			{
				"item_code": rezerv.item_code,
				"item_name": item_name,
				"quantity": flt(rezerv.quantity),
				"sales_order": rezerv.sales_order or "",
			}
		)

	return hammadde_rezervleri


@frappe.whitelist()
def get_profile_stock_overview():
	"""Profil stok genel bakış verisi döner"""
	try:
		# Normal stoklar
		normal_stocks = frappe.get_all(
			"Profile Stock Ledger",
			filters={"is_scrap_piece": 0},
			fields=["item_code", "length", "qty", "total_length"]
		)
		
		# Hurda stoklar
		scrap_stocks = frappe.get_all(
			"Profile Stock Ledger",
			filters={"is_scrap_piece": 1},
			fields=["item_code", "length", "qty", "total_length"]
		)
		
		# Toplam hesaplamalar
		total_normal_qty = sum(stock.qty for stock in normal_stocks)
		total_normal_length = sum(stock.total_length for stock in normal_stocks)
		total_scrap_qty = sum(stock.qty for stock in scrap_stocks)
		total_scrap_length = sum(stock.total_length for stock in scrap_stocks)
		
		return {
			"normal_stocks": {
				"items": normal_stocks,
				"total_qty": total_normal_qty,
				"total_length": total_normal_length,
				"count": len(normal_stocks)
			},
			"scrap_stocks": {
				"items": scrap_stocks,
				"total_qty": total_scrap_qty,
				"total_length": total_scrap_length,
				"count": len(scrap_stocks)
			},
			"summary": {
				"total_items": len(normal_stocks) + len(scrap_stocks),
				"total_qty": total_normal_qty + total_scrap_qty,
				"total_length": total_normal_length + total_scrap_length
			}
		}
		
	except Exception as e:
		frappe.log_error(f"get_profile_stock_overview error: {str(e)}", "Profile Stock Overview Error")
		return {"error": str(e)}


@frappe.whitelist()
def search_profile_stocks(search_term="", profile_type="", length="", scrap=0):
	"""Profil stok arama fonksiyonu"""
	try:
		filters = {"is_scrap_piece": int(scrap)}
		
		if search_term:
			filters["item_code"] = ["like", f"%{search_term}%"]
		if profile_type:
			filters["item_code"] = profile_type
		if length:
			filters["length"] = float(length)
		
		stocks = frappe.get_all(
			"Profile Stock Ledger",
			filters=filters,
			fields=["item_code", "length", "qty", "total_length", "modified"],
			order_by="item_code, length"
		)
		
		# Ürün bilgilerini ekle
		for stock in stocks:
			item_name = frappe.db.get_value("Item", stock.item_code, "item_name")
			stock["item_name"] = item_name or stock.item_code
			stock["last_updated"] = frappe.utils.time_diff(stock.modified, frappe.utils.now())
		
		return stocks
		
	except Exception as e:
		frappe.log_error(f"search_profile_stocks error: {str(e)}", "Profile Stock Search Error")
		return []
