import frappe
from uretim_planlama.uretim_planlama.utils import normalize_profile_length, normalize_profile_quantity, get_or_create_boy_record

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
            
        # Boy kaydını bul veya oluştur (duplicate önleyici)
        boy_name = get_or_create_boy_record(length)
        if not boy_name:
            frappe.log_error(f"Boy kaydı bulunamadı/oluşturulamadı: {length}", "Purchase Receipt Boy Error")
            continue
            
        try:
            # Item bilgilerini al
            item_data = frappe.db.get_value("Item", item.item_code, 
                                          ["item_name", "item_group"], as_dict=True)
            
            # Profile Entry oluştur
            profile_entry = frappe.get_doc({
                "doctype": "Profile Entry",
                "date": doc.posting_date,
                "supplier": doc.supplier,
                "warehouse": item.warehouse,
                "remarks": f"Purchase Receipt: {doc.name}",
                "items": [{
                    "item_code": item.item_code,
                    "item_name": item_data.item_name if item_data else "",
                    "item_group": item_data.item_group if item_data else "",
                    "length": boy_name,
                    "received_quantity": int(qty),
                    "total_length": float(length) * float(qty),
                    "purchase_receipt": doc.name
                }]
            })

            # PR kaynaklı olduğu için grup kontrolünü atla
            profile_entry.flags.bypass_group_check = True
            
            profile_entry.insert()
            profile_entry.submit()
            
        except Exception as e:
            frappe.log_error(f"Profile Entry oluşturulurken hata: {str(e)}", "Purchase Receipt Profile Error") 