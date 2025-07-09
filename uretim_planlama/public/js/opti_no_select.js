// Aksesuar Teslimat Paketi Doctype'ında opti_no alanını dinamik doldurmak için JS
// Bu dosya, sadece Accessory Delivery Package formunda çalışacak şekilde tasarlanmıştır.

frappe.ui.form.on('Accessory Delivery Package', {
    refresh: function(frm) {
        // Yeni belge ise (daha kaydedilmemişse) kullanıcıya uyarı göster
        if (frm.is_new()) {
            frappe.msgprint({
                title: 'Bilgi',
                message: 'Bu uyarı koddan otomatik olarak gösterildi. JS entegrasyonu çalışıyor!',
                indicator: 'blue'
            });
        }
        // opti_no alanı select ise, değerleri dinamik doldur
        if (frm.fields_dict.opti_no && frm.fields_dict.opti_no.df.fieldtype === 'Select') {
            // Önce mevcut seçenekleri temizle
            frm.set_df_property('opti_no', 'options', []);
            // Sunucudan onaylanmış üretim planlarını çek
            frappe.call({
                method: 'uretim_planlama.uretim_planlama.api.get_approved_opti_nos',
                callback: function(r) {
                    let options = ['']; // Boş seçenek ("Seçiniz")
                    (r.message || []).forEach(function(row) {
                        if (row.custom_opti_no) {
                            // custom_opti_no gösterilecek, value olarak name kullanılacak
                            options.push({
                                label: row.custom_opti_no,
                                value: row.name
                            });
                        }
                    });
                    frm.set_df_property('opti_no', 'options', options);
                }
            });
        }
    }
}); 