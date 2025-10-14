// Import Öncesi Stok Kontrol Sistemi

frappe.ui.form.on('Data Import', {
    refresh: function(frm) {
        // Import butonu yanına "Stok Kontrolü" butonu ekle
        if (frm.doc.reference_doctype === 'Profile Stock Ledger') {
            frm.add_custom_button(__('Sayım Öncesi Kontrol'), function() {
                check_existing_stock_before_import(frm);
            }, __('Araçlar'));
        }
    }
});

function check_existing_stock_before_import(frm) {
    if (!frm.doc.import_file) {
        frappe.msgprint(__('Önce dosya yükleyiniz.'));
        return;
    }
    
    // Loading göster
    let d = new frappe.ui.Dialog({
        title: __('Sayım Öncesi Stok Kontrolü'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'loading',
                options: `
                    <div class="text-center" style="padding: 20px;">
                        <div class="spinner-border" role="status">
                            <span class="sr-only">Yükleniyor...</span>
                        </div>
                        <p class="mt-2">Stok kontrolü yapılıyor...</p>
                    </div>
                `
            }
        ],
        primary_action_label: __('Kapat'),
        primary_action: function() {
            d.hide();
        }
    });
    d.show();
    
    // CSV dosyasını oku ve analiz et
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'File',
            name: frm.doc.import_file
        },
        callback: function(response) {
            if (response.message) {
                analyze_csv_content(response.message.file_url, d);
            }
        }
    });
}

function analyze_csv_content(file_url, dialog) {
    // CSV içeriğini analiz et (basit örnek)
    frappe.call({
        method: 'uretim_planlama.api.import_pre_check.check_existing_stock_before_import',
        args: {
            import_data: [] // CSV içeriği buraya parse edilecek
        },
        callback: function(response) {
            if (response.message && response.message.status === 'success') {
                show_import_analysis(response.message, dialog);
            } else {
                show_error_message(response.message, dialog);
            }
        }
    });
}

function show_import_analysis(data, dialog) {
    let conflicts_html = '';
    let new_items_html = '';
    
    // Çakışmalar
    if (data.conflicts && data.conflicts.length > 0) {
        conflicts_html = `
            <div class="alert alert-warning">
                <h5>⚠️ Stok Çakışmaları Bulundu (${data.conflicts.length} adet)</h5>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Ürün Kodu</th>
                                <th>Boy</th>
                                <th>Mevcut Stok</th>
                                <th>Import Miktarı</th>
                                <th>Toplam (Sonrası)</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        data.conflicts.forEach(function(conflict) {
            conflicts_html += `
                <tr>
                    <td>${conflict.item_code}</td>
                    <td>${conflict.length}</td>
                    <td>${conflict.existing_stock}</td>
                    <td>${conflict.import_qty}</td>
                    <td><strong>${conflict.total_after_import}</strong></td>
                </tr>
            `;
        });
        
        conflicts_html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    // Yeni ürünler
    if (data.new_items && data.new_items.length > 0) {
        new_items_html = `
            <div class="alert alert-success">
                <h5>✅ Yeni Ürünler (${data.new_items.length} adet)</h5>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Ürün Kodu</th>
                                <th>Boy</th>
                                <th>Import Miktarı</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        data.new_items.forEach(function(item) {
            new_items_html += `
                <tr>
                    <td>${item.item_code}</td>
                    <td>${item.length}</td>
                    <td>${item.import_qty}</td>
                </tr>
            `;
        });
        
        new_items_html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    // Özet
    let summary_html = `
        <div class="alert alert-info">
            <h5>📊 Import Özeti</h5>
            <ul class="mb-0">
                <li>Toplam Kayıt: ${data.summary.total_rows}</li>
                <li>Çakışmalı: ${data.summary.conflict_count}</li>
                <li>Yeni Ürün: ${data.summary.new_count}</li>
                <li>Çakışmalı Miktar: ${data.summary.total_conflict_qty}</li>
                <li>Yeni Miktar: ${data.summary.total_new_qty}</li>
            </ul>
        </div>
    `;
    
    // Dialog içeriğini güncelle
    dialog.fields_dict.loading.$wrapper.html(`
        <div style="padding: 20px;">
            ${summary_html}
            ${conflicts_html}
            ${new_items_html}
            
            ${data.summary.has_conflicts ? `
                <div class="alert alert-danger">
                    <h5>🚨 Dikkat!</h5>
                    <p>Bazı ürünler için mevcut stok bulundu. Import işlemi bu stoklara ekleme yapacak.</p>
                    <p><strong>Devam etmek istediğinizden emin misiniz?</strong></p>
                </div>
            ` : `
                <div class="alert alert-success">
                    <h5>✅ Güvenli Import</h5>
                    <p>Hiçbir stok çakışması bulunamadı. Import işlemi güvenle devam edebilir.</p>
                </div>
            `}
        </div>
    `);
}

function show_error_message(error, dialog) {
    dialog.fields_dict.loading.$wrapper.html(`
        <div class="alert alert-danger" style="padding: 20px;">
            <h5>❌ Hata</h5>
            <p>Stok kontrolü sırasında hata oluştu:</p>
            <p><code>${error.message || 'Bilinmeyen hata'}</code></p>
        </div>
    `);
}

// Import sonrası özet rapor
frappe.ui.form.on('Data Import', {
    after_import: function(frm) {
        if (frm.doc.reference_doctype === 'Profile Stock Ledger') {
            show_import_summary_report();
        }
    }
});

function show_import_summary_report() {
    frappe.call({
        method: 'uretim_planlama.api.import_pre_check.get_import_summary_report',
        callback: function(response) {
            if (response.message && response.message.status === 'success') {
                let d = new frappe.ui.Dialog({
                    title: __('Import Sonrası Özet'),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'summary',
                            options: generate_summary_html(response.message.data)
                        }
                    ],
                    primary_action_label: __('Kapat'),
                    primary_action: function() {
                        d.hide();
                    }
                });
                d.show();
            }
        }
    });
}

function generate_summary_html(data) {
    let html = `
        <div style="padding: 20px;">
            <div class="alert alert-info">
                <h5>📊 Son 30 Gün İstatistikleri</h5>
                <ul class="mb-0">
                    <li>Toplam Profile Entry: ${data.statistics.total_recent_entries}</li>
                    <li>Toplam Miktar: ${data.statistics.total_recent_qty}</li>
                    <li>Dönem: ${data.statistics.period}</li>
                </ul>
            </div>
        </div>
    `;
    return html;
}
