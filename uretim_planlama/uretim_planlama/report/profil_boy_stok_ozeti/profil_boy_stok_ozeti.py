import frappe
from frappe import _


def execute(filters=None):
    """
    Profil Boy Stok Özeti raporu.
    Profile Stock Ledger + Profile Entry/Exit + Profile Reorder Rule verilerini
    boy (length) ve profil bazında özetler. ERPNext Stok Özeti benzeri kolonlar üretir.
    """
    filters = filters or {}

    columns = get_columns()
    data, message = get_data(filters)

    return columns, data, None, message


def get_columns():
    return [
        {"label": _("Ürün Kodu"), "fieldname": "profile_type", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": _("Ürün Adı"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Boy (m)"), "fieldname": "length", "fieldtype": "Float", "width": 110},
        {"label": _("Stok Miktarı"), "fieldname": "qty", "fieldtype": "Float", "precision": 3, "width": 120},
        {"label": _("Toplam (mtül)"), "fieldname": "total_length", "fieldtype": "Float", "precision": 3, "width": 120},
        {"label": _("Minimum Stok Miktarı"), "fieldname": "min_qty", "fieldtype": "Float", "width": 150},
        {"label": _("Yeniden Sipariş Miktarı"), "fieldname": "reorder_qty", "fieldtype": "Float", "width": 180},
        {"label": _("Hurda Parça mı?"), "fieldname": "is_scrap_piece", "fieldtype": "Check", "width": 130},
    ]


def get_data(filters):
    where = {}
    if filters.get("profile_type"):
        where["profile_type"] = filters.get("profile_type")
    if filters.get("length"):
        where["length"] = filters.get("length")
    if filters.get("is_scrap_piece") is not None:
        where["is_scrap_piece"] = int(filters.get("is_scrap_piece"))

    # Mevcut stok kayıtlarını al
    stocks = frappe.get_all(
        "Profile Stock Ledger",
        filters=where,
        fields=[
            "profile_type", "length", "qty", "total_length", "is_scrap_piece", "modified"
        ],
        order_by="profile_type, length"
    )

    # Item adları
    item_names = {}
    result = []

    # Reorder kurallarını indeksle: (profile_type, length, warehouse) -> rule
    rules = get_reorder_rules(index=True)

    # Boy eşlemesi: Boy.name -> numeric length, hızlı lookup
    boy_map = get_boy_length_map()

    # Stok kayıtlarını dict'e çevir (hızlı lookup için)
    stock_dict = {}
    for stock in stocks:
        key = (stock.profile_type, float(stock.length), stock.is_scrap_piece)
        stock_dict[key] = stock

    # Sadece stok miktarı > 0 olan kombinasyonları al
    all_combinations = set()
    
    # Mevcut stok kayıtlarından sadece stok miktarı > 0 olanları ekle
    for stock in stocks:
        if stock.qty > 0:  # Sadece stok miktarı > 0 olanları ekle
            key = (stock.profile_type, float(stock.length), stock.is_scrap_piece)
            all_combinations.add(key)

    # Filtre uygula
    filtered_combinations = []
    for combination in all_combinations:
        profile_type, length, is_scrap_piece = combination
        
        # Profil filtresi
        if filters.get("profile_type") and profile_type != filters.get("profile_type"):
            continue
            
        # Boy filtresi (Boy tablosundan length değeri ile eşleştir)
        if filters.get("length"):
            # Boy tablosundan length değerini al
            boy_length = frappe.db.get_value("Boy", filters.get("length"), "length")
            if boy_length and float(boy_length) != length:
                continue
                
        # Hurda parça filtresi
        if filters.get("is_scrap_piece") is not None:
            if is_scrap_piece != int(filters.get("is_scrap_piece")):
                continue
        
        filtered_combinations.append(combination)

    # Sonuçları oluştur
    for combination in filtered_combinations:
        profile_type, length, is_scrap_piece = combination
        
        if profile_type not in item_names:
            item_names[profile_type] = frappe.db.get_value("Item", profile_type, "item_name") or profile_type

        # Stok kaydını al
        stock = stock_dict.get(combination)
        
        # Rule bilgisini al
        rule = rules.get((profile_type, length))
        
        min_qty = (rule or {}).get("min_qty") or 0
        reorder_qty = (rule or {}).get("reorder_qty") or 0

        # Stok bilgileri (stock zaten mevcut çünkü qty > 0 filtresi uygulandı)
        qty = stock.qty
        total_length = stock.total_length

        result.append({
            "profile_type": profile_type,
            "item_name": item_names[profile_type],
            "length": length,
            "qty": qty,
            "total_length": total_length,
            "is_scrap_piece": is_scrap_piece,
            "min_qty": min_qty,
            "reorder_qty": reorder_qty,
        })

    # Sonuçları sırala
    result.sort(key=lambda x: (x["profile_type"], x["length"], x["is_scrap_piece"]))

    message = None
    if not result:
        message = _("Kayıt bulunamadı.")

    return result, message


def get_reorder_rules(index=False):
    rules = frappe.get_all(
        "Profile Reorder Rule",
        filters={"active": 1},
        fields=[
            "profile_type", "length", "min_qty", "reorder_qty"
        ]
    )
    if not index:
        return rules
    # Boy name -> numeric length map
    boy_map = get_boy_length_map()
    indexed = {}
    for r in rules:
        boy_len_str = boy_map.get(r.length)
        try:
            boy_len = float(boy_len_str) if boy_len_str is not None else None
        except Exception:
            boy_len = None
        if boy_len is None:
            # Boy bulunamazsa bu kuralı atla
            continue
        key = (r.profile_type, boy_len)
        indexed[key] = r
    return indexed


def get_boy_length_map():
    """Boy.name -> Boy.length (string) haritası"""
    boys = frappe.get_all("Boy", fields=["name", "length"], limit_page_length=10000)
    return {b.name: b.length for b in boys}


