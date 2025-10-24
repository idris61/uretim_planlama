// Item Auto Fill - Ürün Kodu Seçildiğinde Otomatik Doldurma
// Copyright (c) 2025, idris and contributors

/**
 * Ürün kodu seçildiğinde ürün adı ve ürün grubunu otomatik doldurur
 */
window.autoFillItemDetails = function(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    
    if (!row.item_code) {
        // Ürün kodu boşsa, diğer alanları temizle
        frappe.model.set_value(cdt, cdn, 'item_name', '');
        frappe.model.set_value(cdt, cdn, 'item_group', '');
        return;
    }
    
    // Backend'den ürün bilgilerini al
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Item',
            filters: {
                name: row.item_code
            },
            fieldname: ['item_name', 'item_group']
        },
        callback: function(response) {
            if (response.message) {
                const item_data = response.message;
                
                // Ürün adını ve grubunu güncelle
                frappe.model.set_value(cdt, cdn, 'item_name', item_data.item_name || '');
                frappe.model.set_value(cdt, cdn, 'item_group', item_data.item_group || '');
            }
        },
        error: function(error) {
            console.error('Ürün bilgileri alınırken hata:', error);
            frappe.msgprint({
                title: 'Hata',
                message: 'Ürün bilgileri alınırken hata oluştu!',
                indicator: 'red'
            });
        }
    });
};

// =============================================================================
// DOCTYPE EVENT'LERİ - ÜRÜN KODU SEÇİLDİĞİNDE OTOMATİK DOLDURMA
// =============================================================================

// Profile Entry Item
frappe.ui.form.on('Profile Entry Item', {
    item_code: function(frm, cdt, cdn) {
        window.autoFillItemDetails(frm, cdt, cdn);
    }
});

// Profile Exit Item
frappe.ui.form.on('Profile Exit Item', {
    item_code: function(frm, cdt, cdn) {
        window.autoFillItemDetails(frm, cdt, cdn);
    }
});

// Profile Stock Ledger
frappe.ui.form.on('Profile Stock Ledger', {
    item_code: function(frm) {
        if (frm.doc.item_code) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item',
                    filters: {
                        name: frm.doc.item_code
                    },
                    fieldname: ['item_name', 'item_group']
                },
                callback: function(response) {
                    if (response.message) {
                        const item_data = response.message;
                        frm.set_value('item_name', item_data.item_name || '');
                        frm.set_value('item_group', item_data.item_group || '');
                    }
                }
            });
        } else {
            frm.set_value('item_name', '');
            frm.set_value('item_group', '');
        }
    }
});

// Profile Reorder Rule
frappe.ui.form.on('Profile Reorder Rule', {
    item_code: function(frm) {
        if (frm.doc.item_code) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item',
                    filters: {
                        name: frm.doc.item_code
                    },
                    fieldname: ['item_name', 'item_group']
                },
                callback: function(response) {
                    if (response.message) {
                        const item_data = response.message;
                        frm.set_value('item_name', item_data.item_name || '');
                        frm.set_value('item_group', item_data.item_group || '');
                    }
                }
            });
        } else {
            frm.set_value('item_name', '');
            frm.set_value('item_group', '');
        }
    }
});

// Scrap Profile Entry
frappe.ui.form.on('Scrap Profile Entry', {
    item_code: function(frm) {
        if (frm.doc.item_code) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item',
                    filters: {
                        name: frm.doc.item_code
                    },
                    fieldname: ['item_name', 'item_group']
                },
                callback: function(response) {
                    if (response.message) {
                        const item_data = response.message;
                        frm.set_value('item_name', item_data.item_name || '');
                        frm.set_value('item_group', item_data.item_group || '');
                    }
                }
            });
        } else {
            frm.set_value('item_name', '');
            frm.set_value('item_group', '');
        }
    }
});

// Rezerved Raw Materials
frappe.ui.form.on('Rezerved Raw Materials', {
    item_code: function(frm) {
        if (frm.doc.item_code) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item',
                    filters: {
                        name: frm.doc.item_code
                    },
                    fieldname: ['item_name', 'item_group']
                },
                callback: function(response) {
                    if (response.message) {
                        const item_data = response.message;
                        frm.set_value('item_name', item_data.item_name || '');
                        frm.set_value('item_group', item_data.item_group || '');
                    }
                }
            });
        } else {
            frm.set_value('item_name', '');
            frm.set_value('item_group', '');
        }
    }
});

// Accessory Delivery Package Item
frappe.ui.form.on('Accessory Delivery Package Item', {
    item_code: function(frm, cdt, cdn) {
        window.autoFillItemDetails(frm, cdt, cdn);
    }
});

// Long Term Reserve Usage
frappe.ui.form.on('Long Term Reserve Usage', {
    item_code: function(frm) {
        if (frm.doc.item_code) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item',
                    filters: {
                        name: frm.doc.item_code
                    },
                    fieldname: ['item_name', 'item_group']
                },
                callback: function(response) {
                    if (response.message) {
                        const item_data = response.message;
                        frm.set_value('item_name', item_data.item_name || '');
                        frm.set_value('item_group', item_data.item_group || '');
                    }
                }
            });
        } else {
            frm.set_value('item_name', '');
            frm.set_value('item_group', '');
        }
    }
});

// Cutting Plan Row
frappe.ui.form.on('Cutting Plan Row', {
    item_code: function(frm, cdt, cdn) {
        window.autoFillItemDetails(frm, cdt, cdn);
    }
});

// Deleted Long Term Reserve
frappe.ui.form.on('Deleted Long Term Reserve', {
    item_code: function(frm) {
        if (frm.doc.item_code) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item',
                    filters: {
                        name: frm.doc.item_code
                    },
                    fieldname: ['item_name', 'item_group']
                },
                callback: function(response) {
                    if (response.message) {
                        const item_data = response.message;
                        frm.set_value('item_name', item_data.item_name || '');
                        frm.set_value('item_group', item_data.item_group || '');
                    }
                }
            });
        } else {
            frm.set_value('item_name', '');
            frm.set_value('item_group', '');
        }
    }
});

