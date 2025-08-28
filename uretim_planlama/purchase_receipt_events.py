import frappe
from .utils import normalize_profile_length, normalize_profile_quantity

def on_submit(doc, method=None):
    """Purchase Receipt on_submit event handler for profile items"""
    
    for item in doc.items:
        # Profil ürünü kontrolü
        if not getattr(item, "custom_is_profile", 0):
            continue
            
        # Boy ve adet kontrolü
        length = getattr(item, "custom_profile_length_m", None)
        qty = getattr(item, "custom_profile_length_qty", None)
        
        # Ortak fonksiyonla normalize et
        length = normalize_profile_length(length)
        qty = normalize_profile_quantity(qty)
        
        if not length or not qty or float(qty) < 1:
            continue
            
        # Boy kaydını bul veya oluştur
        try:
            # Boy kaydını lenght field'ına göre ara
            boy_records = frappe.get_list("Boy", filters={"lenght": length.replace('.', ',')}, fields=["name"])
            
            if boy_records:
                boy_name = boy_records[0].name
            else:
                # Yeni Boy kaydı oluştur (virgüllü olarak)
                boy_doc = frappe.get_doc({
                    "doctype": "Boy",
                    "lenght": length.replace('.', ',')
                })
                boy_doc.insert()
                boy_name = boy_doc.name
                
        except Exception as e:
            frappe.log_error(f"Boy kaydı oluşturulamadı: {str(e)}", "Purchase Receipt Boy Error")
            continue
            
        try:
            # Profile Entry oluştur
            profile_entry = frappe.get_doc({
                "doctype": "Profile Entry",
                "date": doc.posting_date,
                "supplier": doc.supplier,
                "warehouse": item.warehouse,
                "remarks": f"Purchase Receipt: {doc.name}",
                "items": [{
                    "item_code": item.item_code,
                    "length": boy_name,
                    "received_quantity": int(qty),
                    "total_length": float(length) * float(qty),
                    "purchase_receipt": doc.name
                }]
            })
            
            profile_entry.insert()
            profile_entry.submit()
            
        except Exception as e:
            frappe.log_error(f"Profile Entry oluşturulurken hata: {str(e)}", "Purchase Receipt Profile Error") 