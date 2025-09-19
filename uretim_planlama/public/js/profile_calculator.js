// Profil Miktar Hesaplama - Tüm DocType'lar İçin Tek Dosya
// Copyright (c) 2025, idris and contributors

console.log('Profile Calculator JS V6 yüklendi - Tek Dosya Yapısı');

/**
 * Profil miktar hesaplama ana fonksiyonu
 * Tüm DocType'larda kullanılabilir
 */
window.calculateProfileQty = function(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    
    // Validasyonlar
    if (!row.custom_is_profile) {
        frappe.msgprint({
            title: 'Uyarı',
            message: 'Önce "Profil mi?" alanını işaretleyin!',
            indicator: 'orange'
        });
        return;
    }
    
    if (!row.custom_profile_length_m) {
        frappe.msgprint({
            title: 'Uyarı', 
            message: 'Profil Boyu (m) seçin!',
            indicator: 'orange'
        });
        return;
    }
    
    if (!row.custom_profile_length_qty || row.custom_profile_length_qty <= 0) {
        frappe.msgprint({
            title: 'Uyarı',
            message: 'Profil Boyu Adedi girin!',
            indicator: 'orange'
        });
        return;
    }
    
    // Backend API çağrısı
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.api.profile_calculator.calculate_profile_quantity',
        args: {
            boy_name: row.custom_profile_length_m,
            profile_qty: row.custom_profile_length_qty,
            conversion_factor: row.conversion_factor || 1.0
        },
        callback: function(response) {
            if (response.message.error) {
                frappe.msgprint({
                    title: 'Hata',
                    message: response.message.error,
                    indicator: 'red'
                });
                return;
            }
            
            const result = response.message;
            
            // Değerleri güncelle
            frappe.model.set_value(cdt, cdn, 'qty', result.qty).then(() => {
                frappe.model.set_value(cdt, cdn, 'stock_qty', result.stock_qty);
                
                // Başarı mesajı
                frappe.show_alert({
                    message: `✅ ${result.calculation}`,
                    indicator: 'green'
                });
                
                // Form'u yenile
                frm.refresh_field('items');
            });
        },
        error: function(error) {
            frappe.msgprint({
                title: 'API Hatası',
                message: 'Hesaplama sırasında hata oluştu!',
                indicator: 'red'
            });
            console.error('Profile calculation API error:', error);
        }
    });
};

/**
 * Profil hesaplama butonlarını stillendirir
 */
window.styleProfileButtons = function() {
    // Birden fazla selector dene ve timing artır
    const tryStyleButtons = () => {
        const selectors = [
            'button[data-fieldname="custom_calculate_profile_qty"]',
            'button[data-fieldname*="calculate_profile"]',
            '.btn[data-fieldname="custom_calculate_profile_qty"]',
            'input[data-fieldname="custom_calculate_profile_qty"]'
        ];
        
        let buttons = $();
        for (const selector of selectors) {
            const found = $(selector);
            if (found.length > 0) {
                buttons = found;
                break;
            }
        }
        
        if (buttons.length > 0) {
            buttons.css({
                'background-color': '#dc3545',
                'border-color': '#dc3545', 
                'color': 'white',
                'font-weight': 'bold',
                'border-radius': '4px'
            });
            
            // Hover efekti
            buttons.hover(
                function() { 
                    $(this).css('background-color', '#c82333'); 
                },
                function() { 
                    $(this).css('background-color', '#dc3545'); 
                }
            );
            
            console.log(`✅ Profil butonları stillendirildi: ${buttons.length} buton`);
            return true;
        }
        return false;
    };
    
    // İlk deneme
    if (!tryStyleButtons()) {
        // 1 saniye sonra tekrar dene
        setTimeout(() => {
            if (!tryStyleButtons()) {
                // 2 saniye sonra son deneme
                setTimeout(tryStyleButtons, 2000);
            }
        }, 1000);
    }
};

// =============================================================================
// TÜM DOCTYPE'LAR İÇİN FORM EVENT'LERİ - TEK DOSYADA
// =============================================================================

// Purchase Receipt
frappe.ui.form.on('Purchase Receipt Item', {
    custom_calculate_profile_qty: function(frm, cdt, cdn) {
        window.calculateProfileQty(frm, cdt, cdn);
    }
});

frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        window.styleProfileButtons();
    }
});

// Delivery Note
frappe.ui.form.on('Delivery Note Item', {
    custom_calculate_profile_qty: function(frm, cdt, cdn) {
        window.calculateProfileQty(frm, cdt, cdn);
    }
});

frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        window.styleProfileButtons();
    }
});

// Sales Invoice
frappe.ui.form.on('Sales Invoice Item', {
    custom_calculate_profile_qty: function(frm, cdt, cdn) {
        window.calculateProfileQty(frm, cdt, cdn);
    }
});

frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        window.styleProfileButtons();
    }
});

// Purchase Invoice
frappe.ui.form.on('Purchase Invoice Item', {
    custom_calculate_profile_qty: function(frm, cdt, cdn) {
        window.calculateProfileQty(frm, cdt, cdn);
    }
});

frappe.ui.form.on('Purchase Invoice', {
    refresh: function(frm) {
        window.styleProfileButtons();
    }
});

// Stock Entry
frappe.ui.form.on('Stock Entry Detail', {
    custom_calculate_profile_qty: function(frm, cdt, cdn) {
        window.calculateProfileQty(frm, cdt, cdn);
    }
});

frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        window.styleProfileButtons();
    }
});

// Material Request
frappe.ui.form.on('Material Request Item', {
    custom_calculate_profile_qty: function(frm, cdt, cdn) {
        window.calculateProfileQty(frm, cdt, cdn);
    }
});

frappe.ui.form.on('Material Request', {
    refresh: function(frm) {
        window.styleProfileButtons();
    }
});

// Sales Order
frappe.ui.form.on('Sales Order Item', {
    custom_calculate_profile_qty: function(frm, cdt, cdn) {
        window.calculateProfileQty(frm, cdt, cdn);
    }
});

frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        window.styleProfileButtons();
    }
});

// Purchase Order
frappe.ui.form.on('Purchase Order Item', {
    custom_calculate_profile_qty: function(frm, cdt, cdn) {
        window.calculateProfileQty(frm, cdt, cdn);
    }
});

frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
        window.styleProfileButtons();
    }
});
