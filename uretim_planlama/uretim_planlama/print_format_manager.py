"""
Print Format Manager - Yazdırma Formatı Yönetimi
================================================

Bu dosya tüm yazdırma formatı geliştirmelerini organize eder:
- Custom field'ların print_hide ayarları
- Description güncellemeleri
- Fiyat alanlarının gizlenmesi
- Property setter'lar

Copyright (c) 2025, idris and contributors
"""

import frappe
from frappe import _


class PrintFormatManager:
    """Yazdırma formatı yönetimi için ana sınıf"""
    
    # =============================================================================
    # CUSTOM FIELD PRINT HIDE AYARLARI
    # =============================================================================
    
    @staticmethod
    def get_custom_field_print_settings():
        """
        Custom field'ların print_hide ayarlarını döndürür
        """
        return {
            # Gizlenen alanlar (print_hide: 1)
            "hidden_fields": [
                "custom_is_profile",           # Profil checkbox'ı
                "custom_is_jalousie",          # Jaluzi checkbox'ı
                "custom_calculate_profile_qty", # Profil hesaplama butonu
                "custom_calculate_jalousie_qty", # Jaluzi hesaplama butonu
            ],
            
            # Görünen alanlar (print_hide: 0, print_hide_if_no_value: 1)
            "visible_fields": [
                "custom_profile_length_m",     # Profil Boyu (m)
                "custom_profile_length_qty",   # Profil Boyu Adedi
                "custom_jalousie_width",       # Jaluzi Eni (m)
                "custom_jalousie_height",      # Jaluzi Boyu (m)
            ]
        }
    
    @staticmethod
    def get_price_fields_to_hide():
        """
        İrsaliye çıktılarında gizlenecek fiyat alanları
        """
        return [
            "rate",                           # Birim Fiyat
            "amount",                         # Tutar
            "discount_amount",                # İndirim Tutarı
            "distributed_discount_amount",    # Dağıtılmış İndirim Tutarı
            "rate_and_amount",                # Fiyat ve Tutar
            "stock_uom_rate",                 # Stok Birim Fiyatı
            "base_rate_with_margin",          # Marjlı Fiyat (Şirket Para Birimi)
            "use_serial_batch_fields",        # Seri No / Parti Alanlarını Kullanın
            "grant_commission",               # Komisyona İzin ver
        ]
    
    # =============================================================================
    # DESCRIPTION GÜNCELLEMELERİ
    # =============================================================================
    
    @staticmethod
    def update_item_descriptions_for_print(doc):
        """
        Print format için item description'larına profil ve jaluzi bilgilerini ekler
        """
        if not hasattr(doc, 'items'):
            return
        
        for item in doc.items:
            base_description = item.item_name or item.item_code or ""
            additional_info = []
            
            # Profil bilgisi
            if getattr(item, "custom_is_profile", 0):
                length_m = getattr(item, "custom_profile_length_m", None)
                length_qty = getattr(item, "custom_profile_length_qty", None)
                
                if length_m and length_qty:
                    try:
                        # Boy link field'ından değeri al
                        if isinstance(length_m, str) and frappe.db.exists("Boy", length_m):
                            boy_doc = frappe.get_doc("Boy", length_m)
                            length_value = boy_doc.length
                        else:
                            length_value = length_m
                        
                        additional_info.append(f"Profil: {length_value}m × {int(float(length_qty))} adet")
                    except Exception as e:
                        frappe.log_error(f"Description update error for profile: {str(e)}", "Print Format Utils")
            
            # Jaluzi bilgisi
            elif getattr(item, "custom_is_jalousie", 0):
                width = getattr(item, "custom_jalousie_width", None)
                height = getattr(item, "custom_jalousie_height", None)
                
                if width and height:
                    try:
                        area = float(width) * float(height)
                        additional_info.append(f"Jaluzi: {float(width)}m (En) × {float(height)}m (Boy) = {area:.2f} m²")
                    except Exception as e:
                        frappe.log_error(f"Description update error for jalousie: {str(e)}", "Print Format Utils")
            
            # Description'ı güncelle
            if additional_info:
                # Mevcut description'da profil/jaluzi bilgisi varsa temizle
                if item.description:
                    # Eski profil/jaluzi satırlarını temizle
                    lines = item.description.split('\n')
                    cleaned_lines = [line for line in lines if not (line.startswith('Profil:') or line.startswith('Jaluzi:'))]
                    base_description = '\n'.join(cleaned_lines).strip()
                
                item.description = base_description + '\n' + '\n'.join(additional_info)
    
    # =============================================================================
    # PROPERTY SETTER YÖNETİMİ
    # =============================================================================
    
    @staticmethod
    def hide_price_fields_in_delivery_note():
        """
        Delivery Note'da fiyat alanlarını gizler
        """
        # Item seviyesinde fiyat alanları
        doctype = "Delivery Note Item"
        price_fields = PrintFormatManager.get_price_fields_to_hide()
        
        for field_name in price_fields:
            PrintFormatManager.set_property_setter(
                doctype=doctype,
                fieldname=field_name,
                property="print_hide",
                value="1"
            )
        
        # Belge seviyesinde toplam alanları
        doctype = "Delivery Note"
        total_fields = ["total", "grand_total", "rounded_total", "in_words", "amount_eligible_for_commission"]
        
        for field_name in total_fields:
            PrintFormatManager.set_property_setter(
                doctype=doctype,
                fieldname=field_name,
                property="print_hide",
                value="1"
            )
    
    @staticmethod
    def hide_price_fields_in_purchase_receipt():
        """
        Purchase Receipt'te fiyat alanlarını gizler
        """
        # Item seviyesinde fiyat alanları
        doctype = "Purchase Receipt Item"
        price_fields = PrintFormatManager.get_price_fields_to_hide()
        
        for field_name in price_fields:
            PrintFormatManager.set_property_setter(
                doctype=doctype,
                fieldname=field_name,
                property="print_hide",
                value="1"
            )
        
        # Belge seviyesinde toplam alanları
        doctype = "Purchase Receipt"
        total_fields = ["total", "grand_total", "tax_withholding_net_total", "rounded_total", "in_words"]
        
        for field_name in total_fields:
            PrintFormatManager.set_property_setter(
                doctype=doctype,
                fieldname=field_name,
                property="print_hide",
                value="1"
            )
    
    @staticmethod
    def set_property_setter(doctype, fieldname, property, value):
        """
        Property Setter oluşturur veya günceller
        """
        property_setter_name = f"{doctype}-{fieldname}-{property}"
        
        if frappe.db.exists("Property Setter", property_setter_name):
            # Mevcut property setter'ı güncelle
            frappe.db.set_value("Property Setter", property_setter_name, "value", value)
        else:
            # Yeni property setter oluştur
            doc = frappe.get_doc({
                "doctype": "Property Setter",
                "doctype_or_field": "DocField",
                "doc_type": doctype,
                "field_name": fieldname,
                "property": property,
                "value": value,
                "property_type": "Data"
            })
            doc.insert(ignore_permissions=True)
    
    # =============================================================================
    # YARDIMCI FONKSİYONLAR
    # =============================================================================
    
    @staticmethod
    def get_item_details_for_print(item):
        """
        Item için profil veya jaluzi detaylarını formatlanmış string olarak döndürür
        
        Args:
            item: Item child table row
        
        Returns:
            str: Formatlanmış detay metni veya boş string
        """
        details = []
        
        # Profil kontrolü
        if getattr(item, "custom_is_profile", 0):
            length_m = getattr(item, "custom_profile_length_m", None)
            length_qty = getattr(item, "custom_profile_length_qty", None)
            
            if length_m and length_qty:
                # Boy link field'ından değeri al
                try:
                    if isinstance(length_m, str):
                        # Link field ise Boy doctype'ından length değerini al
                        boy_doc = frappe.get_doc("Boy", length_m)
                        length_value = boy_doc.length
                    else:
                        length_value = length_m
                    
                    details.append(f"<b>Profil:</b> {length_value}m × {int(float(length_qty))} adet")
                except:
                    if length_m and length_qty:
                        details.append(f"<b>Profil:</b> {length_m}m × {int(float(length_qty))} adet")
        
        # Jaluzi kontrolü
        elif getattr(item, "custom_is_jalousie", 0):
            width = getattr(item, "custom_jalousie_width", None)
            height = getattr(item, "custom_jalousie_height", None)
            
            if width and height:
                area = float(width) * float(height)
                details.append(f"<b>Jaluzi:</b> {float(width)}m (En) × {float(height)}m (Boy) = {area:.2f} m²")
        
        return "<br>".join(details) if details else ""
    
    @staticmethod
    @frappe.whitelist()
    def create_material_request_print_format():
        """
        Material Request için özel print format oluşturur
        """
        html_content = """
<div class="print-format">
    <div class="print-heading">
        <h2>{{ doc.title or "Material Request" }}</h2>
        <div class="print-heading-details">
            <div class="row">
                <div class="col-6">
                    <div class="print-heading-field">
                        <label>Document ID:</label>
                        <span>{{ doc.name }}</span>
                    </div>
                </div>
                <div class="col-6">
                    <div class="print-heading-field">
                        <label>Status:</label>
                        <span>{{ doc.status }}</span>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-6">
                    <div class="print-heading-field">
                        <label>Transaction Type:</label>
                        <span>{{ doc.transaction_type }}</span>
                    </div>
                </div>
                <div class="col-6">
                    <div class="print-heading-field">
                        <label>Transaction Date:</label>
                        <span>{{ doc.transaction_date }}</span>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-6">
                    <div class="print-heading-field">
                        <label>Required Date:</label>
                        <span>{{ doc.schedule_date }}</span>
                    </div>
                </div>
                <div class="col-6">
                    <div class="print-heading-field">
                        <label>Price List:</label>
                        <span>{{ doc.price_list or "Default" }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="print-table">
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>No</th>
                    <th>Item Code</th>
                    <th>Required Date</th>
                    <th>Description</th>
                    <th>Profile Length (m)</th>
                    <th>Profile Qty</th>
                    <th>Jalousie Width (m)</th>
                    <th>Jalousie Height (m)</th>
                    <th>Quantity</th>
                    <th>Target Warehouse</th>
                    <th>Unit</th>
                </tr>
            </thead>
            <tbody>
                {% for item in doc.items %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ item.item_code }}</td>
                    <td>{{ item.schedule_date or doc.schedule_date }}</td>
                    <td>{{ item.description or item.item_name }}</td>
                    <td>{{ item.custom_profile_length_m or "" }}</td>
                    <td>{{ item.custom_profile_length_qty or "" }}</td>
                    <td>{{ item.custom_jalousie_width or "" }}</td>
                    <td>{{ item.custom_jalousie_height or "" }}</td>
                    <td>{{ item.qty }}</td>
                    <td>{{ item.warehouse }}</td>
                    <td>{{ item.uom }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
        """
        
        # Print format oluştur veya güncelle
        print_format_name = "Material Request - Custom"
        
        if frappe.db.exists("Print Format", print_format_name):
            # Mevcut print format'ı güncelle
            frappe.db.set_value("Print Format", print_format_name, "html", html_content)
            frappe.db.commit()
            return f"Print format '{print_format_name}' updated successfully"
        else:
            # Yeni print format oluştur
            doc = frappe.get_doc({
                "doctype": "Print Format",
                "name": print_format_name,
                "doc_type": "Material Request",
                "print_format_type": "Jinja",
                "html": html_content,
                "standard": "No"
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            return f"Print format '{print_format_name}' created successfully"
    
    @staticmethod
    @frappe.whitelist()
    def get_print_item_details(doctype, name, item_field="items"):
        """
        Print format'tan çağrılmak üzere tüm item'ların detaylarını döndürür
        
        Args:
            doctype: Ana DocType (örn: Sales Order)
            name: Doküman adı
            item_field: Child table field name (default: items)
        
        Returns:
            dict: {item_name: details_html}
        """
        doc = frappe.get_doc(doctype, name)
        items = getattr(doc, item_field, [])
        
        result = {}
        for item in items:
            details = PrintFormatManager.get_item_details_for_print(item)
            if details:
                result[item.name] = details
        
        return result
    
    # =============================================================================
    # BAŞLATMA VE YÖNETİM FONKSİYONLARI
    # =============================================================================
    
    @staticmethod
    def fix_custom_field_print_settings():
        """
        Custom field'ların print ayarlarını düzeltir
        Tüm DocType'larda profil ve jaluzi field'ları için print ayarlarını yapar
        """
        doctypes = [
            "Material Request Item",
            "Sales Order Item", 
            "Purchase Order Item",
            "Delivery Note Item",
            "Purchase Receipt Item",
            "Sales Invoice Item",
            "Purchase Invoice Item",
            "Stock Entry Detail"
        ]
        
        # Profil alanları için print_hide=0 ayarla
        profile_fields = ["custom_profile_length_m", "custom_profile_length_qty"]
        for doctype in doctypes:
            for field_name in profile_fields:
                PrintFormatManager.set_property_setter(
                    doctype=doctype,
                    fieldname=field_name,
                    property="print_hide",
                    value="0"
                )
                PrintFormatManager.set_property_setter(
                    doctype=doctype,
                    fieldname=field_name,
                    property="print_hide_if_no_value",
                    value="1"
                )
        
        # Jaluzi alanları için print_hide=0 ayarla
        jalousie_fields = ["custom_jalousie_width", "custom_jalousie_height"]
        for doctype in doctypes:
            for field_name in jalousie_fields:
                PrintFormatManager.set_property_setter(
                    doctype=doctype,
                    fieldname=field_name,
                    property="print_hide",
                    value="0"
                )
                PrintFormatManager.set_property_setter(
                    doctype=doctype,
                    fieldname=field_name,
                    property="print_hide_if_no_value",
                    value="1"
                )

    @staticmethod
    def initialize_print_settings():
        """
        Tüm print format ayarlarını başlatır
        """
        try:
            PrintFormatManager.hide_price_fields_in_delivery_note()
            PrintFormatManager.hide_price_fields_in_purchase_receipt()
            PrintFormatManager.fix_custom_field_print_settings()
            frappe.db.commit()
            frappe.msgprint(_("Print format settings initialized successfully!"))
        except Exception as e:
            frappe.log_error(f"Print format initialization error: {str(e)}", "Print Format Manager")
            frappe.msgprint(_("Error initializing print format settings!"))
    
    @staticmethod
    def get_print_format_summary():
        """
        Print format ayarlarının özetini döndürür
        """
        return {
            "custom_fields": PrintFormatManager.get_custom_field_print_settings(),
            "price_fields": PrintFormatManager.get_price_fields_to_hide(),
            "description_update": "Automatic description updates for profile and jalousie items",
            "price_hiding": "Price fields hidden in Delivery Note and Purchase Receipt"
        }


# =============================================================================
# EVENT HOOK'LARI (utils.py'den çağrılır)
# =============================================================================

# before_save hook'u utils.py'de birleştirilmiştir
# PrintFormatManager.update_item_descriptions_for_print() fonksiyonu
# utils.before_save() içinden çağrılır


# =============================================================================
# FRAPPE COMMAND'LARI
# =============================================================================

@frappe.whitelist()
def initialize_print_format_settings():
    """Print format ayarlarını başlatır - bench execute ile çağrılabilir"""
    PrintFormatManager.initialize_print_settings()
    PrintFormatManager.create_material_request_print_format()
    return {"status": "success", "message": "Print format settings initialized"}


@frappe.whitelist()
def get_print_format_info():
    """Print format bilgilerini döndürür"""
    return PrintFormatManager.get_print_format_summary()