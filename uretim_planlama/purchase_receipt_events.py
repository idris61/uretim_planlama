import frappe
from uretim_planlama.uretim_planlama.utils import normalize_profile_length, normalize_profile_quantity, get_or_create_boy_record

def validate(doc, method=None):
    """
    Purchase Receipt validate sırasında, Purchase Order'dan 
    custom_material_request_references field'ını kopyala
    """
    copy_material_request_references_from_po(doc)


def on_submit(doc, method=None):
    """Purchase Receipt on_submit event handler for profile items and material request status update"""
    
    # Material Request statuslerini güncelle (birleştirilmiş MR'lar için)
    update_material_request_statuses(doc)
    
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


def copy_material_request_references_from_po(doc):
    """
    Purchase Order'dan Purchase Receipt oluşturulurken
    custom_material_request_references field'ını kopyala
    
    Args:
        doc: Purchase Receipt document
    """
    if not doc.items:
        return
    
    for pr_item in doc.items:
        # Eğer Purchase Order Item referansı varsa
        po_detail = getattr(pr_item, "purchase_order_item", None)
        if not po_detail:
            continue
        
        # Purchase Order Item'dan custom_material_request_references'ı al
        po_item_data = frappe.db.get_value(
            "Purchase Order Item",
            po_detail,
            ["custom_material_request_references"],
            as_dict=1
        )
        
        if po_item_data and po_item_data.custom_material_request_references:
            # PR Item'a kopyala
            pr_item.custom_material_request_references = po_item_data.custom_material_request_references


def update_material_request_statuses(doc):
    """
    Purchase Receipt Item'larındaki Material Request referanslarını bulup
    MR statuslerini 'Received' olarak günceller
    
    Args:
        doc: Purchase Receipt document
    """
    if not doc.items:
        return
    
    # MR'leri topla: {mr_name: True}
    mr_names = set()
    
    for pr_item in doc.items:
        # Custom text field'dan MR referanslarını al
        mr_references_str = getattr(pr_item, "custom_material_request_references", "") or ""
        
        # Önce custom field'ı kontrol et
        if mr_references_str and mr_references_str.strip():
            # Virgülle ayrılmış string'i listeye çevir
            mr_list = [x.strip() for x in mr_references_str.split(",") if x.strip()]
            
            # Her MR'i ekle
            for mr_name in mr_list:
                if mr_name:
                    mr_names.add(mr_name)
        
        # Custom field boşsa, standart material_request field'ına bak
        else:
            old_mr = getattr(pr_item, "material_request", None)
            if old_mr:
                mr_names.add(old_mr)
    
    # Hiç MR referansı yoksa çık
    if not mr_names:
        return
    
    # Her MR için status güncelle
    updated_mrs = []
    failed_mrs = []
    
    for mr_name in mr_names:
        try:
            # MR'nin mevcut durumunu kontrol et
            mr_doc = frappe.get_doc("Material Request", mr_name)
            
            # Sadece submit edilmiş Purchase tipindeki MR'leri güncelle
            if mr_doc.docstatus != 1:
                continue
            
            if mr_doc.material_request_type != "Purchase":
                # Sadece Purchase tipindeki MR'leri işle
                continue
            
            # Tüm items'ların received_qty'sini stock_qty'ye eşitle (100% received)
            frappe.db.sql("""
                UPDATE `tabMaterial Request Item`
                SET received_qty = stock_qty,
                    ordered_qty = stock_qty
                WHERE parent = %s
            """, (mr_name,))
            
            # per_received yüzdesini hesapla ve güncelle
            frappe.db.sql("""
                UPDATE `tabMaterial Request` mr
                SET per_received = 100,
                    per_ordered = 100,
                    modified = NOW()
                WHERE name = %s
            """, (mr_name,))
            
            # MR'yi reload et
            mr_doc.reload()
            
            # Status'ü "Received" yap
            frappe.db.sql("""
                UPDATE `tabMaterial Request`
                SET status = 'Received', modified = NOW()
                WHERE name = %s AND docstatus = 1
            """, (mr_name,))
            
            frappe.db.commit()
            
            updated_mrs.append(f"{mr_name} (Received)")
            
        except Exception as e:
            # Hata durumunda log'a yaz ama işlemi durdurma
            failed_mrs.append(mr_name)
            frappe.log_error(
                f"Material Request {mr_name} status güncellenirken hata oluştu: {str(e)}\n\n{frappe.get_traceback()}",
                "Purchase Receipt MR Status Update Error"
            )
    
    # Özet mesajı
    if updated_mrs:
        frappe.msgprint(
            f"Material Request statusleri güncellendi (Received): {', '.join(updated_mrs)}",
            indicator="green"
        )
    
    if failed_mrs:
        frappe.msgprint(
            f"Bazı Material Request'ler güncellenemedi: {', '.join(failed_mrs)}. Detaylar için Error Log kontrol edin.",
            indicator="red"
        )