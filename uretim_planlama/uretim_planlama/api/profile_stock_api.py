# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def get_profile_stock_panel(profil=None, depo=None, scrap=0):
	"""Profil stok paneli için veri döner"""
	try:
		scrap = int(scrap)
		
		# Filtreleri hazırla
		filters = {"is_scrap_piece": scrap}
		
		# Profil filtresi
		if profil:
			filters["profile_type"] = profil
		
		# Depo filtresi (şimdilik kullanılmıyor çünkü profil stok takibinde depo yok)
		# if depo:
		#     filters["warehouse"] = depo
		
		# Profil stoklarını getir
		stocks = frappe.get_all(
			"Profile Stock Ledger",
			filters=filters,
			fields=["profile_type", "length", "qty", "total_length", "modified"],
			order_by="profile_type, length"
		)
		
		# Ürün bilgilerini ekle
		for stock in stocks:
			item_name = frappe.db.get_value("Item", stock.profile_type, "item_name")
			stock["item_name"] = item_name or stock.profile_type
			stock["last_updated"] = frappe.utils.time_diff(stock.modified, frappe.utils.now())
		
		# JavaScript'te beklenen veri yapısını oluştur
		depo_stoklari = []
		boy_bazinda_stok = []
		scrap_profiller = []
		hammadde_rezervleri = []
		
		# Hammadde rezervleri verisini çek
		try:
			rezerv_filters = {}
			if profil:
				rezerv_filters["item_code"] = profil
			
			rezervler = frappe.get_all(
				"Rezerved Raw Materials",
				filters=rezerv_filters,
				fields=["item_code", "quantity", "sales_order", "modified"],
				order_by="item_code"
			)
			
			for rezerv in rezervler:
				item_name = frappe.db.get_value("Item", rezerv.item_code, "item_name")
				hammadde_rezervleri.append({
					"item_code": rezerv.item_code,
					"item_name": item_name or rezerv.item_code,
					"quantity": rezerv.quantity or 0,
					"sales_order": rezerv.sales_order or ""
				})
		except Exception as e:
			frappe.log_error(f"Hammadde rezervleri çekme hatası: {str(e)}")
		
		for stock in stocks:
			# Depo bazında stok (varsayılan depo)
			depo_stoklari.append({
				"depo": "Ana Depo",  # Varsayılan depo
				"profil": stock.profile_type,
				"profil_adi": stock.item_name,
				"toplam_stok_mtul": stock.total_length or 0
			})
			
			# Boy bazında stok
			boy_bazinda_stok.append({
				"profil": stock.profile_type,
				"profil_adi": stock.item_name,
				"boy": stock.length or 0,
				"adet": stock.qty or 0,
				"mtul": stock.total_length or 0,
				"rezerv": 0,  # Rezerv bilgisi yok
				"guncelleme": stock.modified
			})
			
			# Scrap profiller (eğer scrap=1 ise)
			if scrap:
				scrap_profiller.append({
					"profil": stock.profile_type,
					"profil_adi": stock.item_name,
					"boy": stock.length or 0,
					"adet": stock.qty or 0,
					"mtul": stock.total_length or 0,
					"aciklama": "Hurda profil",
					"giris_tarihi": stock.modified,
					"guncelleme": stock.modified
				})
		
		return {
			"depo_stoklari": depo_stoklari,
			"boy_bazinda_stok": boy_bazinda_stok,
			"scrap_profiller": scrap_profiller,
			"hammadde_rezervleri": hammadde_rezervleri,
			"stocks": stocks,  # Orijinal veri de korunuyor
			"total_items": len(stocks),
			"total_qty": sum(stock.qty for stock in stocks),
			"total_length": sum(stock.total_length for stock in stocks)
		}
		
	except Exception as e:
		frappe.log_error(f"get_profile_stock_panel error: {str(e)}", "Profile Stock Panel Error")
		return {"error": str(e)}


@frappe.whitelist()
def get_profile_stock_overview():
	"""Profil stok genel bakış verisi döner"""
	try:
		# Normal stoklar
		normal_stocks = frappe.get_all(
			"Profile Stock Ledger",
			filters={"is_scrap_piece": 0},
			fields=["profile_type", "length", "qty", "total_length"]
		)
		
		# Hurda stoklar
		scrap_stocks = frappe.get_all(
			"Profile Stock Ledger",
			filters={"is_scrap_piece": 1},
			fields=["profile_type", "length", "qty", "total_length"]
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
			filters["profile_type"] = ["like", f"%{search_term}%"]
		if profile_type:
			filters["profile_type"] = profile_type
		if length:
			filters["length"] = float(length)
		
		stocks = frappe.get_all(
			"Profile Stock Ledger",
			filters=filters,
			fields=["profile_type", "length", "qty", "total_length", "modified"],
			order_by="profile_type, length"
		)
		
		# Ürün bilgilerini ekle
		for stock in stocks:
			item_name = frappe.db.get_value("Item", stock.profile_type, "item_name")
			stock["item_name"] = item_name or stock.profile_type
			stock["last_updated"] = frappe.utils.time_diff(stock.modified, frappe.utils.now())
		
		return stocks
		
	except Exception as e:
		frappe.log_error(f"search_profile_stocks error: {str(e)}", "Profile Stock Search Error")
		return []
