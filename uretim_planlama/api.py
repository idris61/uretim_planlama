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

@frappe.whitelist()
def get_materials_by_opti(opti_no):
    """
    Girdi: Production Plan'ın name (docname) değeri
    Çıktı: Üretim planı, bağlı satış siparişleri, malzeme listesi (MLY entegrasyonu için placeholder)
    """
    plan = frappe.get_doc("Production Plan", opti_no)
    if not plan:
        frappe.throw(_("Production Plan not found for OpTi No: {0}").format(opti_no))
    # Child table'dan sales_orders listesini çek
    sales_orders = [row.sales_order for row in plan.sales_orders if row.sales_order]
    # Placeholder: Fetch MLY file materials (to be implemented)
    materials = []  # Bu kısım API ile doldurulacak
    return {
        "production_plan": plan.name,
        "sales_orders": sales_orders,
        "materials": materials
    }

@frappe.whitelist()
def create_delivery_package(data):
    """
    Create Accessory Delivery Package with given data (materials, opti_no, delivered_to, notes, etc).
    """
    import json
    if isinstance(data, str):
        data = json.loads(data)
    doc = frappe.new_doc("Accessory Delivery Package")
    doc.opti_no = data.get("opti_no")
    doc.sales_order = data.get("sales_order")
    doc.delivered_to = data.get("delivered_to")
    doc.delivered_by = frappe.session.user
    doc.delivery_date = frappe.utils.now_datetime()
    doc.notes = data.get("notes")
    for item in data.get("item_list", []):
        doc.append("item_list", {
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name"),
            "qty": item.get("qty"),
            "uom": item.get("uom")
        })
    doc.save()
    frappe.db.commit()
    return {"name": doc.name} 

@frappe.whitelist()
def get_approved_opti_nos():
    """
    Onaylı üretim planlarının hem OpTi No (custom_opti_no) hem de name (docname) değerlerini döndürür.
    """
    return frappe.get_all(
        "Production Plan",
        filters={"docstatus": 1},
        fields=["name", "custom_opti_no"],
        order_by="creation desc"
    )

@frappe.whitelist()
def get_sales_orders_by_opti(opti_no):
    """
    Seçilen OpTi No'ya (Production Plan'ın name'i) ait satış siparişlerini, sales_orders child table'ından döndürür.
    """
    plan = frappe.get_doc("Production Plan", opti_no)
    if not plan:
        return []
    sales_orders = [row.sales_order for row in plan.sales_orders if row.sales_order]
    return sales_orders 