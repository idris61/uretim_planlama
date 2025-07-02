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
                    <button class="btn btn-warning" type="button" id="btn-long-term-reserve-check">
                        <i class="fa fa-clock-o"></i> Uzun Vadeli Rezerv Kontrolü
                    </button>
                </div>
                <div id="raw-materials-table-content" style="margin-top:16px;"></div>`;
            frm.fields_dict['custom_raw_materials_html'].wrapper.innerHTML = html;

            // Buton eventlerini ekle
            const btnRawMaterials = document.getElementById('btn-raw-materials-show');
            const btnLongTermReserve = document.getElementById('btn-long-term-reserve-check');
            
            if (btnRawMaterials) {
                btnRawMaterials.onclick = function() {
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
            
            if (btnLongTermReserve) {
                btnLongTermReserve.onclick = function() {
                    if (!frm.doc.name || frm.doc.__islocal) {
                        frappe.msgprint('Lütfen önce Satış Siparişini kaydedin.');
                        return;
                    }
                    if (frm.doc.docstatus == 1) {
                        frappe.msgprint('Onaylanmış (submit edilmiş) satış siparişlerinde uzun vadeli rezerv kullanılamaz.');
                        return;
                    }
                    checkLongTermReserveAvailability(frm);
                }
            }
        }
    },
    on_submit: function(frm) {
        // Submit sonrası tabloyu otomatik yenile
        setTimeout(function() {
            loadRawMaterialsTable(frm);
        }, 500);
    }
});

function checkLongTermReserveAvailability(frm) {
            frappe.call({
        method: "uretim_planlama.sales_order_hooks.raw_materials.check_long_term_reserve_availability",
                args: { sales_order: frm.doc.name },
                callback: function(r) {
            if (r.message && r.message.length > 0) {
                showLongTermReserveModal(frm, r.message);
            } else {
                frappe.show_alert({
                    message: 'Uzun vadeli rezervden kullanılabilecek hammadde bulunamadı.',
                    indicator: 'orange'
                });
            }
        }
    });
}

function showLongTermReserveModal(frm, recommendations) {
    let modalHtml = `
        <div class="modal fade" id="longTermReserveModal" tabindex="-1" role="dialog">
            <div class="modal-dialog modal-lg" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fa fa-clock-o text-warning"></i> Uzun Vadeli Rezerv Kullanımı
                        </h5>
                        <button type="button" class="close" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <i class="fa fa-info-circle"></i> 
                            Aşağıdaki hammaddeler için uzun vadeli rezervden kullanım yapılabilir. 
                            Kullanılan miktarlar daha sonra yeniden alınacaktır.
                        </div>
                        <table class="table table-bordered table-hover">
                            <thead class="thead-light">
                                <tr>
                                    <th>Hammadde</th>
                                    <th>Açık Miktar</th>
                                    <th>Uzun Vadeli Rezerv</th>
                                    <th>Uzun Vadeli Kullanılan Rezerv</th>
                                    <th>Kullanılabilir</th>
                                    <th>Önerilen Kullanım</th>
                                    <th>Kullanılacak Miktar</th>
                                </tr>
                            </thead>
                            <tbody>`;
    
    recommendations.forEach((item, index) => {
        modalHtml += `
            <tr style="font-weight:bold;">
                <td>
                    <strong>${item.item_code}</strong><br>
                    <small class="text-muted">${item.item_name}</small>
                </td>
                <td class="text-danger">${item.acik_miktar.toFixed(2)}</td>
                <td class="text-secondary">${item.uzun_vadeli_rezerv.toFixed(2)}</td>
                <td class="text-warning">${item.kullanilan_rezerv.toFixed(2)}</td>
                <td class="text-success">${item.kullanilabilir_uzun_vadeli.toFixed(2)}</td>
                <td class="text-info">${item.onerilen_kullanim.toFixed(2)}</td>
                <td>
                    <input type="number" class="form-control form-control-sm" 
                           id="qty-${index}" 
                           value="${item.onerilen_kullanim.toFixed(2)}" 
                           min="0" 
                           max="${item.kullanilabilir_uzun_vadeli}" 
                           step="0.01"
                           data-item-code="${item.item_code}">
                </td>
            </tr>`;
                        });
    
    modalHtml += `
                            </tbody>
                        </table>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>
                        <button type="button" class="btn btn-warning" id="btn-use-long-term-reserve">
                            <i class="fa fa-check"></i> Uzun Vadeli Rezervden Kullan
                        </button>
                    </div>
                </div>
            </div>
        </div>`;
    
    // Modal'ı DOM'a ekle
    if (document.getElementById('longTermReserveModal')) {
        document.getElementById('longTermReserveModal').remove();
    }
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Modal'ı göster
    $('#longTermReserveModal').modal('show');
    
    // Kullanım butonuna event ekle
    document.getElementById('btn-use-long-term-reserve').onclick = function() {
        useLongTermReserveFromModal(frm, recommendations);
    };
}

function useLongTermReserveFromModal(frm, recommendations) {
    let usageData = [];
    
    recommendations.forEach((item, index) => {
        const qtyInput = document.getElementById(`qty-${index}`);
        const qty = parseFloat(qtyInput.value) || 0;
        
        if (qty > 0) {
            usageData.push({
                item_code: item.item_code,
                qty: qty
            });
        }
    });
    
    if (usageData.length === 0) {
        frappe.show_alert({
            message: 'Kullanılacak miktar seçilmedi.',
            indicator: 'orange'
        });
        return;
    }
    
    frappe.call({
        method: "uretim_planlama.sales_order_hooks.raw_materials.use_long_term_reserve_bulk",
        args: { 
            sales_order: frm.doc.name,
            usage_data: JSON.stringify(usageData)
        },
        freeze: true,
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: r.message.message,
                    indicator: 'green'
                });
                $('#longTermReserveModal').modal('hide');
                // Tabloyu yenile
                loadRawMaterialsTable(frm);
            } else {
                frappe.show_alert({
                    message: r.message && r.message.message ? r.message.message : 'İşlem başarısız.',
                    indicator: 'red'
                });
            }
        }
    });
}

function loadRawMaterialsTable(frm) {
        frappe.call({
            method: "uretim_planlama.sales_order_hooks.raw_materials.get_sales_order_raw_materials",
            args: { sales_order: frm.doc.name },
            callback: function(r) {
                if (r.message) {
                let html = '';
                html += `<div style='background:#fff; border-radius:12px; box-shadow:0 2px 8px #b3c6e7; padding:12px; margin-top:8px;'>`;
                
                // Uzun vadeli rezerv uyarısı kontrolü
                let hasShortageWithLongTermReserve = false;
                let shortageItems = [];
                
                    r.message.forEach(row => {
                    let acikMiktar = parseFloat(row.acik_miktar) || 0;
                    let uzunVadeliRezerv = parseFloat(row.long_term_reserve_qty) || 0;
                    let kullanilanRezerv = parseFloat(row.used_from_long_term_reserve) || 0;
                    
                    if (acikMiktar > 0 && (uzunVadeliRezerv - kullanilanRezerv) > 0) {
                        hasShortageWithLongTermReserve = true;
                        shortageItems.push({
                            item_code: row.raw_material,
                            item_name: row.item_name,
                            acik_miktar: acikMiktar,
                            kullanilabilir_uzun_vadeli: uzunVadeliRezerv - kullanilanRezerv
                        });
                    }
                });
                
                // Uzun vadeli rezerv uyarısı
                let isLongTermOrder = false;
                if (frm.doc.delivery_date) {
                    const today = new Date();
                    const deliveryDate = new Date(frm.doc.delivery_date);
                    const diffDays = Math.ceil((deliveryDate - today) / (1000 * 60 * 60 * 24));
                    if (diffDays > 30) {
                        isLongTermOrder = true;
                    }
                }
                
                if (isLongTermOrder) {
                    html += `
                        <div class="alert alert-info" style="margin-bottom:16px; border-left:4px solid #2196f3;">
                            <div style="display:flex; align-items:center; gap:12px;">
                                <i class="fa fa-clock-o" style="font-size:18px; color:#2196f3;"></i>
                                <div style="flex:1;">
                                    <strong>Uzun Vadeli Sipariş</strong><br>
                                    <small>Bu sipariş uzun vadeli bir sipariştir ve uzun vadeli rezerv olarak ayrılacaktır.</small>
                                </div>
                            </div>
                        </div>`;
                } else if (hasShortageWithLongTermReserve) {
                    html += `
                        <div class="alert alert-warning" style="margin-bottom:16px; border-left:4px solid #ff9800;">
                            <div style="display:flex; align-items:center; gap:12px;">
                                <i class="fa fa-clock-o" style="font-size:18px; color:#ff9800;"></i>
                                <div style="flex:1;">
                                    <strong>Uzun Vadeli Rezerv Kullanımı Önerisi</strong><br>
                                    <small>${shortageItems.length} hammadde için uzun vadeli rezervden kullanım yapılabilir.</small>
                                </div>
                            </div>
                        </div>`;
                }
                
                // Tablo başlıkları
                let showAcikMiktar = !(frm.doc.docstatus == 1);
                let showEksikTalepBtn = !(frm.doc.docstatus == 1);
                html += `<style>
                .custom-raw-material-table th, .custom-raw-material-table td {
                    font-size: 13px;
                }
                .custom-raw-material-table .stok-pozitif-box,
                .custom-raw-material-table .rezerv-pembe,
                .custom-raw-material-table .ihtiyac-turuncu,
                .custom-raw-material-table .acik-miktar {
                    font-size: 13px;
                }
                .custom-raw-material-table th {
                    font-weight: bold;
                    background: #f8f9fa;
                    color: #222;
                    border-bottom: 2px solid #e3e3e3;
                    text-align: center;
                }
                .custom-raw-material-table td {
                    font-weight: bold;
                    color: #222;
                    text-align: center;
                }
                .custom-raw-material-table td:first-child,
                .custom-raw-material-table th:first-child {
                    text-align: left;
                }
                .custom-raw-material-table td:nth-child(2),
                .custom-raw-material-table th:nth-child(2) {
                    text-align: left;
                }
                .custom-raw-material-table .stok-pozitif-box {
                    background: #219653;
                    color: #fff;
                    border-radius: 6px;
                    padding: 2px 12px;
                    display: inline-block;
                    font-weight: bold;
                }
                .custom-raw-material-table .stok-negatif { color: #d32f2f; }
                .custom-raw-material-table .rezerv-mavi { color: #1976d2; }
                .custom-raw-material-table .kullanilan-rezerv-turuncu { color: #ff9800; }
                .custom-raw-material-table .acik-miktar { background: #d32f2f; color: #fff; border-radius: 6px; padding: 2px 10px; display: inline-block; }
                .custom-raw-material-table .rezerv-pembe {
                    background: #e573b4;
                    color: #fff;
                    border-radius: 6px;
                    padding: 2px 12px;
                    display: inline-block;
                    font-weight: bold;
                }
                .custom-raw-material-table .ihtiyac-turuncu {
                    background: #ff9800;
                    color: #fff;
                    border-radius: 6px;
                    padding: 2px 12px;
                    display: inline-block;
                    font-weight: bold;
                }
                .custom-raw-material-table .beyaz-kutu {
                    background: #fff;
                    border-radius: 6px;
                    padding: 2px 12px;
                    display: inline-block;
                    font-weight: bold;
                }
                </style>`;
                html += `<table class="table table-bordered custom-raw-material-table" style="border-radius:10px; overflow:hidden; border:1px solid #e3e3e3; margin-bottom:0;">
                <thead>
                  <tr>
                    <th>Hammadde Kodu</th>
                    <th>Hammadde Adı</th>
                    <th>Mevcut Sipariş İhtiyacı</th>
                    <th>Fiziki Stok (Depo)</th>
                    <th>Toplam Rezerv Miktarı</th>
                    <th>Uzun Vadeli Rezerv</th>
                    <th>Uzun Vadeli Kullanılan Rezerv</th>
                    <th>Kullanılabilir Stok</th>`;
                if (showAcikMiktar) html += `<th>Açık Miktar</th>`;
                html += `<th>Malzeme Talep Miktarı</th>
                    <th>Sipariş Edilen Miktar</th>
                    <th>Beklenen Teslim Tarihi</th>
                  </tr>
                </thead><tbody>`;
                r.message.forEach(row => {
                    let rowClass = '';
                    let kullanilabilirStok = parseFloat(row.kullanilabilir_stok) || 0;
                    let acikMiktar = parseFloat(row.acik_miktar) || 0;
                    let stok = parseFloat(row.stock) || 0;
                    let stok_by_warehouse = row.stock_by_warehouse || {};
                    let uzunVadeliRezerv = parseFloat(row.long_term_reserve_qty) || 0;
                    let kullanilanRezerv = parseFloat(row.used_from_long_term_reserve) || 0;
                    if (acikMiktar > 0) {
                        rowClass = 'table-danger';
                    } else if (kullanilabilirStok > 0) {
                        rowClass = 'table-success';
                    } else if (stok > 0) {
                        rowClass = 'table-warning';
                    }
                    let acikMiktarCell = acikMiktar > 0 ? `<span class='acik-miktar'>${acikMiktar.toFixed(2)}</span>` : `<span class='stok-pozitif-box'>0</span>`;
                    let kullanilabilirStokCell = kullanilabilirStok > 0 ? `<span class='stok-pozitif-box'>${kullanilabilirStok.toFixed(2)}</span>` : `<span class='stok-negatif'>${kullanilabilirStok.toFixed(2)}</span>`;
                    let uzunVadeliRezervCell = uzunVadeliRezerv > 0
                        ? `<a href="#" class="beyaz-kutu rezerv-mavi long-term-detail-link" data-item='${row.raw_material}' style="text-decoration:underline;">${uzunVadeliRezerv.toFixed(2)}</a>`
                        : `<span class='beyaz-kutu rezerv-mavi'>${uzunVadeliRezerv.toFixed(2)}</span>`;
                    let kullanilanRezervCell = kullanilanRezerv > 0
                        ? `<a href="#" class="beyaz-kutu kullanilan-rezerv-turuncu used-long-term-detail-link" data-item='${row.raw_material}' style="text-decoration:underline;">${kullanilanRezerv.toFixed(2)}</a>`
                        : `<span class='beyaz-kutu kullanilan-rezerv-turuncu'>${kullanilanRezerv.toFixed(2)}</span>`;
                    let malzemeTalepCell = (row.malzeme_talep_details && row.malzeme_talep_details.length > 0)
                        ? `<a href="#" class="malzeme-talep-detail-link" data-item='${row.raw_material}' style="color:#1976d2;font-weight:bold;text-decoration:underline;">${row.malzeme_talep_details.reduce((a,b)=>a+parseFloat(b.qty||0),0)}</a>`
                        : '-';
                    let siparisEdilenCell = (row.siparis_edilen_details && row.siparis_edilen_details.length > 0)
                        ? `<a href="#" class="siparis-edilen-detail-link" data-item='${row.raw_material}' style="color:#1976d2;font-weight:bold;text-decoration:underline;">${row.siparis_edilen_details.reduce((a,b)=>a+parseFloat(b.qty||0),0)}</a>`
                        : '-';
                    let beklenenTeslimCell = row.beklenen_teslim_tarihi ? row.beklenen_teslim_tarihi : '-';
                    let qtyFormatted = (row.qty !== undefined && row.qty !== null) ? parseFloat(row.qty).toFixed(2) : '';
                    let reservedQtyFormatted = (row.reserved_qty !== undefined && row.reserved_qty !== null) ? parseFloat(row.reserved_qty).toFixed(2) : '';
                    let itemLink = `<a href='/app/item/${encodeURIComponent(row.raw_material)}' target='_blank'>${row.raw_material}</a>`;
                    let itemNameLink = row.item_name ? `<a href='/app/item/${encodeURIComponent(row.raw_material)}' target='_blank'>${row.item_name}</a>` : '';
                    let stokTooltip = Object.keys(stok_by_warehouse).length > 0
                        ? Object.entries(stok_by_warehouse)
                            .filter(([depo, miktar]) => miktar > 0)
                            .map(([depo, miktar]) => `${depo}: ${miktar}`)
                            .join("<br>")
                        : "-";
                    let stokCell = stok >= 0
                        ? `<span class='stok-pozitif-box' style='cursor:pointer;' title='${stokTooltip.replace(/'/g, "&apos;")}' data-toggle='tooltip' data-html='true'>${stok}</span>`
                        : `<span class='stok-negatif' style='cursor:pointer;' title='${stokTooltip.replace(/'/g, "&apos;")}' data-toggle='tooltip' data-html='true'>${stok}</span>`;
                    let rezervCell = reservedQtyFormatted > 0 ? `<span class='rezerv-pembe'>${reservedQtyFormatted}</span>` : reservedQtyFormatted;
                    let ihtiyacCell = qtyFormatted > 0 ? `<span class='ihtiyac-turuncu'>${qtyFormatted}</span>` : qtyFormatted;
                    html += `<tr class='${rowClass}' style='vertical-align:middle;'>
                        <td style='padding:8px 12px;'>${itemLink}</td>
                        <td style='padding:8px 12px;'>${itemNameLink}</td>
                        <td style='padding:8px 12px;'>${ihtiyacCell}</td>
                        <td style='padding:8px 12px;'>${stokCell}</td>
                        <td style='padding:8px 12px;'>${rezervCell}</td>
                        <td style='padding:8px 12px;'>${uzunVadeliRezervCell}</td>
                        <td style='padding:8px 12px;'>${kullanilanRezervCell}</td>
                        <td style='padding:8px 12px;'>${kullanilabilirStokCell}</td>`;
                    if (showAcikMiktar) {
                        html += `<td style='padding:8px 12px;'>${acikMiktarCell}</td>`;
                    }
                    html += `<td style='padding:8px 12px;'>${malzemeTalepCell}</td>
                        <td style='padding:8px 12px;'>${siparisEdilenCell}</td>
                        <td style='padding:8px 12px;'>${beklenenTeslimCell}</td>
                    </tr>`;
                });
                html += "</tbody></table>";
                if (showEksikTalepBtn) {
                    html += `<button class="btn btn-dark" id="btn-create-mr-for-shortages" style="margin-top:8px;">Eksikler İçin Satınalma Talebi Oluştur</button>`;
                }
                html += "</div>";
                document.getElementById('raw-materials-table-content').innerHTML = html;
                if (showEksikTalepBtn) {
                    const btn = document.getElementById('btn-create-mr-for-shortages');
                    if (btn) {
                        btn.onclick = function() {
                            frappe.call({
                                method: "uretim_planlama.sales_order_hooks.raw_materials.create_material_request_for_shortages",
                                args: { sales_order: frm.doc.name },
                                freeze: true,
                                callback: function(res) {
                                    if (res.message && res.message.success) {
                                        let message = res.message.message || 'Satınalma Talebi oluşturuldu.';
                                        if (res.message.created_rows) {
                                            let shortageCount = res.message.created_rows.filter(row => row.type === 'shortage').length;
                                            let renewalCount = res.message.created_rows.filter(row => row.type === 'renewal').length;
                                            if (renewalCount > 0) {
                                                message += ` (${shortageCount} eksik miktar, ${renewalCount} rezerv yenileme)`;
                                            }
                                        }
                                        frappe.show_alert({
                                            message: `${message} <a href='/app/material-request/${res.message.mr_name}' target='_blank'>${res.message.mr_name}</a>` ,
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
                // Tabloyu ekledikten sonra eventleri bağla:
                setTimeout(function() {
                    // Uzun vadeli rezerv detay linkleri
                    document.querySelectorAll('.long-term-detail-link').forEach(el => {
                        el.onclick = function(e) {
                            e.preventDefault();
                            let itemCode = el.getAttribute('data-item');
                            let row = r.message.find(rw => rw.raw_material === itemCode);
                            if (row && row.long_term_details && row.long_term_details.length > 0) {
                                showDetailsModal(__('Long Term Reserve Details'), row.long_term_details, [__('Sales Order'), __('Customer'), __('Delivery Date'), __('Quantity')], 'sales-order');
                            } else {
                                frappe.show_alert({message:__('No details found.'), indicator:'orange'});
                            }
                        };
                    });
                    // Kullanılan uzun vadeli rezerv detay linkleri
                    document.querySelectorAll('.used-long-term-detail-link').forEach(el => {
                        el.onclick = function(e) {
                            e.preventDefault();
                            let itemCode = el.getAttribute('data-item');
                            let row = r.message.find(rw => rw.raw_material === itemCode);
                            if (row && row.used_long_term_details && row.used_long_term_details.length > 0) {
                                showDetailsModal(__('Used Long Term Reserve Details'), row.used_long_term_details, [__('Sales Order'), __('Customer'), __('Usage Date'), __('Used Qty')], 'sales-order');
                            } else {
                                frappe.show_alert({message:__('No details found.'), indicator:'orange'});
                            }
                        };
                    });
                    // Malzeme Talep Detay linkleri
                    document.querySelectorAll('.malzeme-talep-detail-link').forEach(el => {
                        el.onclick = function(e) {
                            e.preventDefault();
                            let itemCode = el.getAttribute('data-item');
                            let row = r.message.find(rw => rw.raw_material === itemCode);
                            if (row && row.malzeme_talep_details && row.malzeme_talep_details.length > 0) {
                                showDocumentDetailsModal(__('Material Request Details'), row.malzeme_talep_details, [__('Document No'), __('Quantity'), __('Date')], 'material-request');
                            }
                        };
                    });
                    // Sipariş Edilen Detay linkleri
                    document.querySelectorAll('.siparis-edilen-detail-link').forEach(el => {
                        el.onclick = function(e) {
                            e.preventDefault();
                            let itemCode = el.getAttribute('data-item');
                            let row = r.message.find(rw => rw.raw_material === itemCode);
                            if (row && row.siparis_edilen_details && row.siparis_edilen_details.length > 0) {
                                showDocumentDetailsModal(__('Purchase Order Details'), row.siparis_edilen_details, [__('Document No'), __('Quantity'), __('Date')], 'purchase-order');
                            }
                        };
                    });
                    // Tooltipleri etkinleştir
                    $(`[data-toggle='tooltip']`).tooltip({html:true, trigger:'hover click'});
                }, 100);
            }
        });
    }


// Modal gösterme fonksiyonu (her tür detay için)
function showDetailsModal(title, details, columns, doctype) {
    // Türkçe başlık -> backend anahtarı eşlemesi
    const colMap = {
        'Satış Siparişi': ['sales_order', 'parent'],
        'Müşteri': ['customer'],
        'Teslimat Tarihi': ['delivery_date'],
        'Kullanım Tarihi': ['usage_date'],
        'Miktar': ['quantity', 'qty'],
        'Kullanılan Miktar': ['used_qty'],
        'Belge No': ['parent'],
        'Tarih': ['schedule_date', 'transaction_date'],
        'Quantity': ['quantity', 'qty'],
        'Date': ['schedule_date', 'transaction_date'],
        'Customer': ['customer'],
        'Delivery Date': ['delivery_date'],
        'Usage Date': ['usage_date'],
        'Used Qty': ['used_qty'],
        'Document No': ['parent'],
        'Sales Order': ['sales_order', 'parent']
    };
    let modalHtml = `
        <div class="modal fade" id="detailsModal" tabindex="-1" role="dialog">
            <div class="modal-dialog modal-lg" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
                    </div>
                    <div class="modal-body">
                        <table class="table table-bordered table-hover">
                            <thead><tr>${columns.map(col => `<th>${col}</th>`).join('')}</tr></thead>
                            <tbody>`;
    details.forEach(row => {
        modalHtml += `<tr>`;
        columns.forEach(col => {
            let val = '';
            // Belge linki için
            if(col === __('Sales Order') || col === __('Document No') || col === 'Satış Siparişi' || col === 'Belge No') {
                let keyList = colMap[col] || [];
                let docVal = '';
                for (let k of keyList) { if (row[k]) { docVal = row[k]; break; } }
                let doctype_link = doctype || (col.includes('Satış') ? 'sales-order' : '');
                if (docVal) {
                    val = `<a href="/app/${doctype_link}/${docVal}" target="_blank">${docVal}</a>`;
                }
            } else {
                let keyList = colMap[col] || [col.toLowerCase().replace(/ /g,'_')];
                for (let k of keyList) { if (row[k] !== undefined && row[k] !== null) { val = row[k]; break; } }
            }
            modalHtml += `<td>${val || ''}</td>`;
        });
        modalHtml += `</tr>`;
    });
    modalHtml += `</tbody></table></div></div></div></div>`;
    if (document.getElementById('detailsModal')) document.getElementById('detailsModal').remove();
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    $('#detailsModal').modal('show');
}

// Modal fonksiyonu
function showDocumentDetailsModal(title, details, columns, doctype) {
    showDetailsModal(title, details, columns, doctype);
}