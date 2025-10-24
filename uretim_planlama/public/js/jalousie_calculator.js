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
 * Jaluzi butonlarını yeşil yapma fonksiyonu
 */
window.forceJalousieButtonsGreen = function() {
    const selectors = [
        'button[data-fieldname="custom_calculate_jalousie_qty"]',
        '.btn[data-fieldname="custom_calculate_jalousie_qty"]',
        '[data-fieldname="custom_calculate_jalousie_qty"] button',
        '[data-fieldname="custom_calculate_jalousie_qty"] .btn',
        '.frappe-control[data-fieldname="custom_calculate_jalousie_qty"] button',
        '.frappe-control[data-fieldname="custom_calculate_jalousie_qty"] .btn',
        'input[data-fieldname="custom_calculate_jalousie_qty"] + button',
        '.form-control[data-fieldname="custom_calculate_jalousie_qty"]'
    ];
    
    let found = false;
    selectors.forEach(selector => {
        const buttons = $(selector);
        if (buttons.length > 0) {
            buttons.each(function() {
                const $btn = $(this);
                $btn.removeAttr('style');
                $btn.css({
                    'background-color': '#28a745 !important',
                    'border-color': '#28a745 !important',
                    'color': 'white !important',
                    'font-weight': 'bold !important',
                    'background': '#28a745 !important',
                    'border': '1px solid #28a745 !important'
                });
                $btn.addClass('btn-success');
                $btn.attr('style', 'background-color: #28a745 !important; border-color: #28a745 !important; color: white !important; font-weight: bold !important;');
            });
            found = true;
        }
    });
    
    return found;
};

// Sayfa yüklendiğinde çalıştır
$(document).ready(function() {
    setTimeout(() => window.forceJalousieButtonsGreen(), 1000);
});

// Eski fonksiyon adı için backward compatibility
window.styleJalousieButtonsGreen = window.forceJalousieButtonsGreen;

// =============================================================================
// TÜM DOCTYPE'LAR İÇİN FORM EVENT'LERİ - TEK DOSYADA
// =============================================================================

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
        setTimeout(() => window.forceJalousieButtonsGreen(), 300);
    }
});

frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        setTimeout(() => window.forceJalousieButtonsGreen(), 500);
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
        setTimeout(() => window.forceJalousieButtonsGreen(), 300);
    }
});

frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        setTimeout(() => window.forceJalousieButtonsGreen(), 500);
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
        setTimeout(() => window.forceJalousieButtonsGreen(), 300);
    }
});

frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        setTimeout(() => window.forceJalousieButtonsGreen(), 500);
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
        setTimeout(() => window.forceJalousieButtonsGreen(), 300);
    }
});

frappe.ui.form.on('Purchase Invoice', {
    refresh: function(frm) {
        setTimeout(() => window.forceJalousieButtonsGreen(), 500);
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
        setTimeout(() => window.forceJalousieButtonsGreen(), 300);
    }
});

frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        setTimeout(() => window.forceJalousieButtonsGreen(), 500);
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
        setTimeout(() => window.forceJalousieButtonsGreen(), 300);
    }
});

frappe.ui.form.on('Material Request', {
    refresh: function(frm) {
        setTimeout(() => window.forceJalousieButtonsGreen(), 500);
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
        setTimeout(() => window.forceJalousieButtonsGreen(), 300);
    }
});

frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        setTimeout(() => window.forceJalousieButtonsGreen(), 500);
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
        setTimeout(() => window.forceJalousieButtonsGreen(), 300);
    }
});

frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
        setTimeout(() => window.forceJalousieButtonsGreen(), 500);
    }
});