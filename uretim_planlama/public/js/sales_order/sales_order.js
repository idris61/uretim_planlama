frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        if (frm.fields_dict['custom_raw_materials_html']) {
            // Sadece kaydedilmemiş (yeni) siparişlerde gösterme
            if (frm.is_new() || frm.doc.__islocal) {
                frm.fields_dict['custom_raw_materials_html'].wrapper.innerHTML = '';
                return;
            }
            // Buton ve tablo alanı
            let html = `
                <div style="display:flex;gap:10px;align-items:center;">
                    <button class="btn btn-dark" type="button" id="btn-raw-materials-show">
                        Gerekli Hammaddeler ve Stoklar
                    </button>
                </div>
                <div id="raw-materials-table-content" style="margin-top:16px;"></div>`;
            frm.fields_dict['custom_raw_materials_html'].wrapper.innerHTML = html;

            // Buton eventini sadece bir kez ekle
            const btn = document.getElementById('btn-raw-materials-show');
            if (btn) {
                btn.onclick = function() {
                    const tableContentDiv = document.getElementById('raw-materials-table-content');
                    // Ekstra kontrol: doküman kaydedilmemişse uyarı ver ve devam etme
                    if (!frm.doc.name || frm.doc.__islocal) {
                        frappe.msgprint('Lütfen önce Satış Siparişini kaydedin.');
                        return;
                    }
                    tableContentDiv.innerHTML = '<div style="padding:24px;text-align:center;color:#888;font-size:16px;">Yükleniyor...</div>';
                    loadRawMaterialsTable(frm);
                }
            }
        }
    }
});

function loadRawMaterialsTable(frm) {
    frappe.call({
        method: "uretim_planlama.sales_order_hooks.raw_materials.get_sales_order_raw_materials",
        args: { sales_order: frm.doc.name },
        callback: function(r) {
            if (r.message) {
                let html = '';
                html += `<div style='background:#fff; border-radius:12px; box-shadow:0 2px 8px #b3c6e7; padding:12px; margin-top:8px;'>`;
                html += `<table class=\"table table-bordered table-hover table-striped\" style=\"font-size:14px; border-radius:10px; overflow:hidden; border:1px solid #e3e3e3; margin-bottom:0;\">`;
                html += `<thead style=\"background:#f8fafc; color:#222; font-weight:600;\"><tr>`;
                html += `<th>Hammadde Kodu</th><th>Hammadde Adı</th><th>Sipariş Ürünleri</th><th>Toplam İhtiyaç Miktarı</th><th>Toplam Stok</th><th>Rezerve Miktar</th><th>Kullanılabilir Stok</th><th>Açık Miktar</th><th>Malzeme Talep Miktarı</th><th>Sipariş Edilen Miktar</th><th>Beklenen Teslim Tarihi</th>`;
                html += `</tr></thead><tbody>`;
                r.message.forEach(row => {
                    let rowClass = '';
                    let kullanilabilirStok = parseFloat(row.kullanilabilir_stok) || 0;
                    let acikMiktar = parseFloat(row.acik_miktar) || 0;
                    let stok = parseFloat(row.stock) || 0;
                    let toplam_ihtiyac = parseFloat(row.qty) || 0;
                    let rezerve = parseFloat(row.reserved_qty) || 0;
                    if (acikMiktar > 0) {
                        rowClass = 'table-danger';
                    } else if (kullanilabilirStok > 0) {
                        rowClass = 'table-success';
                    } else if (stok > 0) {
                        rowClass = 'table-warning';
                    }
                    let acikMiktarCell = acikMiktar > 0 ? `<span style='background:#d32f2f;color:#fff;padding:2px 10px;border-radius:6px;font-weight:bold;display:inline-block;'>${acikMiktar.toFixed(2)}</span>` : `<span style='color:#388e3c;font-weight:bold;'>0</span>`;
                    let kullanilabilirStokCell = kullanilabilirStok > 0 ? `<span style='color:#388e3c;font-weight:bold;'>${kullanilabilirStok.toFixed(2)}<br><span style='font-size:10px;color:#888;'>Kullanılabilir</span></span>` : `<span style='color:#d32f2f;font-weight:bold;'>${kullanilabilirStok.toFixed(2)}<br><span style='font-size:10px;color:#888;'>Kullanılabilir</span></span>`;
                    let malzemeTalepCell = (parseFloat(row.malzeme_talep_miktari) || 0) > 0 ? `<span style='color:#1976d2;font-weight:bold;cursor:pointer;' title='${row.malzeme_talep_tooltip}'>${row.malzeme_talep_miktari} <span style='font-size:10px;'>Tedarik Sürecinde</span></span>` : '-';
                    let siparisEdilenCell = (parseFloat(row.siparis_edilen_miktar) || 0) > 0 ? `<span style='color:#1976d2;font-weight:bold;cursor:pointer;' title='${row.siparis_edilen_tooltip}'>${row.siparis_edilen_miktar} <span style='font-size:10px;'>Sipariş Verildi</span></span>` : '-';
                    let beklenenTeslimCell = row.beklenen_teslim_tarihi ? row.beklenen_teslim_tarihi : '-';
                    let qtyFormatted = (row.qty !== undefined && row.qty !== null) ? parseFloat(row.qty).toFixed(2) : '';
                    let reservedQtyFormatted = (row.reserved_qty !== undefined && row.reserved_qty !== null) ? parseFloat(row.reserved_qty).toFixed(2) : '';
                    let itemLink = `<a href='/app/item/${encodeURIComponent(row.raw_material)}' target='_blank'>${row.raw_material}</a>`;
                    html += `<tr class='${rowClass}' style='vertical-align:middle;'>
                        <td style='padding:8px 12px;'>${itemLink}</td>
                        <td style='padding:8px 12px;'>${row.item_name || ''}</td>
                        <td style='padding:8px 12px;'>${row.so_items}</td>
                        <td style='font-weight:bold;color:#222;padding:8px 12px;'>${qtyFormatted}</td>
                        <td style='padding:8px 12px;'>${row.stock}</td>
                        <td style='padding:8px 12px;'>${reservedQtyFormatted}</td>
                        <td style='padding:8px 12px;'>${kullanilabilirStokCell}</td>
                        <td style='padding:8px 12px;'>${acikMiktarCell}</td>
                        <td style='padding:8px 12px;'>${malzemeTalepCell}</td>
                        <td style='padding:8px 12px;'>${siparisEdilenCell}</td>
                        <td style='padding:8px 12px;'>${beklenenTeslimCell}</td>
                    </tr>`;
                });
                html += "</tbody></table>";
                html += `<div style='margin-top:16px;'><button id='create-mr-for-shortages' class='btn btn-primary'>Eksikler İçin Satınalma Talebi Oluştur</button></div>`;
                html += "</div>";
                document.getElementById('raw-materials-table-content').innerHTML = html;

                // Eksikler için satınalma talebi butonu
                const btn = document.getElementById('create-mr-for-shortages');
                if (btn) {
                    btn.onclick = function() {
                        frappe.call({
                            method: "uretim_planlama.sales_order_hooks.raw_materials.create_material_request_for_shortages",
                            args: { sales_order: frm.doc.name },
                            freeze: true,
                            callback: function(res) {
                                if (res.message && res.message.success) {
                                    frappe.show_alert({
                                        message: `Satınalma Talebi Oluşturuldu: <a href='/app/material-request/${res.message.mr_name}' target='_blank'>${res.message.mr_name}</a>` ,
                                        indicator: 'green'
                                    });
                                    loadRawMaterialsTable(frm);
                                } else {
                                    frappe.show_alert({
                                        message: res.message && res.message.message ? res.message.message : 'Talep oluşturulamadı.',
                                        indicator: 'orange'
                                    });
                                }
                            }
                        });
                    }
                }
            }
        }
    });
} 