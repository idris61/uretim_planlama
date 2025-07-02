import frappe
from frappe.utils import getdate, add_days, get_datetime
from datetime import timedelta
from calendar import monthrange
from frappe import _

# Türkçe gün isimleri ve durum haritası
DAY_NAME_TR = {
    'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
    'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'
}
STATUS_MAP = {
    "In Process": "Devam ediyor",
    "Completed": "Tamamlandı",
    "Not Started": "Açık",
    "Açık": "Açık",
    "Devam ediyor": "Devam ediyor",
    "Tamamlandı": "Tamamlandı",
    "İptal Edildi": "İptal Edildi"
}

@frappe.whitelist()
def get_total_stock_summary(profil=None, depo=None):
    """
    ERPNext Bin tablosundan toplam stok (mtül) bilgisini depo ve ürün bazında döndürür.
    Ayrıca, Rezerved Raw Materials doctype'ından toplam rezerv (mtül) ve kullanılabilir (mtül) değerlerini de ekler.
    """
    filters = {}
    if profil:
        filters["item_code"] = profil
    if depo:
        filters["warehouse"] = depo
    bins = frappe.get_all("Bin", filters=filters, fields=["item_code", "warehouse", "actual_qty"])
    # item_name ekle
    item_names = {}
    if bins:
        item_codes = list(set([b["item_code"] for b in bins]))
        for item in frappe.get_all("Item", filters={"item_code": ["in", item_codes]}, fields=["item_code", "item_name"]):
            item_names[item["item_code"]] = item["item_name"]
    # Rezervleri çek (mtül bazında)
    rezervler = frappe.get_all(
        "Rezerved Raw Materials",
        fields=["item_code", "quantity"],
        filters={"item_code": ["in", [b["item_code"] for b in bins]]} if bins else {}
    )
    rezerv_map = {}
    for r in rezervler:
        rezerv_map.setdefault(r["item_code"], 0)
        rezerv_map[r["item_code"]] += float(r["quantity"] or 0)
    result = []
    for b in bins:
        rezerv_mtul = rezerv_map.get(b["item_code"], 0)
        kullanilabilir_mtul = float(b["actual_qty"] or 0) - rezerv_mtul
        result.append({
            "profil": b["item_code"],
            "profil_adi": item_names.get(b["item_code"], ""),
            "depo": b["warehouse"],
            "toplam_stok_mtul": b["actual_qty"],
            "rezerv_mtul": rezerv_mtul,
            "kullanilabilir_mtul": kullanilabilir_mtul
        })
    return result 