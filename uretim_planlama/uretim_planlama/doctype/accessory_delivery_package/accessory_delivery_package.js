console.log("Accessory Delivery Package JS loaded!");
// Copyright (c) 2025, idris and contributors
// For license information, please see license.txt

frappe.ui.form.on('Accessory Delivery Package', {
    refresh: function(frm) {
        // opti_no alanı için {label, value} kullanılabilir
        if (frm.fields_dict.opti_no && frm.fields_dict.opti_no.df.fieldtype === 'Select') {
            frm.set_df_property('opti_no', 'options', []);
            frappe.call({
                method: 'uretim_planlama.uretim_planlama.api.get_approved_opti_nos',
                callback: function(r) {
                    let options = [{ label: '', value: '' }];
                    (r.message || []).forEach(function(row) {
                        if (row.custom_opti_no && row.name) {
                            options.push({ label: row.custom_opti_no, value: row.name });
                        }
                    });
                    frm.set_df_property('opti_no', 'options', options);
                    console.log('[DEBUG] opti_no options:', options);
                }
            });
        }

        // sales_order alanı için dinamik filtre (set_query)
        frm.set_query('sales_order', function() {
            if (frm.doc.opti_no) {
                return {
                    filters: [
                        ['name', 'in', frm.sales_orders_for_opti || []]
                    ]
                };
            }
        });
    },
    opti_no: function(frm) {
        console.log('[DEBUG] opti_no seçildi, value:', frm.doc.opti_no);
        // opti_no değişince sales_order alanını temizle
        frm.set_value('sales_order', '');
        // opti_no'ya bağlı sales_order'ları çekip form objesine ata
        if (frm.doc.opti_no) {
            frappe.call({
                method: 'uretim_planlama.uretim_planlama.api.get_sales_orders_by_opti',
                args: { opti_no: frm.doc.opti_no },
                callback: function(r) {
                    frm.sales_orders_for_opti = r.message || [];
                    console.log('[DEBUG] sales_orders_for_opti:', frm.sales_orders_for_opti);
                }
            });
        } else {
            frm.sales_orders_for_opti = [];
        }
    },
    sales_order: function(frm) {
        console.log('[DEBUG] sales_order seçildi, value:', frm.doc.sales_order);
    }
});
