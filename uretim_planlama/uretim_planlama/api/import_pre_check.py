import frappe
from frappe import _
from frappe.utils import flt
from uretim_planlama.uretim_planlama.utils import get_profile_stock

@frappe.whitelist()
def check_existing_stock_before_import(import_data):
	"""
	Sayım güncellemesi öncesi mevcut stokları kontrol et
	
	Args:
		import_data: [{"item_code": "123", "length": "5.0", "qty": 10}, ...]
	
	Returns:
		{
			"stock_changes": [...],  # Stok değişiklikleri
			"new_items": [...],      # Yeni ürünler
			"no_change": [...],      # Değişiklik olmayan ürünler
			"summary": {...}         # Özet bilgiler
		}
	"""
	try:
		if isinstance(import_data, str):
			import_data = frappe.parse_json(import_data)
		
		stock_changes = []
		new_items = []
		no_change = []
		total_increase_qty = 0
		total_decrease_qty = 0
		total_new_qty = 0
		
		for row in import_data:
			item_code = row.get("item_code")
			length = str(row.get("length", ""))
			qty = flt(row.get("qty", 0))
			
			if not item_code or not length or qty < 0:
				continue
			
			# Mevcut stok kontrolü
			existing_stock = get_profile_stock(item_code, length)
			stock_difference = qty - existing_stock
			
			if existing_stock > 0:
				if stock_difference > 0:
					# Stok artışı
					stock_changes.append({
						"item_code": item_code,
						"length": length,
						"existing_stock": existing_stock,
						"new_stock": qty,
						"difference": stock_difference,
						"change_type": "increase",
						"info": f"📈 Stok artışı: {existing_stock} → {qty} (+{stock_difference})"
					})
					total_increase_qty += stock_difference
				elif stock_difference < 0:
					# Stok azalışı
					stock_changes.append({
						"item_code": item_code,
						"length": length,
						"existing_stock": existing_stock,
						"new_stock": qty,
						"difference": abs(stock_difference),
						"change_type": "decrease",
						"info": f"📉 Stok azalışı: {existing_stock} → {qty} (-{abs(stock_difference)})"
					})
					total_decrease_qty += abs(stock_difference)
				else:
					# Değişiklik yok
					no_change.append({
						"item_code": item_code,
						"length": length,
						"stock": existing_stock,
						"info": "✅ Değişiklik yok"
					})
			else:
				# Yeni ürün
				new_items.append({
					"item_code": item_code,
					"length": length,
					"new_stock": qty,
					"info": "🆕 Yeni ürün"
				})
				total_new_qty += qty
		
		summary = {
			"total_rows": len(import_data),
			"stock_changes_count": len(stock_changes),
			"new_items_count": len(new_items),
			"no_change_count": len(no_change),
			"total_increase_qty": total_increase_qty,
			"total_decrease_qty": total_decrease_qty,
			"total_new_qty": total_new_qty,
			"has_changes": len(stock_changes) > 0
		}
		
		return {
			"stock_changes": stock_changes,
			"new_items": new_items,
			"no_change": no_change,
			"summary": summary,
			"status": "success"
		}
		
	except Exception as e:
		frappe.log_error(f"Import pre-check error: {str(e)}", "Import Pre-check Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_import_summary_report():
	"""Import öncesi özet rapor oluştur"""
	try:
		# Son 30 gün içindeki Profile Entry'leri al
		recent_entries = frappe.get_all(
			"Profile Entry",
			filters={
				"creation": [">=", frappe.utils.add_days(frappe.utils.today(), -30)],
				"docstatus": 1
			},
			fields=["name", "creation", "total_received_qty"],
			order_by="creation desc",
			limit=50
		)
		
		# Son 30 gün içindeki Profile Stock Ledger değişikliklerini al
		recent_ledger_changes = frappe.get_all(
			"Profile Stock Ledger",
			filters={
				"creation": [">=", frappe.utils.add_days(frappe.utils.today(), -30)]
			},
			fields=["item_code", "length", "qty", "creation"],
			order_by="creation desc",
			limit=100
		)
		
		# İstatistikler
		total_recent_entries = len(recent_entries)
		total_recent_qty = sum(flt(entry.total_received_qty) for entry in recent_entries)
		
		return {
			"status": "success",
			"data": {
				"recent_entries": recent_entries[:10],  # Son 10 giriş
				"recent_ledger_changes": recent_ledger_changes[:10],  # Son 10 değişiklik
				"statistics": {
					"total_recent_entries": total_recent_entries,
					"total_recent_qty": total_recent_qty,
					"period": "Son 30 gün"
				}
			}
		}
		
	except Exception as e:
		frappe.log_error(f"Import summary report error: {str(e)}", "Import Summary Error")
		return {
			"status": "error",
			"message": str(e)
		}
