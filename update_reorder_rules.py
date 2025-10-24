import frappe

def update_profile_reorder_rules():
    """Profile Reorder Rule kayıtlarındaki item_name ve item_group alanlarını günceller"""
    
    # Tüm Profile Reorder Rule kayıtlarını getir
    rules = frappe.get_all(
        "Profile Reorder Rule",
        fields=["name", "item_code", "item_name", "item_group"]
    )
    
    updated_count = 0
    total_count = len(rules)
    
    print(f"\nToplam {total_count} Profile Reorder Rule kaydı bulundu.")
    print("Güncelleme başlıyor...\n")
    
    for rule in rules:
        try:
            # Eğer item_name veya item_group boşsa güncelle
            if rule.item_code and (not rule.item_name or not rule.item_group):
                # Item bilgilerini getir
                item = frappe.db.get_value(
                    "Item", 
                    rule.item_code, 
                    ["item_name", "item_group"], 
                    as_dict=True
                )
                
                if item:
                    # Direkt SQL ile güncelle
                    frappe.db.set_value(
                        "Profile Reorder Rule",
                        rule.name,
                        {
                            "item_name": item.item_name,
                            "item_group": item.item_group
                        },
                        update_modified=False
                    )
                    updated_count += 1
                    print(f"✓ {rule.name}: {item.item_name} - {item.item_group}")
                else:
                    print(f"✗ {rule.name}: Item {rule.item_code} bulunamadı")
        except Exception as e:
            print(f"✗ {rule.name}: Hata - {str(e)}")
            continue
    
    frappe.db.commit()
    
    print(f"\n{'='*60}")
    print(f"Güncelleme tamamlandı!")
    print(f"Toplam kayıt: {total_count}")
    print(f"Güncellenen: {updated_count}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    update_profile_reorder_rules()


