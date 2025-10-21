"""
Jaluzi Miktar Hesaplama API
En x Boy = Miktar (m²)
"""

import frappe
from frappe import _


@frappe.whitelist()
def calculate_jalousie_quantity(width, height, conversion_factor=1.0):
	"""
	Jaluzi miktarını hesaplar (En x Boy)
	
	Args:
		width: Jaluzi eni (metre)
		height: Jaluzi boyu (metre)
		conversion_factor: UOM çevrim faktörü
	
	Returns:
		dict: qty, stock_qty ve hesaplama açıklaması
	"""
	try:
		# Validasyonlar
		if not width or not height:
			return {"error": _("Width and Height are required!")}
		
		width_float = float(width)
		height_float = float(height)
		cf = float(conversion_factor or 1.0)
		
		if width_float <= 0 or height_float <= 0:
			return {"error": _("Width and Height must be positive!")}
		
		# Alan hesaplama (m²)
		area = width_float * height_float
		
		# qty ve stock_qty hesaplama
		qty = area  # UOM biriminde miktar
		stock_qty = qty * cf  # Stok biriminde miktar
		
		return {
			"qty": round(qty, 3),
			"stock_qty": round(stock_qty, 3),
			"calculation": f"{width_float}m x {height_float}m = {round(area, 3)} m²"
		}
		
	except (ValueError, TypeError) as e:
		frappe.log_error(f"Jalousie calculation error: {str(e)}", "Jalousie Calculator Error")
		return {"error": _("Invalid width or height value!")}




