frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        if (frm.fields_dict['custom_raw_materials_html']) {
            // Sadece kaydedilmemiş (yeni) siparişlerde gösterme
            if (frm.is_new() || frm.doc.__islocal) {
                frm.fields_dict['custom_raw_materials_html'].wrapper.innerHTML = '';
                return;
            }
            // Buton ve tablo alanı (sadeleştirildi)
            let html = `
                <div style="display:flex;gap:10px;align-items:center;">
                    <button class="btn btn-dark" type="button" id="btn-raw-materials-show">
                        Gerekli Hammaddeler ve Stoklar
                    </button>
                    <button class="btn btn-warning" type="button" id="btn-long-term-reserve-check">
                        <i class="fa fa-clock-o"></i> Uzun Vadeli Rezerv Kontrolü
                    </button>
                    <button class="btn btn-danger" type="button" id="btn-clear-long-term-reserve">
                        <i class="fa fa-trash"></i> Kalan Uzun Vadeli Rezervi Temizle
                    </button>
                </div>
                <div id="raw-materials-table-content" style="margin-top:16px;"></div>`;
            frm.fields_dict['custom_raw_materials_html'].wrapper.innerHTML = html;

            // Buton eventlerini ekle
            const btnRawMaterials = document.getElementById('btn-raw-materials-show');
            const btnLongTermReserve = document.getElementById('btn-long-term-reserve-check');
            const btnClearLongTermReserve = document.getElementById('btn-clear-long-term-reserve');
            
            if (btnRawMaterials) {
                btnRawMaterials.onclick = function() {
                    const tableContentDiv = document.getElementById('raw-materials-table-content');
                    if (!frm.doc.name || frm.doc.__islocal) {
                        frappe.msgprint('Lütfen önce Satış Siparişini kaydedin.');
                        return;
                    }
                    tableContentDiv.innerHTML = '<div style="padding:24px;text-align:center;color:#888;font-size:16px;">Yükleniyor...</div>';
                    loadRawMaterialsTable(frm);
                }
            }
            // --- YENİ: Child siparişlerde uzun vadeli rezerv butonunu ve temizleme butonunu gizle ---
            if (frm.doc.is_long_term_child || frm.doc.parent_sales_order) {
                if (btnLongTermReserve) btnLongTermReserve.style.display = 'none';
                if (btnClearLongTermReserve) btnClearLongTermReserve.style.display = 'none';
            } else {
                if (btnLongTermReserve) btnLongTermReserve.style.display = '';
                if (btnClearLongTermReserve) btnClearLongTermReserve.style.display = '';
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
                    // Child siparişlerde buton zaten gizli, yine de koruma
                    if (frm.doc.is_long_term_child || frm.doc.parent_sales_order) {
                        frappe.msgprint('Bu sipariş ana siparişe bağlıdır. Uzun vadeli rezerv kullanımı ana siparişten yönetilmelidir.');
                        return;
                    }
                    checkLongTermReserveAvailability(frm);
                }
            }
            if (btnClearLongTermReserve) {
                btnClearLongTermReserve.onclick = function() {
                    frappe.confirm(
                        'Bu satış siparişine ait tüm uzun vadeli rezervler silinecek. Emin misiniz?',
                        function() {
                            frappe.call({
                                method: "uretim_planlama.sales_order_hooks.raw_materials.clear_remaining_reserves",
                                args: { parent_sales_order: frm.doc.name },
                                callback: function(r) {
                                    if (r.message && r.message.success) {
                                        frappe.show_alert({
                                            message: 'Kalan uzun vadeli rezervler silindi!',
                                            indicator: 'green'
                                        });
                                        loadRawMaterialsTable(frm);
                                    }
                                }
                            });
                        }
                    );
                };
            }
        }
    },
    on_submit: function(frm) {
        setTimeout(function() {
            loadRawMaterialsTable(frm);
        }, 500);
    },
    delivery_date: function(frm) {
        if (frm.doc.items && frm.doc.delivery_date) {
            frm.doc.items.forEach(function(row) {
                row.delivery_date = frm.doc.delivery_date;
            });
            frm.refresh_field("items");
        }
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
        const maxKullanilabilir = Number(item.kullanilabilir_uzun_vadeli);
        // Eğer usage kaydı varsa input'u pasif yap
        const isUsed = Number(item.kullanilan_rezerv) > 0;
        modalHtml += `
            <tr style="font-weight:bold;">
                <td>
                    <strong>${item.item_code}</strong><br>
                    <small class="text-muted">${item.item_name}</small>
                </td>
                <td class="text-danger">${item.acik_miktar !== undefined && item.acik_miktar !== null ? Number(item.acik_miktar).toFixed(4) : "0.0000"}</td>
                <td class="text-secondary">${item.uzun_vadeli_rezerv !== undefined && item.uzun_vadeli_rezerv !== null ? Number(item.uzun_vadeli_rezerv).toFixed(4) : "0.0000"}</td>
                <td class="text-warning">${item.kullanilan_rezerv !== undefined && item.kullanilan_rezerv !== null ? Number(item.kullanilan_rezerv).toFixed(4) : "0.0000"}</td>
                <td class="text-success">${item.kullanilabilir_uzun_vadeli !== undefined && item.kullanilabilir_uzun_vadeli !== null ? maxKullanilabilir.toFixed(4) : "0.0000"}</td>
                <td class="text-info">${item.onerilen_kullanim !== undefined && item.onerilen_kullanim !== null ? Number(item.onerilen_kullanim).toFixed(4) : "0.0000"}</td>
                <td>
                    <input type="number" class="form-control form-control-sm" 
                           id="qty-${index}" 
                           value="${item.onerilen_kullanim !== undefined && item.onerilen_kullanim !== null ? Math.min(Number(item.onerilen_kullanim), maxKullanilabilir).toFixed(4) : "0.0000"}" 
                           min="0" 
                           max="${maxKullanilabilir.toFixed(4)}" 
                           step="0.0001"
                           data-item-code="${item.item_code}"
                           ${isUsed ? 'disabled' : ''}>
                    <div style='font-size:11px;color:#888;'>Maksimum: ${maxKullanilabilir.toFixed(4)}</div>
                    ${isUsed ? `<div style='color:#d32f2f;font-size:12px;'>Bu ürün için zaten uzun vadeli rezerv kullanımı yapılmış.</div>` : ''}
                </td>
            </tr>`;
    });
    modalHtml += `</tbody></table></div><div class="modal-footer"><button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button><button type="button" class="btn btn-warning" id="btn-use-long-term-reserve"><i class="fa fa-check"></i> Uzun Vadeli Rezervden Kullan</button></div></div></div></div>`;
    if (document.getElementById('longTermReserveModal')) {
        document.getElementById('longTermReserveModal').remove();
    }
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    $('#longTermReserveModal').modal('show');
    document.getElementById('btn-use-long-term-reserve').onclick = function() {
        recommendations.forEach((item, index) => {
            const maxKullanilabilir = Number(item.kullanilabilir_uzun_vadeli);
            const qtyInput = document.getElementById(`qty-${index}`);
            if (qtyInput && parseFloat(qtyInput.value) > maxKullanilabilir) {
                qtyInput.value = maxKullanilabilir.toFixed(4);
            }
            // Inputu 4 basamakta gönder
            if (qtyInput) {
                qtyInput.value = Number(qtyInput.value).toFixed(4);
            }
        });
        useLongTermReserveFromModal(frm, recommendations);
    };
}

function useLongTermReserveFromModal(frm, recommendations) {
    let usageData = [];
    
    recommendations.forEach((item, index) => {
        const qtyInput = document.getElementById(`qty-${index}`);
        let qty = parseFloat(qtyInput.value) || 0;
        qty = Number(qty).toFixed(4); // 4 ondalık olarak gönder
        
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
                // --- YENİ: Uzun vadeli sipariş bilgilendirme uyarısı ---
                if (isLongTermOrder) {
                    html += `
                        <div class="alert alert-info" style="margin-bottom:16px; border-left:4px solid #1976d2;">
                            <i class="fa fa-info-circle"></i>
                            <b>Bu sipariş uzun vadeli bir sipariştir ve uzun vadeli rezerv olarak ayrılacaktır.</b>
                        </div>`;
                }
                // --- YENİ: Child siparişlerde özel uyarı ve öneri/buton gizleme ---
                if (frm.doc.is_long_term_child || frm.doc.parent_sales_order) {
                    html += `
                        <div class="alert" style="margin-bottom:16px; border-left:4px solid #ff9800; background:#fff8e1; color:#ff9800;">
                            <i class="fa fa-info-circle"></i>
                            <b>Bu sipariş için, ana sipariş rezervleri kullanılacaktır.</b>
                        </div>`;
                } else if (hasShortageWithLongTermReserve && frm.doc.docstatus != 1) {
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
                .custom-raw-material-table-wrapper {
                    max-height: 700px;
                    overflow: auto;
                    border-radius: 10px;
                    border: 1px solid #e3e3e3;
                    margin-bottom: 0;
                }
                .custom-raw-material-table {
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                }
                .custom-raw-material-table thead th {
                    position: sticky;
                    top: 0;
                    z-index: 2;
                    background: #f8f9fa;
                    color: #222;
                    border-bottom: 2px solid #e3e3e3;
                    text-align: center;
                }
                </style>`;
                html += `<div class="custom-raw-material-table-wrapper">
                <table class="table table-bordered custom-raw-material-table">
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
                // Satırları renk önceliğine göre sıralamak için önce rowClass'ı belirleyip diziye at
                let rows = r.message.map(row => {
                    let rowClass = '';
                    let acikMiktar = parseFloat(row.acik_miktar) || 0;
                    let kullanilabilirStok = parseFloat(row.kullanilabilir_stok) || 0;
                    if (Math.abs(acikMiktar) > 0.001) {
                        rowClass = 'table-danger';
                    } else if (kullanilabilirStok > 0.001) {
                        rowClass = 'table-success';
                    } else {
                        rowClass = 'table-warning';
                    }
                    return { row, rowClass };
                });
                // Renk önceliği: kırmızı > sarı > yeşil
                const renkOncelik = {
                    'table-danger': 1,
                    'table-warning': 2,
                    'table-success': 3,
                    '': 99
                };
                rows.sort((a, b) => (renkOncelik[a.rowClass] || 99) - (renkOncelik[b.rowClass] || 99));
                // Tabloyu oluştururken sıralı rows'u kullan
                rows.forEach(({row, rowClass}) => {
                    let acikMiktar, kullanilabilirStok, stok, stok_by_warehouse, uzunVadeliRezerv, kullanilanRezerv;
                    let acikMiktarCell, kullanilabilirStokCell, toplamRezervCell, uzunVadeliRezervCell, kullanilanRezervCell, malzemeTalepCell, siparisEdilenCell, beklenenTeslimCell, qtyFormatted, reservedQtyFormatted, itemLink, itemNameLink, stokTooltip, stokCell, ihtiyacCell;
                    acikMiktar = parseFloat(row.acik_miktar) || 0;
                    kullanilabilirStok = parseFloat(row.kullanilabilir_stok) || 0;
                    stok = parseFloat(row.stock) || 0;
                    stok_by_warehouse = row.stock_by_warehouse || {};
                    uzunVadeliRezerv = parseFloat(row.total_long_term_reserve_qty) || 0;
                    kullanilanRezerv = parseFloat(row.used_from_long_term_reserve) || 0;
                    // Child siparişlerde özel gösterim (backend'den gelen alanlara göre)
                    let isLongTermChild = row.is_long_term_child || row.parent_sales_order;
                    if (isLongTermChild) {
                        kullanilabilirStokCell = "<span title='Ana rezervden karşılanacak' style='color:#888;cursor:help;'>-</span>";
                        acikMiktarCell = "<span title='Ana rezervden karşılanacak' style='color:#888;cursor:help;'>-</span>";
                    } else {
                        acikMiktarCell = Math.abs(acikMiktar) > 0.001 ? `<span class='acik-miktar'>${acikMiktar.toFixed(2)}</span>` : `<span class='stok-pozitif-box'>0</span>`;
                        kullanilabilirStokCell = kullanilabilirStok > 0.001 ? `<span class='stok-pozitif-box'>${kullanilabilirStok.toFixed(2)}</span>` : `<span class='stok-negatif'>${kullanilabilirStok.toFixed(2)}</span>`;
                    }
                    toplamRezervCell = `<span class='beyaz-kutu rezerv-pembe total-reserved-detail-link' data-item='${row.raw_material}'><span style='color:#fff; text-decoration:underline; cursor:pointer;'>${parseFloat(row.total_reserved_qty || 0).toFixed(2)}</span></span>`;
                    // Uzun vadeli rezerv detay linki
                    uzunVadeliRezervCell = uzunVadeliRezerv > 0
                        ? `<a href="#" class="beyaz-kutu rezerv-mavi long-term-detail-link" data-item='${row.raw_material}' style="text-decoration:underline; cursor:pointer;">${uzunVadeliRezerv.toFixed(2)}</a>`
                        : `<span class='beyaz-kutu rezerv-mavi'>${uzunVadeliRezerv.toFixed(2)}</span>`;
                    // Kullanılan uzun vadeli rezerv detay linki
                    kullanilanRezervCell = kullanilanRezerv > 0
                        ? `<a href="#" class="beyaz-kutu kullanilan-rezerv-turuncu used-long-term-detail-link" data-item='${row.raw_material}' style="text-decoration:underline; cursor:pointer;">${kullanilanRezerv.toFixed(2)}</a>`
                        : `<span class='beyaz-kutu kullanilan-rezerv-turuncu'>${kullanilanRezerv.toFixed(2)}</span>`;
                    malzemeTalepCell = (row.malzeme_talep_details && row.malzeme_talep_details.length > 0)
                        ? `<a href="#" class="malzeme-talep-detail-link" data-item='${row.raw_material}' style="color:#1976d2;font-weight:bold;text-decoration:underline;">${row.malzeme_talep_details.reduce((a,b)=>a+parseFloat(b.qty||0),0)}</a>`
                        : '-';
                    siparisEdilenCell = (row.siparis_edilen_details && row.siparis_edilen_details.length > 0)
                        ? `<a href="#" class="siparis-edilen-detail-link" data-item='${row.raw_material}' style="color:#1976d2;font-weight:bold;text-decoration:underline;">${row.siparis_edilen_details.reduce((a,b)=>a+parseFloat(b.qty||0),0)}</a>`
                        : '-';
                    beklenenTeslimCell = row.beklenen_teslim_tarihi ? row.beklenen_teslim_tarihi : '-';
                    qtyFormatted = (row.qty !== undefined && row.qty !== null) ? parseFloat(row.qty).toFixed(2) : '';
                    itemLink = `<a href='/app/item/${encodeURIComponent(row.raw_material)}' target='_blank'>${row.raw_material}</a>`;
                    itemNameLink = row.item_name ? `<a href='/app/item/${encodeURIComponent(row.raw_material)}' target='_blank'>${row.item_name}</a>` : '';
                    stokTooltip = Object.keys(stok_by_warehouse).length > 0
                        ? Object.entries(stok_by_warehouse)
                            .filter(([depo, miktar]) => miktar > 0)
                            .map(([depo, miktar]) => `${depo}: ${miktar}`)
                            .join("<br>")
                        : "-";
                    stokCell = stok >= 0
                        ? `<span class='stok-pozitif-box' style='cursor:pointer;' title='${stokTooltip.replace(/'/g, "&apos;")}' data-toggle='tooltip' data-html='true'>${stok}</span>`
                        : `<span class='stok-negatif' style='cursor:pointer;' title='${stokTooltip.replace(/'/g, "&apos;")}' data-toggle='tooltip' data-html='true'>${stok}</span>`;
                    ihtiyacCell = qtyFormatted > 0 ? `<span class='ihtiyac-turuncu'>${qtyFormatted}</span>` : qtyFormatted;
                    html += `<tr class='${rowClass}' style='vertical-align:middle;'>
                        <td style='padding:8px 12px;'>${itemLink}</td>
                        <td style='padding:8px 12px;'>${itemNameLink}</td>
                        <td style='padding:8px 12px;'>${ihtiyacCell}</td>
                        <td style='padding:8px 12px;'>${stokCell}</td>
                        <td style='padding:8px 12px;'>${toplamRezervCell}</td>
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
                html += "</tbody></table></div>";
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
                                showDetailsModal(__('Long Term Reserve Details'), row.long_term_details, [__('Sales Order'), __('Customer'), __('Nihayi Müşteri'), __('Delivery Date'), __('Quantity')], 'sales-order');
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
                                showDocumentDetailsModal(__('Used Long Term Reserve Details'), row.used_long_term_details, [__('Sales Order'), __('Customer'), __('Usage Date'), __('Used Qty')], 'sales-order');
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
                                showDetailsModal(__('Material Request Details'), row.malzeme_talep_details, [__('Belge No'), __('Miktar'), __('Tarih')], 'material-request');
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
                                showDetailsModal(__('Purchase Order Details'), row.siparis_edilen_details, [__('Belge No'), __('Miktar'), __('Tarih')], 'purchase-order');
                            }
                        };
                    });
                    // Toplam Rezerv Miktarı hücresini tıklanabilir yap
                    document.querySelectorAll('.total-reserved-detail-link').forEach(el => {
                        el.onclick = function(e) {
                            e.preventDefault();
                            let itemCode = el.getAttribute('data-item');
                            let row = r.message.find(rw => rw.raw_material === itemCode);
                            if (row && row.total_reserved_details && row.total_reserved_details.length > 0) {
                                showDetailsModal(__('Toplam Rezerv Detayı'), row.total_reserved_details, [__('Sales Order'), __('Customer'), __('Nihayi Müşteri'), __('Quantity')], 'sales-order');
                            } else {
                                frappe.show_alert({message:__('No details found.'), indicator:'orange'});
                            }
                        };
                    });
                    // Tooltipleri etkinleştir
                    $(`[data-toggle='tooltip']`).tooltip({html:true, trigger:'hover click'});
                }, 100);
            }
        });
    }


// Modal gösterme fonksiyonu (her tür detay için) - mapping sadeleştirildi, "Nihai Müşteri" ve özel alanlar korundu
function enrichDetailsWithEndCustomer(details) {
    let soToEndCustomer = {};
    details.forEach(d => {
        if (d.sales_order && d.custom_end_customer) {
            soToEndCustomer[d.sales_order] = d.custom_end_customer;
        }
    });
    return details.map(detail => {
        if ((!detail.custom_end_customer || detail.custom_end_customer === '') && detail.sales_order && soToEndCustomer[detail.sales_order]) {
            return { ...detail, custom_end_customer: soToEndCustomer[detail.sales_order] };
        }
        return detail;
    });
}

    const colMap = {
        'Satış Siparişi': ['sales_order', 'parent'],
        'Müşteri': ['customer'],
    'Nihayi Müşteri': ['custom_end_customer'],
    'End Customer': ['custom_end_customer'],
        'Teslimat Tarihi': ['delivery_date'],
    'Teslim Tarihi': ['delivery_date'],
        'Kullanım Tarihi': ['usage_date'],
    'Miktar': ['qty', 'quantity'],
    'Quantity': ['qty', 'quantity'],
        'Kullanılan Miktar': ['used_qty'],
    'Belge No': ['parent', 'name'],
    'Tarih': ['transaction_date', 'schedule_date', 'date'],
    'Date': ['transaction_date', 'schedule_date', 'date'],
    'Document No': ['parent', 'name'],
        'Customer': ['customer'],
        'Delivery Date': ['delivery_date'],
        'Usage Date': ['usage_date'],
        'Used Qty': ['used_qty'],
        'Sales Order': ['sales_order', 'parent']
    };

function showDetailsModal(title, details, columns, type) {
    if (columns.includes(__('End Customer')) || columns.includes(__('Nihayi Müşteri'))) {
        details = enrichDetailsWithEndCustomer(details);
    }
    renderDetailsModal(title, details, columns, type);
}

function renderDetailsModal(title, details, columns, doctype) {
    let html = `<div style='overflow-x:auto;'>`;
    html += `<table class='table table-bordered'>`;
    html += `<thead><tr>`;
    columns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += `</tr></thead><tbody>`;
    // --- HATA DÜZELTME: hasLongTerm ve hasChild fonksiyon başında tanımlanmalı ---
    let hasLongTerm = false;
    let hasChild = false;
    let hasChildUsage = false;
    if (!details || details.length === 0) {
        html += `<tr><td colspan='${columns.length}' style='text-align:center;'>Kayıt bulunamadı.</td></tr>`;
    } else {
        const today = new Date();
        const thirtyDaysLater = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 30);
        details.forEach(detail => {
            // Uzun vadeli sipariş mi?
            let isLongTerm = false;
            if (detail.delivery_date) {
                let dt = new Date(detail.delivery_date);
                if (!isNaN(dt) && dt >= thirtyDaysLater) isLongTerm = true;
            }
            // Child sipariş mi?
            let isChild = false;
            if (detail.is_long_term_child || detail.parent_sales_order) isChild = true;
            // Child usage satırı mı? (ana rezervden child'a aktarılan miktar)
            let isChildUsage = false;
            if (detail.is_child_usage) isChildUsage = true;
            
            if (isLongTerm) hasLongTerm = true;
            if (isChild) hasChild = true;
            if (isChildUsage) hasChildUsage = true;
            
            let rowStyle = '';
            if (isLongTerm) rowStyle = "background:#e3f2fd;color:#1976d2;font-weight:bold;";
            if (isChild) rowStyle = "background:#fff3e0;color:#ff9800;font-weight:bold;";
            if (isChildUsage) rowStyle = "background:#fff3e0;color:#ff9800;font-weight:bold;";
            
            html += `<tr${rowStyle ? ` style='${rowStyle}'` : ''}>`;
            columns.forEach(col => {
                let val = '';
                // Dinamik belge linki için mantık eklendi
                if(col === __('Sales Order') || col === __('Document No') || col === 'Satış Siparişi' || col === 'Belge No') {
                    let keyList = colMap[col] || [];
                    let docVal = '';
                    for (let k of keyList) { if (detail[k]) { docVal = detail[k]; break; } }
                    // Doctype'ı otomatik belirle
                    let doctype_link = doctype;
                    if (!doctype_link) {
                        if (col.includes('Satış') || col.includes('Sales')) doctype_link = 'sales-order';
                        else if (col.includes('Material')) doctype_link = 'material-request';
                        else if (col.includes('Purchase')) doctype_link = 'purchase-order';
                        else doctype_link = '';
                    }
                    if (docVal && doctype_link) {
                        val = `<a href="/app/${doctype_link}/${docVal}" target="_blank">${docVal}</a>`;
                    } else {
                        val = docVal;
                    }
                } else if (
                    col === __('Miktar') || col === __('Quantity') || col === 'Miktar' || col === 'Quantity' ||
                    col === __('Kullanılan Miktar') || col === __('Used Qty') || col === 'Kullanılan Miktar' || col === 'Used Qty'
                ) {
                    // Miktar ve Kullanılan Miktar sütunları için daima 2 basamak göster
                    let keyList = colMap[col] || [col.toLowerCase().replace(/ /g,'_')];
                    let miktarVal = '';
                    for (let k of keyList) { if (detail[k] !== undefined && detail[k] !== null) { miktarVal = detail[k]; break; } }
                    if (miktarVal !== '' && !isNaN(Number(miktarVal))) {
                        val = Number(miktarVal).toFixed(2);
                    } else {
                        val = miktarVal;
                    }
                } else {
                    let keyList = colMap[col] || [col.toLowerCase().replace(/ /g,'_')];
                    for (let k of keyList) { if (detail[k] !== undefined && detail[k] !== null) { val = detail[k]; break; } }
                }
                html += `<td>${val || ''}</td>`;
            });
            html += `</tr>`;
        });
    }
    html += `</tbody></table></div>`;
    // --- YENİ: Uzun vadeli/child satır bilgi notu ---
    if (hasLongTerm) {
        html += `<div style='color:#1976d2;font-size:12px;font-style:italic;margin-top:4px;'>Mavi renkli satırlar uzun vadeli (teslim tarihi 30 günden fazla) siparişleri göstermektedir.</div>`;
    }
    if (hasChild) {
        html += `<div style='color:#ff9800;font-size:12px;font-style:italic;margin-top:2px;'>Turuncu renkli satırlar alt (child) siparişleri göstermektedir.</div>`;
    }
    if (hasChildUsage) {
        html += `<div style='color:#ff9800;font-size:12px;font-style:italic;margin-top:2px;'>Turuncu renkli satırlar, ana siparişten child siparişlere aktarılan rezerv miktarını göstermektedir. Toplam rezerv değişmez.</div>`;
    }
    frappe.msgprint({
        title: title,
        indicator: 'blue',
        message: html,
        wide: true
    });
}

function showDocumentDetailsModal(title, details, columns, doctype) {
    showDetailsModal(title, details, columns, doctype);
}

// --- Kullanılan Uzun Vadeli Rezerv Özet Modalı ---
function showLongTermReserveUsageSummaryModal(parent_sales_order) {
    frappe.call({
        method: "uretim_planlama.sales_order_hooks.raw_materials.get_long_term_reserve_usage_summary",
        args: { parent_sales_order },
        callback: function(r) {
            if (!r.message) {
                frappe.show_alert({message: 'Veri bulunamadı.', indicator: 'orange'});
                return;
            }
            let ana_rezerv = parseFloat(r.message.ana_rezerv) || 0;
            let toplam_kullanilan = parseFloat(r.message.toplam_kullanilan) || 0;
            let kalan_rezerv = parseFloat(r.message.kalan_rezerv) || 0;
            let kullanimlar = r.message.kullanimlar || [];
            let modalHtml = `
                <div class="modal fade" id="longTermReserveUsageSummaryModal" tabindex="-1" role="dialog">
                    <div class="modal-dialog modal-lg" role="document">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Uzun Vadeli Rezerv Özeti</h5>
                                <button type="button" class="close" data-dismiss="modal"><span>&times;</span></button>
                            </div>
                            <div class="modal-body">
                                <div class="alert alert-info">
                                    <b>Ana Sipariş:</b> ${parent_sales_order} <br>
                                    <b>Toplam Uzun Vadeli Rezerv:</b> <span style="color:#1976d2;">${ana_rezerv.toFixed(2)}</span><br>
                                    <b>Alt Siparişlerde Kullanılan:</b> <span style="color:#e67e22;">${toplam_kullanilan.toFixed(2)}</span><br>
                                    <b>Kalan Rezerv:</b> <span style="color:#27ae60;">${kalan_rezerv.toFixed(2)}</span>
                                </div>
                                <table class="table table-bordered table-hover">
                                    <thead><tr><th>Alt Sipariş</th><th>Kullanılan Miktar</th><th>Kullanım Tarihi</th></tr></thead>
                                    <tbody>`;
            if (!kullanimlar || kullanimlar.length === 0) {
                modalHtml += `<tr><td colspan="3" style="text-align:center;">Kullanım kaydı yok.</td></tr>`;
            } else {
                kullanimlar.forEach(row => {
                    modalHtml += `<tr><td>${row.sales_order}</td><td>${parseFloat(row.used_qty).toFixed(2)}</td><td>${row.usage_date || ''}</td></tr>`;
                });
            }
            modalHtml += `</tbody></table></div></div></div></div>`;
            if (document.getElementById('longTermReserveUsageSummaryModal')) document.getElementById('longTermReserveUsageSummaryModal').remove();
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            $('#longTermReserveUsageSummaryModal').modal('show');
        }
    });
}