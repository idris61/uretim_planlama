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
		{"label": _("Ürün Kodu"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": _("Ürün Grubu"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 150},
        {"label": _("Boy (m)"), "fieldname": "length", "fieldtype": "Float", "width": 110},
        {"label": _("Stok Miktarı"), "fieldname": "qty", "fieldtype": "Float", "precision": 3, "width": 120},
        {"label": _("Toplam (mtül)"), "fieldname": "total_length", "fieldtype": "Float", "precision": 3, "width": 120},
        {"label": _("Minimum Stok Miktarı"), "fieldname": "min_qty", "fieldtype": "Float", "width": 150},
        {"label": _("Yeniden Sipariş Miktarı"), "fieldname": "reorder_qty", "fieldtype": "Float", "width": 180},
        {"label": _("Parça Profil mi?"), "fieldname": "is_scrap_piece", "fieldtype": "Check", "width": 130},
    ]


def get_data(filters):
    where = {}
    if filters.get("item_code"):
        where["item_code"] = filters.get("item_code")
    
    if filters.get("item_group"):
        where["item_group"] = filters.get("item_group")
    
    # Sadece profil ürünlerini göster
    from uretim_planlama.uretim_planlama.utils import get_allowed_profile_groups
    allowed_groups = get_allowed_profile_groups()
    # length özel işlenir: Boy adı ya da sayısal değer gelebilir
    input_length_value = None
    if filters.get("length"):
        boy_length_str = frappe.db.get_value("Boy", filters.get("length"), "length")
        if boy_length_str is not None:
            try:
                input_length_value = float(boy_length_str)
            except Exception:
                input_length_value = None
        if input_length_value is None:
            # Doğrudan sayısal girilmiş olabilir (","/"." toleransı ile)
            raw = str(filters.get("length")).replace(",", ".")
            try:
                input_length_value = float(raw)
            except Exception:
                input_length_value = None
    if filters.get("is_scrap_piece") is not None:
        where["is_scrap_piece"] = int(filters.get("is_scrap_piece"))

    # Mevcut stok kayıtlarını al - sadece profil ürünleri
    # qty > 0 koşulunu doğrudan sorguda uygula (sıfır stokları hiç getirme)
    filters_list = []
    for key, value in where.items():
        filters_list.append(["Profile Stock Ledger", key, "=", value])
    if input_length_value is not None:
        filters_list.append(["Profile Stock Ledger", "length", "=", input_length_value])
    filters_list.append(["Profile Stock Ledger", "qty", ">", 0])

    # Filtreleri SQL'e ekle
    sql_filters = {
        'allowed_groups': tuple(allowed_groups)
    }
    where_conditions = ["psl.qty > 0", "i.item_group IN %(allowed_groups)s"]
    
    if filters.get("item_code"):
        where_conditions.append("psl.item_code = %(item_code)s")
        sql_filters['item_code'] = filters.get("item_code")
    
    if filters.get("item_group"):
        where_conditions.append("i.item_group = %(item_group)s")
        sql_filters['item_group'] = filters.get("item_group")
    
    if input_length_value is not None:
        where_conditions.append("psl.length = %(length)s")
        sql_filters['length'] = input_length_value
    
    # Sadece profil ürünlerini al
    stocks = frappe.db.sql(f"""
        SELECT psl.item_code, psl.length, psl.qty, psl.total_length, psl.is_scrap_piece, psl.modified, i.item_group
        FROM `tabProfile Stock Ledger` psl
        INNER JOIN `tabItem` i ON psl.item_code = i.name
        WHERE {' AND '.join(where_conditions)}
        ORDER BY psl.item_code, psl.length
    """, sql_filters, as_dict=True)

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
        key = (stock.item_code, float(stock.length), stock.is_scrap_piece)
        stock_dict[key] = stock

    # Sadece stok miktarı > 0 olan kombinasyonları al
    all_combinations = set()
    for stock in stocks:
        key = (stock.item_code, float(stock.length), stock.is_scrap_piece)
        all_combinations.add(key)

    # Filtre uygula
    filtered_combinations = []
    for combination in all_combinations:
        profile_type, length, is_scrap_piece = combination
        
        # Profil filtresi
        if filters.get("item_code") and profile_type != filters.get("item_code"):
            continue
            
        # Boy filtresi (Boy tablosundan length değeri ile eşleştir)
        if input_length_value is not None:
            if float(length) != float(input_length_value):
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
            "item_code": profile_type,
            "item_group": stock.item_group,
            "length": length,
            "qty": qty,
            "total_length": total_length,
            "is_scrap_piece": is_scrap_piece,
            "min_qty": min_qty,
            "reorder_qty": reorder_qty,
        })

    # Sonuçları sırala
    result.sort(key=lambda x: (x["item_code"], x["length"], x["is_scrap_piece"]))

    message = None
    if not result:
        message = _("Kayıt bulunamadı.")

    return result, message


def get_reorder_rules(index=False):
    rules = frappe.get_all(
        "Profile Reorder Rule",
        filters={"active": 1},
        fields=[
            "item_code", "length", "min_qty", "reorder_qty"
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
        key = (r.item_code, boy_len)
        indexed[key] = r
    return indexed


def get_boy_length_map():
    """Boy.name -> Boy.length (string) haritası"""
    boys = frappe.get_all("Boy", fields=["name", "length"], limit_page_length=10000)
    return {b.name: b.length for b in boys}


