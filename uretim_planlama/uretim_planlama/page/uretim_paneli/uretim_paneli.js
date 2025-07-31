// NOT: Bu dosya, Üretim Planlama Paneli için Frappe JS framework ile hazırlanmıştır.
// Optimize edilmiş performans ile veri çekme, tablo render, filtreleme ve modal desteklidir.

// Global değişkenler
let allPlannedData = []; // Tüm planlanan veriler
let showCompletedItems = false; // Tamamlananları göster/gizle

frappe.pages['uretim-paneli'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Üretim Planlama Paneli',
        single_column: true
    });

    let container = $('<div class="container-fluid"></div>').appendTo(page.body);

    // Sayfa bileşenleri yükleniyor
    initControls(container);
    initSummary(container);
    initFilters(container);
    initTables(container);

    // Sayfa yüklendiğinde otomatik veri çek
    setTimeout(() => loadProductionData(), 100);
};

function initControls(container) {
    const row = $('<div class="row mb-3"></div>').appendTo(container);
    const col = $('<div class="col"></div>').appendTo(row);
    col.append(`
        <button class="btn btn-primary" onclick="loadProductionData()" id="refresh-btn">
            <i class="fa fa-refresh"></i> Verileri Yenile
        </button>
        <span class="ml-3 text-muted" id="debug-status">Hazır</span>
        <div class="spinner-border spinner-border-sm ml-2" id="loading-spinner" style="display:none;"></div>
    `);
}



function initSummary(container) {
    const summaryRow = $('<div class="row mb-3"></div>').appendTo(container);
    const summaryList = [
        { id: 'planlanan-sayisi', class: 'alert-info', label: 'Planlanan', icon: 'fa fa-check-circle' },
        { id: 'planlanmamis-sayisi', class: 'alert-warning', label: 'Planlanmamış', icon: 'fa fa-clock-o' },
        { id: 'toplam-sayisi', class: 'alert-success', label: 'Toplam', icon: 'fa fa-list' },
        { id: 'acil-sayisi', class: 'alert-danger', label: 'Acil', icon: 'fa fa-exclamation-triangle' }
    ];

    summaryList.forEach(s => {
        $('<div class="col-md-3"></div>').append(`
            <div class="alert ${s.class} d-flex align-items-center">
                <i class="${s.icon} mr-2"></i>
                <strong>${s.label}:</strong> 
                <span id="${s.id}" class="ml-1">0</span>
            </div>
        `).appendTo(summaryRow);
    });
}

function initFilters(container) {
    const filterRow = $('<div class="row mb-3"></div>').appendTo(container);
    const filterCol = $('<div class="col"></div>').appendTo(filterRow);

    filterCol.append(`
        <div class="filter-section">
            <div class="d-flex flex-wrap align-items-center" style="gap: 8px;">
                <select id="hafta-filter" class="form-control" style="min-width: 120px; max-width: 120px;">
                    <option value="">Hafta (Tümü)</option>
                </select>
                <input id="opti-no-filter" class="form-control" placeholder="Opti No Ara..." style="min-width: 120px; max-width: 120px;">
                <input id="siparis-no-filter" class="form-control" placeholder="Sipariş No Ara..." style="min-width: 120px; max-width: 120px;">
                <input id="bayi-filter" class="form-control" placeholder="Bayi Ara..." style="min-width: 120px; max-width: 120px;">
                <input id="musteri-filter" class="form-control" placeholder="Müşteri Ara..." style="min-width: 120px; max-width: 120px;">
                <input id="seri-filter" class="form-control" placeholder="Seri Ara..." style="min-width: 120px; max-width: 120px;">
                <input id="renk-filter" class="form-control" placeholder="Renk Ara..." style="min-width: 120px; max-width: 120px;">
                <select id="durum-filter" class="form-control" style="min-width: 140px; max-width: 140px;">
                    <option value="">Acil Durum (Tümü)</option>
                    <option value="ACİL">ACİL</option>
                    <option value="NORMAL">NORMAL</option>
                </select>
                <select id="siparis-durum-filter" class="form-control" style="min-width: 140px; max-width: 140px;">
                    <option value="">Sipariş Durumu (Tümü)</option>
                    <option value="Yeni Sipariş">Yeni Sipariş</option>
                    <option value="Onaylandı">Onaylandı</option>
                    <option value="Draft">Taslak</option>
                    <option value="Pending Approval">Onay Bekliyor</option>
                    <option value="Approved">Onaylandı</option>
                    <option value="Rejected">Reddedildi</option>
                    <option value="Under Review">İncelemede</option>
                    <option value="Pending Finance">Muhasebe Bekliyor</option>
                    <option value="Finance Approved">Muhasebe Onayı</option>
                    <option value="Ready for Production">Üretime Hazır</option>
                    <option value="In Production">Üretimde</option>
                    <option value="Completed">Tamamlandı</option>
                    <option value="To Deliver and Bill">Teslim ve Fatura</option>
                    <option value="To Bill">Fatura</option>
                    <option value="Closed">Kapatıldı</option>
                    <option value="Cancelled">İptal</option>
                </select>
                <button class="btn btn-primary" onclick="loadProductionData(getFilters())" style="white-space: nowrap;">
                    <i class="fa fa-filter"></i> Filtrele
                </button>
                <button class="btn btn-secondary" onclick="clearFilters()" style="white-space: nowrap;">
                    <i class="fa fa-times"></i> Temizle
                </button>
            </div>
        </div>
    `);

    // Hafta seçeneklerini doldur
    const haftaSelect = $('#hafta-filter');
    for (let i = 1; i <= 53; i++) {
        haftaSelect.append(`<option value="${i}">${i}. Hafta</option>`);
    }
    
    // Autocomplete özelliği ekle
    setupAutocomplete();
}

function getFilters() {
    return {
        hafta: $('#hafta-filter').val(),
        opti_no: $('#opti-no-filter').val(),
        siparis_no: $('#siparis-no-filter').val(),
        bayi: $('#bayi-filter').val(),
        musteri: $('#musteri-filter').val(),
        seri: $('#seri-filter').val(),
        renk: $('#renk-filter').val(),
        acil_durum: $('#durum-filter').val(),
        siparis_durum: $('#siparis-durum-filter').val(),
        limit: 200
    };
}

function clearFilters() {
    $('#hafta-filter').val('');
    $('#opti-no-filter').val('');
    $('#siparis-no-filter').val('');
    $('#bayi-filter').val('');
    $('#musteri-filter').val('');
    $('#seri-filter').val('');
    $('#renk-filter').val('');
    $('#durum-filter').val('');
    $('#siparis-durum-filter').val('');
    loadProductionData();
}

function setupAutocomplete() {
    // Bayi autocomplete
    $('#bayi-filter').on('input', function() {
        const searchTerm = $(this).val();
        if (searchTerm.length >= 2) {
            frappe.call({
                method: 'uretim_planlama.uretim_planlama.page.uretim_paneli.uretim_paneli.get_autocomplete_data',
                args: { field: 'bayi', search: searchTerm },
                callback: function(r) {
                    if (r.message) {
                        showAutocompleteDropdown($('#bayi-filter'), r.message);
                    }
                }
            });
        }
    });
    
    // Müşteri autocomplete
    $('#musteri-filter').on('input', function() {
        const searchTerm = $(this).val();
        if (searchTerm.length >= 2) {
            frappe.call({
                method: 'uretim_planlama.uretim_planlama.page.uretim_paneli.uretim_paneli.get_autocomplete_data',
                args: { field: 'musteri', search: searchTerm },
                callback: function(r) {
                    if (r.message) {
                        showAutocompleteDropdown($('#musteri-filter'), r.message);
                    }
                }
            });
        }
    });
    
    // Seri autocomplete
    $('#seri-filter').on('input', function() {
        const searchTerm = $(this).val();
        if (searchTerm.length >= 2) {
            frappe.call({
                method: 'uretim_planlama.uretim_planlama.page.uretim_paneli.uretim_paneli.get_autocomplete_data',
                args: { field: 'seri', search: searchTerm },
                callback: function(r) {
                    if (r.message) {
                        showAutocompleteDropdown($('#seri-filter'), r.message);
                    }
                }
            });
        }
    });
    
    // Renk autocomplete
    $('#renk-filter').on('input', function() {
        const searchTerm = $(this).val();
        if (searchTerm.length >= 2) {
            frappe.call({
                method: 'uretim_planlama.uretim_planlama.page.uretim_paneli.uretim_paneli.get_autocomplete_data',
                args: { field: 'renk', search: searchTerm },
                callback: function(r) {
                    if (r.message) {
                        showAutocompleteDropdown($('#renk-filter'), r.message);
                    }
                }
            });
        }
    });
}

function showAutocompleteDropdown(input, suggestions) {
    // Mevcut dropdown'ı kaldır
    $('.autocomplete-dropdown').remove();
    
    if (suggestions.length === 0) return;
    
    const dropdown = $('<div class="autocomplete-dropdown"></div>');
    dropdown.css({
        position: 'absolute',
        top: input.offset().top + input.outerHeight(),
        left: input.offset().left,
        width: input.outerWidth(),
        maxHeight: '200px',
        overflowY: 'auto',
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '4px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        zIndex: 1000
    });
    
    suggestions.forEach(suggestion => {
        const item = $('<div class="autocomplete-item"></div>');
        item.text(suggestion);
        item.css({
            padding: '8px 12px',
            cursor: 'pointer',
            borderBottom: '1px solid #eee'
        });
        
        item.hover(
            function() { $(this).css('backgroundColor', '#f5f5f5'); },
            function() { $(this).css('backgroundColor', 'white'); }
        );
        
        item.click(function() {
            input.val(suggestion);
            dropdown.remove();
        });
        
        dropdown.append(item);
    });
    
    $('body').append(dropdown);
    
    // Dışarı tıklandığında dropdown'ı kapat
    $(document).on('click.autocomplete', function(e) {
        if (!$(e.target).closest('.autocomplete-dropdown, input').length) {
            dropdown.remove();
            $(document).off('click.autocomplete');
        }
    });
}

function initTables(container) {
    container.append(`
        <div class="card mb-4">
            <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    <span><i class="fa fa-check-circle mr-2"></i><strong>PLANLANAN ÜRETİMLER</strong></span>
                    <button class="btn btn-sm btn-outline-light ml-3" id="toggle-completed-btn" onclick="toggleCompletedItems()">
                        <i class="fa fa-eye-slash"></i> Tamamlananları Göster
                    </button>
                </div>
                <span class="badge badge-light" id="planlanan-count">0</span>
            </div>
            
            <!-- Planlanan Üretimler Özel Filtreleri -->
            <div class="card-body p-2" style="background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;">
                <div class="d-flex flex-wrap align-items-center" style="gap: 8px;">
                    <select id="planlanan-opti-no-filter" class="form-control form-control-sm" style="min-width: 120px; max-width: 120px;">
                        <option value="">Opti No (Tümü)</option>
                    </select>
                    <select id="planlanan-seri-filter" class="form-control form-control-sm" style="min-width: 120px; max-width: 120px;">
                        <option value="">Seri (Tümü)</option>
                    </select>
                    <select id="planlanan-renk-filter" class="form-control form-control-sm" style="min-width: 120px; max-width: 120px;">
                        <option value="">Renk (Tümü)</option>
                    </select>
                    <select id="planlanan-bayi-filter" class="form-control form-control-sm" style="min-width: 120px; max-width: 120px;">
                        <option value="">Bayi (Tümü)</option>
                    </select>
                    <select id="planlanan-musteri-filter" class="form-control form-control-sm" style="min-width: 120px; max-width: 120px;">
                        <option value="">Müşteri (Tümü)</option>
                    </select>
                    <button class="btn btn-sm btn-outline-success" onclick="applyPlannedFilters()">
                        <i class="fa fa-filter"></i> Filtrele
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="clearPlannedFilters()">
                        <i class="fa fa-times"></i> Temizle
                    </button>
                </div>
            </div>
            
            <div class="card-body p-0">
                <div class="table-container" style="max-height: 400px; overflow-y: auto;">
                    <table class="table table-hover mb-0">
                        <thead style="position: sticky; top: 0; z-index: 10; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                            <tr>
                                <th>Hafta</th>
                                <th>Opti No</th>
                                <th>Sipariş</th>
                                <th>Bayi</th>
                                <th>Müşteri</th>
                                <th>Sipariş Tarihi</th>
                                <th>Teslim Tarihi</th>
                                <th>PVC</th>
                                <th>Cam</th>
                                <th>Toplam MTUL/m²</th>
                                <th>Planlanan Başlangıç</th>
                                <th>Seri</th>
                                <th>Renk</th>
                                <th>Açıklama</th>
                                <th>Acil</th>
                            </tr>
                        </thead>
                        <tbody id="planlanan-tbody">
                            <tr><td colspan="15" class="text-center text-muted">Veri yükleniyor...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header bg-warning text-dark d-flex justify-content-between align-items-center">
                <span><i class="fa fa-clock-o mr-2"></i><strong>PLANLANMAMIŞ SİPARİŞLER</strong></span>
                <span class="badge badge-light" id="planlanmamis-count">0</span>
            </div>
            
            <!-- Planlanmamış Siparişler Özel Filtreleri -->
            <div class="card-body p-2" style="background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;">
                <div class="d-flex flex-wrap align-items-center" style="gap: 8px;">
                    <select id="planlanmamis-siparis-durum-filter" class="form-control form-control-sm" style="min-width: 140px; max-width: 140px;">
                        <option value="">Durum (Tümü)</option>
                        <option value="Yeni Sipariş">Yeni Sipariş</option>
                        <option value="Onaylandı">Onaylandı</option>
                        <option value="Draft">Taslak</option>
                        <option value="Pending Approval">Onay Bekliyor</option>
                        <option value="Approved">Onaylandı</option>
                        <option value="Rejected">Reddedildi</option>
                        <option value="Under Review">İncelemede</option>
                        <option value="Pending Finance">Muhasebe Bekliyor</option>
                        <option value="Finance Approved">Muhasebe Onayı</option>
                        <option value="Ready for Production">Üretime Hazır</option>
                        <option value="In Production">Üretimde</option>
                        <option value="Completed">Tamamlandı</option>
                        <option value="To Deliver and Bill">Teslim ve Fatura</option>
                        <option value="To Bill">Fatura</option>
                        <option value="Closed">Kapatıldı</option>
                        <option value="Cancelled">İptal</option>
                    </select>
                    <select id="planlanmamis-seri-filter" class="form-control form-control-sm" style="min-width: 120px; max-width: 120px;">
                        <option value="">Seri (Tümü)</option>
                    </select>
                    <select id="planlanmamis-renk-filter" class="form-control form-control-sm" style="min-width: 120px; max-width: 120px;">
                        <option value="">Renk (Tümü)</option>
                    </select>
                    <select id="planlanmamis-bayi-filter" class="form-control form-control-sm" style="min-width: 120px; max-width: 120px;">
                        <option value="">Bayi (Tümü)</option>
                    </select>
                    <select id="planlanmamis-musteri-filter" class="form-control form-control-sm" style="min-width: 120px; max-width: 120px;">
                        <option value="">Müşteri (Tümü)</option>
                    </select>
                    <button class="btn btn-sm btn-outline-warning" onclick="applyUnplannedFilters()">
                        <i class="fa fa-filter"></i> Filtrele
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="clearUnplannedFilters()">
                        <i class="fa fa-times"></i> Temizle
                    </button>
                </div>
            </div>
            
            <div class="card-body p-0">
                <div class="table-container" style="max-height: 400px; overflow-y: auto;">
                    <table class="table table-hover mb-0">
                        <thead style="position: sticky; top: 0; z-index: 10; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                            <tr>
                                <th>Sipariş</th>
                                <th>Bayi</th>
                                <th>Müşteri</th>
                                <th>Sipariş Tarihi</th>
                                <th>Teslim Tarihi</th>
                                <th>Durum</th>
                                <th>MLY</th>
                                <th>Kısmi Planlama</th>
                                <th>PVC</th>
                                <th>Cam</th>
                                <th>Seri</th>
                                <th>Renk</th>
                                <th>Açıklama</th>
                                <th>Acil</th>
                            </tr>
                        </thead>
                        <tbody id="planlanmamis-tbody">
                            <tr><td colspan="14" class="text-center text-muted">Veri yükleniyor...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `);
}

function loadProductionData(filters = {}) {
    // Loading durumunu göster
    $('#refresh-btn').prop('disabled', true);
    $('#loading-spinner').show();
    $('#debug-status').text('Veriler yükleniyor...');

    // Tabloları temizle
    $('#planlanan-tbody').html('<tr><td colspan="15" class="text-center text-muted">Yükleniyor...</td></tr>');
    $('#planlanmamis-tbody').html('<tr><td colspan="14" class="text-center text-muted">Yükleniyor...</td></tr>');

    frappe.call({
        method: 'uretim_planlama.uretim_planlama.page.uretim_paneli.uretim_paneli.get_production_planning_data',
        args: { filters: JSON.stringify(filters) },
        callback: function(r) {
            console.log('DEBUG: Server response:', r);
            $('#refresh-btn').prop('disabled', false);
            $('#loading-spinner').hide();
            
            if (r.exc) {
                console.error('DEBUG: Server exception:', r.exc);
                showError('Veri yükleme hatası: ' + r.exc);
                $('#debug-status').text('Hata oluştu');
                return;
            }

            const data = r.message || r;
            console.log('DEBUG: Data received:', data);
            console.log('DEBUG: Planned data count:', data.planned ? data.planned.length : 0);
            console.log('DEBUG: Unplanned data count:', data.unplanned ? data.unplanned.length : 0);
            
            if (data.planned && data.planned.length > 0) {
                console.log('DEBUG: First planned item:', data.planned[0]);
            }
            if (data.unplanned && data.unplanned.length > 0) {
                console.log('DEBUG: First unplanned item:', data.unplanned[0]);
            }
            
            // Tüm planlanan verileri sakla
            if (data.planned) {
                allPlannedData = data.planned;
                const filteredPlannedData = filterCompletedItems(data.planned);
                renderTableRows('planlanan-tbody', filteredPlannedData);
                updateSummary({ planned: filteredPlannedData, unplanned: data.unplanned || [] });
            } else {
                updateSummary(data);
                renderTableRows('planlanan-tbody', []);
            }
            
            // Planlanmamış verileri sakla ve göster
            if (data.unplanned) {
                window.currentUnplannedData = data.unplanned;
                console.log('DEBUG: Planlanmamış veriler:', data.unplanned.slice(0, 3)); // İlk 3 veriyi göster
                renderTableRows('planlanmamis-tbody', data.unplanned);
            } else {
                window.currentUnplannedData = [];
                renderTableRows('planlanmamis-tbody', []);
            }
            
            // Tablo filtrelerini doldur
            populateTableFilters(data.planned || [], data.unplanned || []);
            
            $('#debug-status').text(`Yüklendi (${(data.planned || []).length + (data.unplanned || []).length} kayıt)`);
        },
        error: function(err) {
            $('#refresh-btn').prop('disabled', false);
            $('#loading-spinner').hide();
            showError('Bağlantı hatası: ' + err);
            $('#debug-status').text('Bağlantı hatası');
        }
    });
}

function updateSummary(data) {
    const planned = data.planned || [];
    const unplanned = data.unplanned || [];
    const total = planned.length + unplanned.length;
    
    // Acil durumu hesapla (teslim tarihi bugünden önce olanlar)
    const today = new Date();
    const acilCount = [...planned, ...unplanned].filter(item => {
        if (!item.bitis_tarihi) return false;
        const bitisDate = new Date(item.bitis_tarihi);
        return bitisDate < today;
    }).length;

    $('#planlanan-sayisi').text(planned.length);
    $('#planlanmamis-sayisi').text(unplanned.length);
    $('#toplam-sayisi').text(total);
    $('#acil-sayisi').text(acilCount);
    
    $('#planlanan-count').text(planned.length);
    $('#planlanmamis-count').text(unplanned.length);
}

function filterCompletedItems(plannedData) {
    if (showCompletedItems) {
        return plannedData; // Tüm verileri göster
    } else {
        // Tamamlananları filtrele (teslim tarihi bugünden önce olanlar)
        const today = new Date();
        return plannedData.filter(item => {
            if (!item.bitis_tarihi) return true; // Teslim tarihi yoksa göster
            const bitisDate = new Date(item.bitis_tarihi);
            return bitisDate >= today; // Bugün ve sonrası için göster
        });
    }
}

function toggleCompletedItems() {
    showCompletedItems = !showCompletedItems;
    
    const btn = $('#toggle-completed-btn');
    const icon = btn.find('i');
    const text = btn.text();
    
    if (showCompletedItems) {
        btn.html('<i class="fa fa-eye"></i> Tamamlananları Gizle');
        btn.removeClass('btn-outline-light').addClass('btn-light');
    } else {
        btn.html('<i class="fa fa-eye-slash"></i> Tamamlananları Göster');
        btn.removeClass('btn-light').addClass('btn-outline-light');
    }
    
    // Tabloyu yeniden render et
    const filteredData = filterCompletedItems(allPlannedData);
    renderTableRows('planlanan-tbody', filteredData);
    updateSummary({ planned: filteredData, unplanned: [] });
    $('#planlanan-count').text(filteredData.length);
}



function renderTableRows(tbodyId, rows) {
    const tbody = $(`#${tbodyId}`);
    tbody.empty();
    
    if (!rows || rows.length === 0) {
        const colSpan = tbodyId === 'planlanan-tbody' ? 15 : 14;
        tbody.append(`<tr><td colspan="${colSpan}" class="text-center text-muted">Veri bulunamadı</td></tr>`);
        return;
    }

    // DocumentFragment kullanarak performansı artır
    const fragment = document.createDocumentFragment();
    
    rows.forEach(item => {
        // PVC/Cam renk ayrımı için satır arka plan rengini belirle
        const pvcCount = parseFloat(item.pvc_count || 0);
        const camCount = parseFloat(item.cam_count || 0);
        const isUrgent = item.acil == 1;
        
        // Hem PVC hem Cam varsa, iki ayrı satır oluştur
        if (pvcCount > 0 && camCount > 0) {
            // PVC Satırı
            const pvcRow = document.createElement('tr');
            pvcRow.className = 'cursor-pointer';
            pvcRow.setAttribute('style', 'background-color: #ffe6e6; border-left: 4px solid #dc3545;');
            pvcRow.onclick = () => showOrderDetailsModal(item);
            
            if (tbodyId === 'planlanan-tbody') {
                pvcRow.innerHTML = `
                    <td><span class="badge badge-info" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.hafta || '-'}</span></td>
                    <td><strong>${item.opti_no || truncateText(item.uretim_plani || '-', 15)}</strong></td>
                    <td><strong>${item.sales_order || '-'} <span class="badge badge-danger" style="font-size: 10px;">PVC</span></strong></td>
                    <td>${truncateText(item.bayi || '-', 20)}</td>
                    <td>${truncateText(item.musteri || '-', 25)}</td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #ffc107; color: #000; border: 2px solid #ffc107;">${formatDate(item.siparis_tarihi)}</span></td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #e91e63; color: #fff; border: 2px solid #e91e63;">${formatDate(item.bitis_tarihi)}</span></td>
                    <td><span class="badge badge-danger" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.pvc_count || '0'}</span></td>
                    <td><span class="badge badge-secondary" style="border-radius: 4px; font-weight: bold; font-size: 12px;">0</span></td>
                    <td><span class="badge badge-success" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #28a745; color: #fff; border: 2px solid #28a745;">${item.toplam_mtul_m2 ? item.toplam_mtul_m2.toFixed(2) : '0.00'}</span></td>
                    <td><span class="badge badge-info" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #6f42c1; color: #fff; border: 2px solid #6f42c1;">${formatDate(item.planlanan_baslangic_tarihi)}</span></td>
                    <td>${item.seri || '-'}</td>
                    <td>${item.renk || '-'}</td>
                    <td>${truncateText(item.aciklama || '-', 30)}</td>
                    <td>${isUrgent ? '<span class="badge badge-danger" style="border-radius: 4px; font-weight: bold; background-color: #dc3545; color: #fff; border: 2px solid #dc3545; font-size: 12px;">ACİL</span>' : '<span class="badge badge-success" style="border-radius: 4px; font-weight: bold; background-color: #28a745; color: #fff; border: 2px solid #28a745; font-size: 12px;">NORMAL</span>'}</td>
                `;
            } else {
                const statusBadge = getSalesOrderStatusBadge(item);
                const mlyBadge = item.mly_dosyasi_var ? 
                    '<span class="badge badge-success" style="border-radius: 4px; font-weight: bold; font-size: 10px; background-color: #28a745; color: #fff; border: 2px solid #28a745;">MLY</span>' : 
                    '<span class="badge badge-secondary" style="border-radius: 4px; font-weight: bold; font-size: 10px; background-color: #6c757d; color: #fff; border: 2px solid #6c757d;">YOK</span>';
                const kismiPlanlamaBadge = item.kismi_planlama ? 
                    '<span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 10px; background-color: #ffc107; color: #000; border: 2px solid #ffc107;">KISMİ</span>' : 
                    '<span class="badge badge-info" style="border-radius: 4px; font-weight: bold; font-size: 10px; background-color: #17a2b8; color: #fff; border: 2px solid #17a2b8;">TAM</span>';
                
                pvcRow.innerHTML = `
                    <td><strong>${item.sales_order || '-'} <span class="badge badge-danger" style="font-size: 10px;">PVC</span></strong></td>
                    <td>${truncateText(item.bayi || '-', 20)}</td>
                    <td>${truncateText(item.musteri || '-', 25)}</td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #ffc107; color: #000; border: 2px solid #ffc107;">${formatDate(item.siparis_tarihi)}</span></td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #e91e63; color: #fff; border: 2px solid #e91e63;">${formatDate(item.bitis_tarihi)}</span></td>
                    <td><span class="badge" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: ${statusBadge.bg}; color: ${statusBadge.color}; border: 2px solid ${statusBadge.bg};">${statusBadge.label}</span></td>
                    <td>${mlyBadge}</td>
                    <td>${kismiPlanlamaBadge}</td>
                    <td><span class="badge badge-danger" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.pvc_count || '0'}</span></td>
                    <td><span class="badge badge-secondary" style="border-radius: 4px; font-weight: bold; font-size: 12px;">0</span></td>
                    <td>${item.seri || '-'}</td>
                    <td>${item.renk || '-'}</td>
                    <td>${truncateText(item.aciklama || '-', 30)}</td>
                    <td>${isUrgent ? '<span class="badge badge-danger" style="border-radius: 4px; font-weight: bold; background-color: #dc3545; color: #fff; border: 2px solid #dc3545; font-size: 12px;">ACİL</span>' : '<span class="badge badge-success" style="border-radius: 4px; font-weight: bold; background-color: #28a745; color: #fff; border: 2px solid #28a745; font-size: 12px;">NORMAL</span>'}</td>
                `;
            }
            fragment.appendChild(pvcRow);
            
            // Cam Satırı
            const camRow = document.createElement('tr');
            camRow.className = 'cursor-pointer';
            camRow.setAttribute('style', 'background-color: #e6f3ff; border-left: 4px solid #007bff;');
            camRow.onclick = () => showOrderDetailsModal(item);
            
            if (tbodyId === 'planlanan-tbody') {
                camRow.innerHTML = `
                    <td><span class="badge badge-info" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.hafta || '-'}</span></td>
                    <td><strong>${item.opti_no || truncateText(item.uretim_plani || '-', 15)}</strong></td>
                    <td><strong>${item.sales_order || '-'} <span class="badge badge-primary" style="font-size: 10px;">CAM</span></strong></td>
                    <td>${truncateText(item.bayi || '-', 20)}</td>
                    <td>${truncateText(item.musteri || '-', 25)}</td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #ffc107; color: #000; border: 2px solid #ffc107;">${formatDate(item.siparis_tarihi)}</span></td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #e91e63; color: #fff; border: 2px solid #e91e63;">${formatDate(item.bitis_tarihi)}</span></td>
                    <td><span class="badge badge-secondary" style="border-radius: 4px; font-weight: bold; font-size: 12px;">0</span></td>
                    <td><span class="badge badge-primary" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.cam_count || '0'}</span></td>
                    <td><span class="badge badge-success" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #28a745; color: #fff; border: 2px solid #28a745;">${item.toplam_mtul_m2 ? item.toplam_mtul_m2.toFixed(2) : '0.00'}</span></td>
                    <td><span class="badge badge-info" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #6f42c1; color: #fff; border: 2px solid #6f42c1;">${formatDate(item.planlanan_baslangic_tarihi)}</span></td>
                    <td>${item.seri || '-'}</td>
                    <td>${item.renk || '-'}</td>
                    <td>${truncateText(item.aciklama || '-', 30)}</td>
                    <td>${isUrgent ? '<span class="badge badge-danger" style="border-radius: 4px; font-weight: bold; background-color: #dc3545; color: #fff; border: 2px solid #dc3545; font-size: 12px;">ACİL</span>' : '<span class="badge badge-success" style="border-radius: 4px; font-weight: bold; background-color: #28a745; color: #fff; border: 2px solid #28a745; font-size: 12px;">NORMAL</span>'}</td>
                `;
            } else {
                camRow.innerHTML = `
                    <td><strong>${item.sales_order || '-'} <span class="badge badge-primary" style="font-size: 10px;">CAM</span></strong></td>
                    <td>${truncateText(item.bayi || '-', 20)}</td>
                    <td>${truncateText(item.musteri || '-', 25)}</td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #ffc107; color: #000; border: 2px solid #ffc107;">${formatDate(item.siparis_tarihi)}</span></td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #e91e63; color: #fff; border: 2px solid #e91e63;">${formatDate(item.bitis_tarihi)}</span></td>
                    <td><span class="badge" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: ${statusBadge.bg}; color: ${statusBadge.color}; border: 2px solid ${statusBadge.bg};">${statusBadge.label}</span></td>
                    <td>${mlyBadge}</td>
                    <td>${kismiPlanlamaBadge}</td>
                    <td><span class="badge badge-secondary" style="border-radius: 4px; font-weight: bold; font-size: 12px;">0</span></td>
                    <td><span class="badge badge-primary" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.cam_count || '0'}</span></td>
                    <td>${item.seri || '-'}</td>
                    <td>${item.renk || '-'}</td>
                    <td>${truncateText(item.aciklama || '-', 30)}</td>
                    <td>${isUrgent ? '<span class="badge badge-danger" style="border-radius: 4px; font-weight: bold; background-color: #dc3545; color: #fff; border: 2px solid #dc3545; font-size: 12px;">ACİL</span>' : '<span class="badge badge-success" style="border-radius: 4px; font-weight: bold; background-color: #28a745; color: #fff; border: 2px solid #28a745; font-size: 12px;">NORMAL</span>'}</td>
                `;
            }
            fragment.appendChild(camRow);
        } else {
            // Tek ürün türü varsa normal satır oluştur
            const row = document.createElement('tr');
            row.className = 'cursor-pointer';
            row.onclick = () => showOrderDetailsModal(item);
            
            let rowStyle = '';
            if (pvcCount > 0 && camCount === 0) {
                // Sadece PVC varsa - açık kırmızı arka plan
                rowStyle = 'background-color: #ffe6e6; border-left: 4px solid #dc3545;';
            } else if (camCount > 0 && pvcCount === 0) {
                // Sadece Cam varsa - açık mavi arka plan
                rowStyle = 'background-color: #e6f3ff; border-left: 4px solid #007bff;';
            }
            
            row.setAttribute('style', rowStyle);
            
            if (tbodyId === 'planlanan-tbody') {
                row.innerHTML = `
                    <td><span class="badge badge-info" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.hafta || '-'}</span></td>
                    <td><strong>${item.opti_no || truncateText(item.uretim_plani || '-', 15)}</strong></td>
                    <td><strong>${item.sales_order || '-'}</strong></td>
                    <td>${truncateText(item.bayi || '-', 20)}</td>
                    <td>${truncateText(item.musteri || '-', 25)}</td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #ffc107; color: #000; border: 2px solid #ffc107;">${formatDate(item.siparis_tarihi)}</span></td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #e91e63; color: #fff; border: 2px solid #e91e63;">${formatDate(item.bitis_tarihi)}</span></td>
                    <td><span class="badge badge-danger" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.pvc_count || '0'}</span></td>
                    <td><span class="badge badge-primary" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.cam_count || '0'}</span></td>
                    <td><span class="badge badge-success" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #28a745; color: #fff; border: 2px solid #28a745;">${item.toplam_mtul_m2 ? item.toplam_mtul_m2.toFixed(2) : '0.00'}</span></td>
                    <td><span class="badge badge-info" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #6f42c1; color: #fff; border: 2px solid #6f42c1;">${formatDate(item.planlanan_baslangic_tarihi)}</span></td>
                    <td>${item.seri || '-'}</td>
                    <td>${item.renk || '-'}</td>
                    <td>${truncateText(item.aciklama || '-', 30)}</td>
                    <td>${isUrgent ? '<span class="badge badge-danger" style="border-radius: 4px; font-weight: bold; background-color: #dc3545; color: #fff; border: 2px solid #dc3545; font-size: 12px;">ACİL</span>' : '<span class="badge badge-success" style="border-radius: 4px; font-weight: bold; background-color: #28a745; color: #fff; border: 2px solid #28a745; font-size: 12px;">NORMAL</span>'}</td>
                `;
            } else {
                const statusBadge = getSalesOrderStatusBadge(item);
                
                // MLY dosyası badge'i
                const mlyBadge = item.mly_dosyasi_var ? 
                    '<span class="badge badge-success" style="border-radius: 4px; font-weight: bold; font-size: 10px; background-color: #28a745; color: #fff; border: 2px solid #28a745;">MLY</span>' : 
                    '<span class="badge badge-secondary" style="border-radius: 4px; font-weight: bold; font-size: 10px; background-color: #6c757d; color: #fff; border: 2px solid #6c757d;">YOK</span>';
                
                // Kısmi planlama badge'i
                const kismiPlanlamaBadge = item.kismi_planlama ? 
                    '<span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 10px; background-color: #ffc107; color: #000; border: 2px solid #ffc107;">KISMİ</span>' : 
                    '<span class="badge badge-info" style="border-radius: 4px; font-weight: bold; font-size: 10px; background-color: #17a2b8; color: #fff; border: 2px solid #17a2b8;">TAM</span>';
                
                row.innerHTML = `
                    <td><strong>${item.sales_order || '-'}</strong></td>
                    <td>${truncateText(item.bayi || '-', 20)}</td>
                    <td>${truncateText(item.musteri || '-', 25)}</td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #ffc107; color: #000; border: 2px solid #ffc107;">${formatDate(item.siparis_tarihi)}</span></td>
                    <td><span class="badge badge-warning" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: #e91e63; color: #fff; border: 2px solid #e91e63;">${formatDate(item.bitis_tarihi)}</span></td>
                    <td><span class="badge" style="border-radius: 4px; font-weight: bold; font-size: 12px; background-color: ${statusBadge.bg}; color: ${statusBadge.color}; border: 2px solid ${statusBadge.bg};">${statusBadge.label}</span></td>
                    <td>${mlyBadge}</td>
                    <td>${kismiPlanlamaBadge}</td>
                    <td><span class="badge badge-danger" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.pvc_count || '0'}</span></td>
                    <td><span class="badge badge-primary" style="border-radius: 4px; font-weight: bold; font-size: 12px;">${item.cam_count || '0'}</span></td>
                    <td>${item.seri || '-'}</td>
                    <td>${item.renk || '-'}</td>
                    <td>${truncateText(item.aciklama || '-', 30)}</td>
                    <td>${isUrgent ? '<span class="badge badge-danger" style="border-radius: 4px; font-weight: bold; background-color: #dc3545; color: #fff; border: 2px solid #dc3545; font-size: 12px;">ACİL</span>' : '<span class="badge badge-success" style="border-radius: 4px; font-weight: bold; background-color: #28a745; color: #fff; border: 2px solid #28a745; font-size: 12px;">NORMAL</span>'}</td>
                `;
            }
            
            fragment.appendChild(row);
        }
    });
    
    tbody.append(fragment);
}

function truncateText(text, maxLength) {
    if (!text) return '-';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('tr-TR');
    } catch (e) {
        return dateStr;
    }
}

function showError(message) {
    frappe.msgprint({
        title: 'Hata',
        message: message,
        indicator: 'red'
    });
}

function showOrderDetailsModal(item) {
    // Planlanan üretimler için özel modal
    if (item.uretim_plani) {
        const modal = $(`
            <div class="modal fade" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title">
                                <i class="fa fa-check-circle mr-2"></i>Planlanan Üretim Detayları
                            </h5>
                            <button type="button" class="close text-white" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6><i class="fa fa-shopping-cart mr-2"></i>Sipariş Bilgileri</h6>
                                    <table class="table table-sm table-bordered">
                                        <tr><td><strong>Sipariş No:</strong></td><td><span class="badge badge-primary">${item.sales_order || '-'}</span></td></tr>
                                        <tr><td><strong>Bayi:</strong></td><td>${item.bayi || '-'}</td></tr>
                                        <tr><td><strong>Müşteri:</strong></td><td>${item.musteri || '-'}</td></tr>
                                        <tr><td><strong>Hafta:</strong></td><td><span class="badge badge-info">${item.hafta || '-'}</span></td></tr>
                                        <tr><td><strong>Planlanan Miktar:</strong></td><td><span class="badge badge-success">${item.adet || '0'}</span></td></tr>
                                        <tr><td><strong>Sipariş Tarihi:</strong></td><td>${formatDate(item.siparis_tarihi)}</td></tr>
                                        <tr><td><strong>Teslim Tarihi:</strong></td><td>${formatDate(item.bitis_tarihi)}</td></tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <h6><i class="fa fa-cogs mr-2"></i>Üretim Bilgileri</h6>
                                    <table class="table table-sm table-bordered">
                                        <tr><td><strong>Üretim Planı:</strong></td><td><span class="badge badge-success">${item.uretim_plani || '-'}</span></td></tr>
                                        <tr><td><strong>Opti No:</strong></td><td><span class="badge badge-warning">${item.opti_no || '-'}</span></td></tr>
                                        <tr><td><strong>Seri:</strong></td><td>${item.seri || '-'}</td></tr>
                                        <tr><td><strong>Renk:</strong></td><td>${item.renk || '-'}</td></tr>
                                        <tr><td><strong>PVC:</strong></td><td><span class="badge badge-danger">${item.pvc_count || '0'}</span></td></tr>
                                        <tr><td><strong>Cam:</strong></td><td><span class="badge badge-primary">${item.cam_count || '0'}</span></td></tr>
                                        <tr><td><strong>Toplam MTUL/m²:</strong></td><td><span class="badge badge-info">${item.toplam_mtul_m2 ? item.toplam_mtul_m2.toFixed(2) : '0.00'}</span></td></tr>
                                        <tr><td><strong>Planlanan Başlangıç:</strong></td><td>${formatDate(item.planlanan_baslangic_tarihi)}</td></tr>
                                    </table>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <h6><i class="fa fa-exclamation-triangle mr-2"></i>Acil Durum</h6>
                                    <div class="alert ${item.acil ? 'alert-danger' : 'alert-success'}">
                                        <strong>${item.acil ? 'ACİL' : 'NORMAL'}</strong>
                                        ${item.acil ? ' - Bu sipariş acil olarak işaretlenmiş' : ' - Bu sipariş normal durumda'}
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6><i class="fa fa-comment mr-2"></i>Açıklama</h6>
                                    <div class="alert alert-info">
                                        <p class="mb-0">${item.aciklama || 'Açıklama bulunmuyor'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-success" onclick="window.open('/app/sales-order/${item.sales_order}', '_blank')">
                                <i class="fa fa-external-link mr-2"></i>Siparişi Aç
                            </button>
                            <button type="button" class="btn btn-info" onclick="window.open('/app/production-plan/${item.uretim_plani}', '_blank')">
                                <i class="fa fa-cogs mr-2"></i>Üretim Planını Aç
                            </button>
                            <button type="button" class="btn btn-warning" onclick="showWorkOrders('${item.sales_order}')">
                                <i class="fa fa-tasks mr-2"></i>İş Emirleri
                            </button>
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Kapat</button>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        modal.modal('show');
    } else {
        // Planlanmamış siparişler için mevcut modal
        const modal = $(`
            <div class="modal fade" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-warning text-dark">
                            <h5 class="modal-title">
                                <i class="fa fa-clock-o mr-2"></i>Planlanmamış Sipariş Detayları
                            </h5>
                            <button type="button" class="close" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6><i class="fa fa-shopping-cart mr-2"></i>Sipariş Bilgileri</h6>
                                    <table class="table table-sm table-bordered">
                                        <tr><td><strong>Sipariş No:</strong></td><td><span class="badge badge-primary">${item.sales_order || '-'}</span></td></tr>
                                        <tr><td><strong>Bayi:</strong></td><td>${item.bayi || '-'}</td></tr>
                                        <tr><td><strong>Müşteri:</strong></td><td>${item.musteri || '-'}</td></tr>
                                        <tr><td><strong>Hafta:</strong></td><td><span class="badge badge-info">${item.hafta || '-'}</span></td></tr>
                                        <tr><td><strong>Kalan Miktar:</strong></td><td><span class="badge badge-warning">${item.adet || '0'}</span></td></tr>
                                        <tr><td><strong>Sipariş Tarihi:</strong></td><td>${formatDate(item.siparis_tarihi)}</td></tr>
                                        <tr><td><strong>Teslim Tarihi:</strong></td><td>${formatDate(item.bitis_tarihi)}</td></tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <h6><i class="fa fa-cogs mr-2"></i>Ürün Bilgileri</h6>
                                    <table class="table table-sm table-bordered">
                                        <tr><td><strong>Ürün Kodu:</strong></td><td>${item.item_code || '-'}</td></tr>
                                        <tr><td><strong>Seri:</strong></td><td>${item.seri || '-'}</td></tr>
                                        <tr><td><strong>Renk:</strong></td><td>${item.renk || '-'}</td></tr>
                                        <tr><td><strong>PVC:</strong></td><td><span class="badge badge-danger">${item.pvc_count || '0'}</span></td></tr>
                                        <tr><td><strong>Cam:</strong></td><td><span class="badge badge-primary">${item.cam_count || '0'}</span></td></tr>
                                        <tr><td><strong>Durum:</strong></td><td><span class="badge badge-warning">Planlanmamış</span></td></tr>
                                    </table>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <h6><i class="fa fa-exclamation-triangle mr-2"></i>Acil Durum</h6>
                                    <div class="alert ${item.acil ? 'alert-danger' : 'alert-success'}">
                                        <strong>${item.acil ? 'ACİL' : 'NORMAL'}</strong>
                                        ${item.acil ? ' - Bu sipariş acil olarak işaretlenmiş' : ' - Bu sipariş normal durumda'}
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6><i class="fa fa-comment mr-2"></i>Açıklama</h6>
                                    <div class="alert alert-info">
                                        <p class="mb-0">${item.aciklama || 'Açıklama bulunmuyor'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-success" onclick="window.open('/app/sales-order/${item.sales_order}', '_blank')">
                                <i class="fa fa-external-link mr-2"></i>Siparişi Aç
                            </button>
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Kapat</button>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        modal.modal('show');
    }
}

function showWorkOrders(salesOrder) {
    console.log('showWorkOrders çağrıldı:', salesOrder);
    
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.api.get_sales_order_work_orders',
        args: { sales_order: salesOrder },
        callback: function(r) {
            console.log('API yanıtı:', r);
            
            if (r.message && r.message.length > 0) {
                console.log('İş emirleri bulundu:', r.message.length);
                showWorkOrdersModal(salesOrder, r.message);
            } else {
                console.log('İş emri bulunamadı');
                frappe.msgprint({
                    title: 'Bilgi',
                    message: 'Bu sipariş için iş emri bulunamadı.',
                    indicator: 'blue'
                });
            }
        },
        error: function(err) {
            console.error('API hatası:', err);
            frappe.msgprint({
                title: 'Hata',
                message: 'İş emirleri yüklenirken bir hata oluştu.',
                indicator: 'red'
            });
        }
    });
}

function showWorkOrdersModal(salesOrder, workOrders) {
    let html = `
        <div class="row">
            <div class="col-12">
                <h6><i class="fa fa-tasks mr-2"></i>İş Emirleri Detayları</h6>
                <p><strong>Sipariş No:</strong> ${salesOrder}</p>
            </div>
        </div>
        <div class="row">
            <div class="col-12">
                <div class="table-responsive">
                    <table class="table table-sm table-bordered">
                        <thead class="thead-light">
                            <tr>
                                <th style="width: 50px;"></th>
                                <th>İş Emri</th>
                                <th>Durum</th>
                                <th>Miktar</th>
                                <th>Üretilen</th>
                                <th>Planlanan Başlangıç</th>
                                <th>Planlanan Bitiş</th>
                            </tr>
                        </thead>
                        <tbody>`;
    
    workOrders.forEach((wo, index) => {
        const statusBadge = getStatusBadge(wo.status);
        const hasOperations = wo.operations && wo.operations.length > 0;
        const collapseId = `collapse-wo-${index}`;
        
        html += `
            <tr class="work-order-row">
                <td>
                    ${hasOperations ? `<button class="btn btn-sm btn-outline-primary toggle-operations" data-toggle="collapse" data-target="#${collapseId}" aria-expanded="false" aria-controls="${collapseId}">
                        <i class="fa fa-chevron-down"></i>
                    </button>` : ''}
                </td>
                <td>
                    <a href="/app/work-order/${wo.name}" target="_blank" class="text-primary font-weight-bold">
                        ${wo.name}
                    </a>
                </td>
                <td>
                    <span class="badge" style="background-color: ${statusBadge.bg}; color: ${statusBadge.color};">
                        ${statusBadge.label}
                    </span>
                </td>
                <td>${wo.qty || '0'}</td>
                <td>${wo.produced_qty || '0'}</td>
                <td>${formatDate(wo.planned_start_date)}</td>
                <td>${formatDate(wo.planned_end_date)}</td>
            </tr>`;
        
        // Operasyonları açılır-kapanır olarak ekle
        if (hasOperations) {
            html += `
                <tr class="operations-row">
                    <td colspan="7" class="p-0">
                        <div class="collapse" id="${collapseId}">
                            <div class="card card-body m-2" style="background-color: #f8f9fa; border: 1px solid #dee2e6;">
                                <h6 class="mb-3"><i class="fa fa-cogs mr-2"></i>Operasyonlar</h6>
                                <div class="table-responsive">
                                    <table class="table table-sm table-bordered">
                                        <thead class="thead-light">
                                            <tr>
                                                <th>Operasyon</th>
                                                <th>İş İstasyonu</th>
                                                <th>Durum</th>
                                                <th>Tamamlanan</th>
                                                <th>Planlanan Başlangıç</th>
                                                <th>Planlanan Bitiş</th>
                                                <th>Fiili Başlangıç</th>
                                                <th>Fiili Bitiş</th>
                                            </tr>
                                        </thead>
                                        <tbody>`;
            
            wo.operations.forEach(op => {
                const opStatusBadge = getStatusBadge(op.status);
                html += `
                    <tr>
                        <td><strong>${op.operation || '-'}</strong></td>
                        <td>${op.workstation || '-'}</td>
                        <td>
                            <span class="badge badge-sm" style="background-color: ${opStatusBadge.bg}; color: ${opStatusBadge.color};">
                                ${opStatusBadge.label}
                            </span>
                        </td>
                        <td>${op.completed_qty || '0'}</td>
                        <td>${formatDate(op.planned_start_time)}</td>
                        <td>${formatDate(op.planned_end_time)}</td>
                        <td>${formatDate(op.actual_start_time)}</td>
                        <td>${formatDate(op.actual_end_time)}</td>
                    </tr>`;
            });
            
            html += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>`;
        }
    });
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>`;
    
    const modal = $(`
        <div class="modal fade" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title">
                            <i class="fa fa-tasks mr-2"></i>İş Emirleri Detayları
                        </h5>
                        <button type="button" class="close" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        ${html}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Kapat</button>
                    </div>
                </div>
            </div>
        </div>
    `);
    
    modal.modal('show');
    
    // Toggle butonları için event listener ekle
    modal.on('click', '.toggle-operations', function() {
        const icon = $(this).find('i');
        if (icon.hasClass('fa-chevron-down')) {
            icon.removeClass('fa-chevron-down').addClass('fa-chevron-up');
        } else {
            icon.removeClass('fa-chevron-up').addClass('fa-chevron-down');
        }
    });
}

function getStatusBadge(status) {
    const statusMap = {
        'Draft': { label: 'Taslak', bg: '#6c757d', color: '#fff' },
        'Not Started': { label: 'Başlamadı', bg: '#ffc107', color: '#000' },
        'In Process': { label: 'İşlemde', bg: '#17a2b8', color: '#fff' },
        'Completed': { label: 'Tamamlandı', bg: '#28a745', color: '#fff' },
        'Stopped': { label: 'Durduruldu', bg: '#dc3545', color: '#fff' },
        'Closed': { label: 'Kapatıldı', bg: '#6c757d', color: '#fff' },
        'Pending': { label: 'Beklemede', bg: '#fd7e14', color: '#fff' },
        'Work In Progress': { label: 'İşlemde', bg: '#17a2b8', color: '#fff' },
        'Material Transferred': { label: 'Malzeme Transfer', bg: '#20c997', color: '#fff' },
        'Over Time': { label: 'Fazla Süre', bg: '#e83e8c', color: '#fff' }
    };
    
    return statusMap[status] || { label: status || 'Bilinmiyor', bg: '#6c757d', color: '#fff' };
}

function getSalesOrderStatusBadge(item) {
    // İş akışı durumunu öncelikle kontrol et
    if (item.is_akisi_durumu) {
        const workflowMap = {
            'Draft': { label: 'Taslak', bg: '#6c757d', color: '#fff' },
            'Pending Approval': { label: 'Onay Bekliyor', bg: '#ffc107', color: '#000' },
            'Approved': { label: 'Onaylandı', bg: '#28a745', color: '#fff' },
            'Rejected': { label: 'Reddedildi', bg: '#dc3545', color: '#fff' },
            'Under Review': { label: 'İncelemede', bg: '#17a2b8', color: '#fff' },
            'Pending Finance': { label: 'Muhasebe Bekliyor', bg: '#fd7e14', color: '#fff' },
            'Finance Approved': { label: 'Muhasebe Onayı', bg: '#20c997', color: '#fff' },
            'Ready for Production': { label: 'Üretime Hazır', bg: '#6f42c1', color: '#fff' },
            'In Production': { label: 'Üretimde', bg: '#e83e8c', color: '#fff' },
            'Completed': { label: 'Tamamlandı', bg: '#28a745', color: '#fff' },
            'Yeni Sipariş': { label: 'Yeni Sipariş', bg: '#6c757d', color: '#fff' },
            'New Order': { label: 'Yeni Sipariş', bg: '#6c757d', color: '#fff' },
            'Onaylandı': { label: 'Onaylandı', bg: '#28a745', color: '#fff' }
        };
        
        const workflowStatus = workflowMap[item.is_akisi_durumu];
        if (workflowStatus) {
            return workflowStatus;
        }
    }
    
    // Belge durumunu kontrol et
    if (item.belge_durumu !== undefined) {
        const docStatusMap = {
            0: { label: 'Taslak', bg: '#6c757d', color: '#fff' },
            1: { label: 'Onaylandı', bg: '#28a745', color: '#fff' },
            2: { label: 'İptal', bg: '#dc3545', color: '#fff' }
        };
        
        const docStatus = docStatusMap[item.belge_durumu];
        if (docStatus) {
            return docStatus;
        }
    }
    
    // Eski status alanını kontrol et
    const statusMap = {
        'Draft': { label: 'Taslak', bg: '#6c757d', color: '#fff' },
        'To Deliver and Bill': { label: 'Teslim ve Fatura', bg: '#17a2b8', color: '#fff' },
        'To Bill': { label: 'Fatura', bg: '#fd7e14', color: '#fff' },
        'Closed': { label: 'Kapatıldı', bg: '#28a745', color: '#fff' },
        'Cancelled': { label: 'İptal', bg: '#dc3545', color: '#fff' }
    };
    
    return statusMap[item.siparis_durumu] || { label: item.siparis_durumu || 'Bilinmiyor', bg: '#6c757d', color: '#fff' };
}

// ===== TABLO ÖZEL FİLTRE FONKSİYONLARI =====

// Planlanan Üretimler Filtreleri
function applyPlannedFilters() {
    const filters = {
        planlanan_opti_no: $('#planlanan-opti-no-filter').val(),
        planlanan_seri: $('#planlanan-seri-filter').val(),
        planlanan_renk: $('#planlanan-renk-filter').val(),
        planlanan_bayi: $('#planlanan-bayi-filter').val(),
        planlanan_musteri: $('#planlanan-musteri-filter').val()
    };
    
    // Sadece planlanan tabloyu filtrele
    filterPlannedTable(filters);
}

function clearPlannedFilters() {
    $('#planlanan-opti-no-filter').val('');
    $('#planlanan-seri-filter').val('');
    $('#planlanan-renk-filter').val('');
    $('#planlanan-bayi-filter').val('');
    $('#planlanan-musteri-filter').val('');
    
    // Tüm planlanan verileri göster
    renderTableRows('planlanan-tbody', allPlannedData.filter(item => {
        if (!showCompletedItems) {
            return !isCompleted(item);
        }
        return true;
    }));
}

function filterPlannedTable(filters) {
    const filteredData = allPlannedData.filter(item => {
        // Tamamlanan filtre
        if (!showCompletedItems && isCompleted(item)) {
            return false;
        }
        
        // Özel filtreler
        if (filters.planlanan_opti_no && item.opti_no !== filters.planlanan_opti_no) {
            return false;
        }
        if (filters.planlanan_seri && item.seri !== filters.planlanan_seri) {
            return false;
        }
        if (filters.planlanan_renk && item.renk !== filters.planlanan_renk) {
            return false;
        }
        if (filters.planlanan_bayi && item.bayi !== filters.planlanan_bayi) {
            return false;
        }
        if (filters.planlanan_musteri && item.musteri !== filters.planlanan_musteri) {
            return false;
        }
        
        return true;
    });
    
    renderTableRows('planlanan-tbody', filteredData);
}

// Planlanmamış Siparişler Filtreleri
function applyUnplannedFilters() {
    const filters = {
        planlanmamis_siparis_durum: $('#planlanmamis-siparis-durum-filter').val(),
        planlanmamis_seri: $('#planlanmamis-seri-filter').val(),
        planlanmamis_renk: $('#planlanmamis-renk-filter').val(),
        planlanmamis_bayi: $('#planlanmamis-bayi-filter').val(),
        planlanmamis_musteri: $('#planlanmamis-musteri-filter').val()
    };
    
    // Sadece planlanmamış tabloyu filtrele
    filterUnplannedTable(filters);
}

function clearUnplannedFilters() {
    $('#planlanmamis-siparis-durum-filter').val('');
    $('#planlanmamis-seri-filter').val('');
    $('#planlanmamis-renk-filter').val('');
    $('#planlanmamis-bayi-filter').val('');
    $('#planlanmamis-musteri-filter').val('');
    
    // Tüm planlanmamış verileri göster
    loadProductionData();
}

function filterUnplannedTable(filters) {
    // Mevcut planlanmamış verileri filtrele
    const currentUnplannedData = window.currentUnplannedData || [];
    const filteredData = currentUnplannedData.filter(item => {
        // Özel filtreler
        if (filters.planlanmamis_siparis_durum) {
            const status = getSalesOrderStatusBadge(item);
            if (status.label !== filters.planlanmamis_siparis_durum) {
                return false;
            }
        }
        if (filters.planlanmamis_seri && item.seri !== filters.planlanmamis_seri) {
            return false;
        }
        if (filters.planlanmamis_renk && item.renk !== filters.planlanmamis_renk) {
            return false;
        }
        if (filters.planlanmamis_bayi && item.bayi !== filters.planlanmamis_bayi) {
            return false;
        }
        if (filters.planlanmamis_musteri && item.musteri !== filters.planlanmamis_musteri) {
            return false;
        }
        
        return true;
    });
    
    renderTableRows('planlanmamis-tbody', filteredData);
}

// Yardımcı fonksiyonlar
function isCompleted(item) {
    if (!item.bitis_tarihi) return false;
    const today = new Date();
    const endDate = new Date(item.bitis_tarihi);
    return endDate < today;
}

// Tablo filtrelerini doldur
function populateTableFilters(plannedData, unplannedData) {
    // Planlanan tablo filtreleri
    const plannedOptiNos = [...new Set(plannedData.map(item => item.opti_no).filter(Boolean))];
    const plannedSeries = [...new Set(plannedData.map(item => item.seri).filter(Boolean))];
    const plannedColors = [...new Set(plannedData.map(item => item.renk).filter(Boolean))];
    const plannedBayis = [...new Set(plannedData.map(item => item.bayi).filter(Boolean))];
    const plannedMusteris = [...new Set(plannedData.map(item => item.musteri).filter(Boolean))];
    
    // Planlanmamış tablo filtreleri
    const unplannedSeries = [...new Set(unplannedData.map(item => item.seri).filter(Boolean))];
    const unplannedColors = [...new Set(unplannedData.map(item => item.renk).filter(Boolean))];
    const unplannedBayis = [...new Set(unplannedData.map(item => item.bayi).filter(Boolean))];
    const unplannedMusteris = [...new Set(unplannedData.map(item => item.musteri).filter(Boolean))];
    
    // Planlanan filtreleri doldur
    populateSelectFilter('planlanan-opti-no-filter', plannedOptiNos);
    populateSelectFilter('planlanan-seri-filter', plannedSeries);
    populateSelectFilter('planlanan-renk-filter', plannedColors);
    populateSelectFilter('planlanan-bayi-filter', plannedBayis);
    populateSelectFilter('planlanan-musteri-filter', plannedMusteris);
    
    // Planlanmamış filtreleri doldur
    populateSelectFilter('planlanmamis-seri-filter', unplannedSeries);
    populateSelectFilter('planlanmamis-renk-filter', unplannedColors);
    populateSelectFilter('planlanmamis-bayi-filter', unplannedBayis);
    populateSelectFilter('planlanmamis-musteri-filter', unplannedMusteris);
}

function populateSelectFilter(selectId, options) {
    const select = $(`#${selectId}`);
    const currentValue = select.val();
    
    // Mevcut seçenekleri temizle (ilk seçenek hariç)
    select.find('option:not(:first)').remove();
    
    // Yeni seçenekleri ekle
    options.sort().forEach(option => {
        select.append(`<option value="${option}">${option}</option>`);
    });
    
    // Önceki değeri geri yükle
    if (currentValue) {
        select.val(currentValue);
    }
}
