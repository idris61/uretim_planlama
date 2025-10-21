// Jalousie Miktar Hesaplama - Tüm DocType'lar İçin Tek Dosya
// Copyright (c) 2025, idris and contributors

/**
 * Jalousie miktar hesaplama ana fonksiyonu
 * Tüm DocType'larda kullanılabilir
 */
window.calculateJalousieQty = function(frm, cdt, cdn) {
    const row = locals[cdt][cdn];

    if (!row.custom_is_jalousie) {
        frappe.msgprint({
            title: 'Uyarı',
            message: 'Önce "Jaluzi mi?" alanını işaretleyin!',
            indicator: 'orange'
        });
        return;
    }

    if (!row.custom_jalousie_width || !row.custom_jalousie_height) {
        frappe.msgprint({
            title: 'Uyarı',
            message: 'En ve Boy alanları gereklidir!',
            indicator: 'orange'
        });
        return;
    }

    frappe.call({
        method: 'uretim_planlama.uretim_planlama.api.jalousie_calculator.calculate_jalousie_quantity',
        args: {
            width: row.custom_jalousie_width,
            height: row.custom_jalousie_height,
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
            frappe.model.set_value(cdt, cdn, 'qty', result.qty).then(() => {
                frappe.model.set_value(cdt, cdn, 'stock_qty', result.stock_qty);
                frappe.show_alert({
                    message: `✅ ${result.calculation}`,
                    indicator: 'green'
                });
                frm.refresh_field('items');
            });
        },
        error: function(error) {
            frappe.msgprint({
                title: 'API Hatası',
                message: 'Hesaplama sırasında hata oluştu!',
                indicator: 'red'
            });
            console.error('Jalousie calculation API error:', error);
        }
    });
};

/**
 * Jaluzi hesaplama butonlarını stillendirir
 */
window.styleJalousieButtons = function() {
    const tryStyleButtons = () => {
        const selectors = [
            'button[data-fieldname="custom_calculate_jalousie_qty"]',
            'button[data-fieldname*="calculate_jalousie"]',
            '.btn[data-fieldname="custom_calculate_jalousie_qty"]',
            'input[data-fieldname="custom_calculate_jalousie_qty"]'
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
            buttons.each(function() {
                $(this).css({
                    'background-color': '#28a745 !important',
                    'border-color': '#28a745 !important',
                    'color': 'white !important',
                    'font-weight': 'bold',
                    'border-radius': '4px',
                    'padding': '5px 12px'
                });
            });
            
            // Hover efekti
            buttons.hover(
                function() { 
                    $(this).css('background-color', '#218838 !important'); 
                },
                function() { 
                    $(this).css('background-color', '#28a745 !important'); 
                }
            );
            
            // Class ekle (daha kalıcı olması için)
            buttons.addClass('btn btn-success');
            
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
    custom_calculate_jalousie_qty: function(frm, cdt, cdn) {
        window.calculateJalousieQty(frm, cdt, cdn);
    },
    custom_is_jalousie: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.custom_is_jalousie) {
            frappe.model.set_value(cdt, cdn, 'custom_is_profile', 0);
        }
        frm.refresh_field('items');
    }
});

frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        window.styleJalousieButtons();
    }
});

// Delivery Note
frappe.ui.form.on('Delivery Note Item', {
    custom_calculate_jalousie_qty: function(frm, cdt, cdn) {
        window.calculateJalousieQty(frm, cdt, cdn);
    },
    custom_is_jalousie: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.custom_is_jalousie) {
            frappe.model.set_value(cdt, cdn, 'custom_is_profile', 0);
        }
        frm.refresh_field('items');
    }
});

frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        window.styleJalousieButtons();
    }
});

// Sales Invoice
frappe.ui.form.on('Sales Invoice Item', {
    custom_calculate_jalousie_qty: function(frm, cdt, cdn) {
        window.calculateJalousieQty(frm, cdt, cdn);
    },
    custom_is_jalousie: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.custom_is_jalousie) {
            frappe.model.set_value(cdt, cdn, 'custom_is_profile', 0);
        }
        frm.refresh_field('items');
    }
});

frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        window.styleJalousieButtons();
    }
});

// Purchase Invoice
frappe.ui.form.on('Purchase Invoice Item', {
    custom_calculate_jalousie_qty: function(frm, cdt, cdn) {
        window.calculateJalousieQty(frm, cdt, cdn);
    },
    custom_is_jalousie: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.custom_is_jalousie) {
            frappe.model.set_value(cdt, cdn, 'custom_is_profile', 0);
        }
        frm.refresh_field('items');
    }
});

frappe.ui.form.on('Purchase Invoice', {
    refresh: function(frm) {
        window.styleJalousieButtons();
    }
});

// Stock Entry
frappe.ui.form.on('Stock Entry Detail', {
    custom_calculate_jalousie_qty: function(frm, cdt, cdn) {
        window.calculateJalousieQty(frm, cdt, cdn);
    },
    custom_is_jalousie: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.custom_is_jalousie) {
            frappe.model.set_value(cdt, cdn, 'custom_is_profile', 0);
        }
        frm.refresh_field('items');
    }
});

frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        window.styleJalousieButtons();
    }
});

// Material Request
frappe.ui.form.on('Material Request Item', {
    custom_calculate_jalousie_qty: function(frm, cdt, cdn) {
        window.calculateJalousieQty(frm, cdt, cdn);
    },
    custom_is_jalousie: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.custom_is_jalousie) {
            frappe.model.set_value(cdt, cdn, 'custom_is_profile', 0);
        }
        frm.refresh_field('items');
    }
});

frappe.ui.form.on('Material Request', {
    refresh: function(frm) {
        window.styleJalousieButtons();
    }
});

// Sales Order
frappe.ui.form.on('Sales Order Item', {
    custom_calculate_jalousie_qty: function(frm, cdt, cdn) {
        window.calculateJalousieQty(frm, cdt, cdn);
    },
    custom_is_jalousie: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.custom_is_jalousie) {
            frappe.model.set_value(cdt, cdn, 'custom_is_profile', 0);
        }
        frm.refresh_field('items');
    }
});

frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        window.styleJalousieButtons();
    }
});

// Purchase Order
frappe.ui.form.on('Purchase Order Item', {
    custom_calculate_jalousie_qty: function(frm, cdt, cdn) {
        window.calculateJalousieQty(frm, cdt, cdn);
    },
    custom_is_jalousie: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.custom_is_jalousie) {
            frappe.model.set_value(cdt, cdn, 'custom_is_profile', 0);
        }
        frm.refresh_field('items');
    }
});

frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
        window.styleJalousieButtons();
    }
});