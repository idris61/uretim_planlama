frappe.pages['profil_stok_paneli'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Profil Stok Paneli',
        single_column: true
    });

    // Başlık ve filtre alanları
    $(wrapper).prepend(`
        <div class="container" style="max-width: 1400px; margin: 18px auto 0 auto;">
            <div class="row mb-2 align-items-end flex-nowrap" style="gap: 0.3rem;">
                <div class="col-md-3 col-12 mb-1 mb-md-0">
                    <label for="profil-filter" style="font-weight: 500; color: #333; margin-bottom: 1px; font-size: 0.92rem;">Profil</label>
                    <select id="profil-filter" class="form-control filter-input" style="border-radius: 6px; border: 1px solid #b3c6e7; background: #f8fafc; font-weight: 400; color: #222; height: 28px; font-size: 0.92rem; padding: 2px 8px;"><option value="">Profil Kodu Seçin</option></select>
                </div>
                <div class="col-md-3 col-12 mb-1 mb-md-0">
                    <label for="depo-filter" style="font-weight: 500; color: #333; margin-bottom: 1px; font-size: 0.92rem;">Depo</label>
                    <select id="depo-filter" class="form-control filter-input" style="border-radius: 6px; border: 1px solid #b3c6e7; background: #f8fafc; font-weight: 400; color: #222; height: 28px; font-size: 0.92rem; padding: 2px 8px;"><option value="">Depo Seçin</option></select>
                </div>
                <div class="col-md-2 col-12 mb-1 mb-md-0 d-flex align-items-center" style="height: 28px;">
                    <div class="form-check d-flex align-items-center" style="margin-top: 6px;">
                        <input type="checkbox" id="scrap-filter" class="form-check-input" style="margin-top: 0; width: 16px; height: 16px;">
                        <label class="form-check-label ms-1" for="scrap-filter" style="font-weight: 500; color: #333; font-size: 0.92rem; margin-left: 4px;">Sadece Parça Profil</label>
                </div>
                </div>
                <div class="col-md-2 col-12 mb-1 mb-md-0 d-flex align-items-center" style="height: 28px;">
                    <button id="filtrele-btn" class="btn btn-dark w-100" style="font-weight: 500; border-radius: 6px; padding: 4px 0; font-size: 0.92rem; height: 28px;">Filtrele</button>
                </div>
            </div>
        </div>
    `);

    // Tablo alanlarını güncelle
    $(wrapper).append(`
        <div class="container" style="max-width: 1400px; margin: auto;">
            <div class="row mt-4 mb-2" id="row-erpnext-stok">
                <div class="col-md-12">
                    <div class="card mb-3" style="background: #e3f2fd; border-radius: 12px; box-shadow: 0 2px 8px #b3c6e7;">
                        <div class="card-body">
                            <div class="d-flex align-items-center justify-content-between card-title" style="cursor:pointer; font-weight: bold; color: #1565c0;">
                                <span>Depo Bazında Toplam Profil Stoku</span>
                                <span class="toggle-table" data-target="#erpnext-stok-tablo" style="font-size:1.2em; user-select:none;">&#9660;</span>
                            </div>
                            <div id="erpnext-stok-tablo" class="table-body"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mb-4" id="row-profil-boy">
                <div class="col-md-12">
                    <div class="card" style="background: #f1f8e9; border-radius: 12px; box-shadow: 0 2px 8px #b6d7a8;">
                        <div class="card-body">
                            <div class="d-flex align-items-center justify-content-between card-title" style="cursor:pointer; font-weight: bold; color: #388e3c;">
                                <span>Boy Bazında Profil Stok Detayı</span>
                                <span class="toggle-table" data-target="#profil-boy-tablo" style="font-size:1.2em; user-select:none;">&#9660;</span>
                            </div>
                            <div id="profil-boy-tablo" class="table-body"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mb-4" id="row-scrap-profile">
                <div class="col-md-12">
                    <div class="card" style="background: #fff3e0; border-radius: 12px; box-shadow: 0 2px 8px #ffd180;">
                        <div class="card-body">
                            <div class="d-flex align-items-center justify-content-between card-title" style="cursor:pointer; font-weight: bold; color: #e65100;">
                                <span>Parça Profil Kayıtları</span>
                                <span class="toggle-table" data-target="#scrap-profile-tablo" style="font-size:1.2em; user-select:none;">&#9660;</span>
                            </div>
                            <div id="scrap-profile-tablo" class="table-body"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mb-4" id="row-hammadde-rezervleri">
                <div class="col-md-12">
                    <div class="card" style="background: #fffbe7; border-radius: 12px; box-shadow: 0 2px 8px #ffe082;">
                        <div class="card-body">
                            <div class="d-flex align-items-center justify-content-between card-title" style="cursor:pointer; font-weight: bold; color: #bfa100;">
                                <span>Hammadde Rezervleri</span>
                                <span class="toggle-table" data-target="#hammadde-rezervleri-tablo" style="font-size:1.2em; user-select:none;">&#9660;</span>
                            </div>
                            <div id="hammadde-rezervleri-tablo" class="table-body"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);

    // Aç/kapa ikonları için event
    $(document).on('click', '.toggle-table, .card-title', function(e) {
        let $target = $(e.target);
        let $icon = $target.hasClass('toggle-table') ? $target : $target.closest('.card-title').find('.toggle-table');
        let tableId = $icon.data('target');
        let $table = $(tableId);
        $table.slideToggle(180, function() {
            $icon.html($table.is(':visible') ? '&#9660;' : '&#9654;');
        });
        e.stopPropagation();
    });

    // Filtrele butonu event
    $(document).on('click', '#filtrele-btn', function() {
        get_and_render_panel(true);
    });

    // Sadece Parça filtresi değiştiğinde tablo görünürlüğünü ayarla
    $(document).on('change', '#scrap-filter', function() {
        toggle_tables();
        get_and_render_panel(false);
    });

    function toggle_tables() {
        const is_scrap = $('#scrap-filter').is(':checked');
        $('#row-erpnext-stok').toggle(!is_scrap);
        $('#row-profil-boy').toggle(!is_scrap);
        $('#row-hammadde-rezervleri').toggle(!is_scrap);
        $('#depo-filter').prop('disabled', is_scrap).trigger('change.select2');
        if (is_scrap) {
            $('#depo-filter').val(null).trigger('change.select2');
        }
    }

    // Sayfa ilk açıldığında filtreleri doldur
    fill_filters();
    // Sayfa ilk açıldığında tablo görünürlüğünü ayarla
    toggle_tables();
    // Sayfa ilk açıldığında genel veriyi çek (profil/depo seçilmemiş olabilir)
    get_and_render_panel(false);

    // Gerekli kütüphaneleri yükle
    frappe.require([
        '/assets/uretim_planlama/js/chart.bundle.min.js',
        '/assets/uretim_planlama/js/select2.min.js',
        '/assets/uretim_planlama/css/select2.min.css'
    ], function() {
        // Profil kodu select2 AJAX ile dinamik arama
        $('#profil-filter').select2({
            width: '100%',
            placeholder: 'Profil Kodu Seçin',
            allowClear: true,
            ajax: {
                transport: function (params, success, failure) {
                    frappe.call({
                        method: 'frappe.client.get_list',
                        args: {
                            doctype: 'Item',
                            fields: ['item_code'],
                            filters: params.data.q ? [['item_code', 'like', '%' + params.data.q + '%']] : [],
                            limit_page_length: 20
                        },
                        callback: function(r) {
                            success({
                                results: (r.message || []).map(function(item) {
                                    return { id: item.item_code, text: item.item_code };
                                })
                            });
                        },
                        error: failure
                    });
                },
                delay: 250
            },
            minimumInputLength: 1
        });
        // Depo select2 sabit kalsın
        $('#depo-filter').select2({width: '100%', placeholder: 'Depo Seçin', allowClear: true});
    });

    function fill_filters() {
        // Profil kodu doldurma kaldırıldı, select2 AJAX ile geliyor
        // Depo doldur
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Warehouse",
                fields: ["name"],
                limit_page_length: 1000
            },
            callback: function(r) {
                let select = $('#depo-filter');
                select.empty();
                select.append('<option value="">Tümü</option>');
                r.message.forEach(item => {
                    select.append(`<option value="${item.name}">${item.name}</option>`);
                });
            }
        });
    }

    function show_loading() {
        const loading_html = '<div style="text-align:center; padding:12px; color:#666;">Veriler yükleniyor...</div>';
        // Depo tablosu için loading durumu, profil seçimine göre ayrı yönetilecek
        $('#profil-boy-tablo').html(loading_html);
        $('#scrap-profile-tablo').html(loading_html);
        $('#hammadde-rezervleri-tablo').html(loading_html);
    }

    function clear_tables(message_html) {
        $('#erpnext-stok-tablo').html(message_html || '');
        $('#profil-boy-tablo').html(message_html || '');
        $('#scrap-profile-tablo').html(message_html || '');
        $('#hammadde-rezervleri-tablo').html(message_html || '');
    }

    function get_and_render_panel(is_manual_filter) {
        const profil = $('#profil-filter').val() || undefined;

        const loading_html = '<div style="text-align:center; padding:12px; color:#666;">Veriler yükleniyor...</div>';
        const no_profile_html = '<div style="text-align:center; padding:12px; color:#666;">Depo bazında stok için lütfen bir profil seçin.</div>';

        // Depo tablosu: profil varsa loading, yoksa açıklama mesajı
        if (profil) {
            $('#erpnext-stok-tablo').html(loading_html);
        } else {
            $('#erpnext-stok-tablo').html(no_profile_html);
        }

        // Diğer tablolar için standart loading
        show_loading();

        const args = {
            profil: profil,
            depo: $('#depo-filter').val() || undefined,
            scrap: $('#scrap-filter').is(':checked') ? 1 : undefined
        };
        frappe.call({
            method: 'uretim_planlama.uretim_planlama.api.get_profile_stock_panel',
            args: args,
            callback: function(r) {
                const data = r.message || {};
                // Debug log kaldırıldı
                // Her tabloya özel veri
                if (profil) {
                    render_erpnext_stok_tablo(data.depo_stoklari || []);
                }
                render_boy_bazinda_tablo(data.boy_bazinda_stok || []);
                render_scrap_profile_tablo(data.scrap_profiller || []);
                render_hammadde_rezervleri_tablo(data.hammadde_rezervleri || []);
            },
            error: function() {
                $('#erpnext-stok-tablo').html('<div style="text-align:center; color:red;">Veri alınamadı</div>');
                $('#profil-boy-tablo').html('<div style="text-align:center; color:red;">Veri alınamadı</div>');
                $('#scrap-profile-tablo').html('<div style="text-align:center; color:red;">Veri alınamadı</div>');
                $('#hammadde-rezervleri-tablo').html('<div style="text-align:center; color:red;">Veri alınamadı</div>');
            }
        });
    }

    function render_erpnext_stok_tablo(data) {
        let toplam = 0;
        data.forEach(row => {
            toplam += Number(row.toplam_stok_mtul) || 0;
        });
        let tablo = `<div class="table-responsive"><table class="table table-bordered table-hover table-striped" style="background: #fff; border-collapse: separate; border-spacing: 0; table-layout: auto; width: 100%;">
            <thead style="background: #e9ecef; color: #2c3e50; font-weight: bold;">
                <tr>
                    <th class="sticky-col sticky-header">#</th>
                    <th class="sticky-header">Depo</th>
                    <th class="sticky-header">Profil</th>
                    <th class="sticky-header">Profil Adı</th>
                    <th class="sticky-header">Toplam Stok (mtül)</th>
                </tr>
            </thead>
            <tbody>`;
        data.forEach((row, i) => {
            if ((Number(row.toplam_stok_mtul) || 0) <= 0) { return; }
            tablo += `<tr>
                <td class="sticky-col">${i+1}</td>
                <td>${row.depo}</td>
                <td>${row.profil}</td>
                <td>${row.profil_adi}</td>
                <td>${row.toplam_stok_mtul}</td>
            </tr>`;
        });
        // Genel toplam satırı
        tablo += `<tr style="font-weight:bold; background:#f5f5f5;"><td class="sticky-col"></td><td colspan="3" style="text-align:right;">Genel Toplam</td><td>${toplam}</td></tr>`;
        tablo += '</tbody></table></div>';
        $('#erpnext-stok-tablo').html(tablo);
    }

    function render_boy_bazinda_tablo(data) {
        let toplam = 0;
        data.forEach(row => {
            toplam += Number(row.mtul) || 0;
        });
        let tablo = `<div class="table-responsive"><table class="table table-bordered table-hover table-striped" style="background: #fff; border-collapse: separate; border-spacing: 0; table-layout: auto; width: 100%;">
            <thead style="background: #e9ecef; color: #2c3e50; font-weight: bold;">
                <tr>
                    <th class="sticky-col sticky-header">#</th>
                    <th class="sticky-header">Profil</th>
                    <th class="sticky-header">Profil Adı</th>
                    <th class="sticky-header">Boy</th>
                    <th class="sticky-header">Adet</th>
                    <th class="sticky-header">Toplam (mtül)</th>
                    <th class="sticky-header">Güncelleme</th>
                </tr>
            </thead>
            <tbody>`;
        data.forEach((row, i) => {
            let tarih = row.guncelleme ? frappe.datetime.str_to_user(row.guncelleme) : '';
            if (((Number(row.mtul) || 0) <= 0) && ((Number(row.adet) || 0) <= 0)) { return; }
            tablo += `<tr>
                <td class="sticky-col">${i+1}</td>
                <td>${row.profil}</td>
                <td>${row.profil_adi}</td>
                <td>${row.boy}</td>
                <td>${row.adet}</td>
                <td>${row.mtul}</td>
                <td>${tarih}</td>
            </tr>`;
        });
        // Genel toplam satırı
        tablo += `<tr style="font-weight:bold; background:#f5f5f5;"><td class="sticky-col"></td><td colspan="4" style="text-align:right;">Genel Toplam</td><td>${toplam}</td><td></td></tr>`;
        tablo += '</tbody></table></div>';
        $('#profil-boy-tablo').html(tablo);
    }

    function render_scrap_profile_tablo(data) {
        let toplam = 0;
        data.forEach(row => {
            toplam += Number(row.mtul) || 0;
        });
        let tablo = `<div class="table-responsive"><table class="table table-bordered table-hover table-striped" style="background: #fff; border-collapse: separate; border-spacing: 0; table-layout: auto; width: 100%;">
            <thead style="background: #e9ecef; color: #2c3e50; font-weight: bold;">
                <tr>
                    <th class="sticky-col sticky-header">#</th>
                    <th class="sticky-header">Profil</th>
                    <th class="sticky-header">Profil Adı</th>
                    <th class="sticky-header">Boy</th>
                    <th class="sticky-header">Adet</th>
                    <th class="sticky-header">Toplam (mtül)</th>
                    <th class="sticky-header">Açıklama</th>
                    <th class="sticky-header">Giriş Tarihi</th>
                    <th class="sticky-header">Güncelleme</th>
                </tr>
            </thead>
            <tbody>`;
        data.forEach((row, i) => {
            let tarih = row.tarih ? frappe.datetime.str_to_user(row.tarih) : '';
            let guncelleme = row.guncelleme ? frappe.datetime.str_to_user(row.guncelleme) : '';
            tablo += `<tr>
                <td class="sticky-col">${i+1}</td>
                <td>${row.profil}</td>
                <td>${row.profil_adi}</td>
                <td>${row.boy}</td>
                <td>${row.adet}</td>
                <td>${row.mtul}</td>
                <td>${row.aciklama || ''}</td>
                <td>${tarih}</td>
                <td>${guncelleme}</td>
            </tr>`;
        });
        // Genel toplam satırı
        tablo += `<tr style="font-weight:bold; background:#f5f5f5;"><td class="sticky-col"></td><td colspan="4" style="text-align:right;">Genel Toplam</td><td>${toplam}</td><td colspan="3"></td></tr>`;
        tablo += '</tbody></table></div>';
        $('#scrap-profile-tablo').html(tablo);
    }

    function render_hammadde_rezervleri_tablo(data) {
        let toplam = 0;
        data.forEach(row => {
            toplam += Number(row.quantity) || 0;
        });
        let tablo = `<div class="table-responsive"><table class="table table-bordered table-hover table-striped" style="background: #fff; border-collapse: separate; border-spacing: 0; table-layout: auto; width: 100%;">
            <thead style="background: #fffde7; color: #bfa100; font-weight: bold;">
                <tr>
                    <th class="sticky-col sticky-header">Hammadde Kodu</th>
                    <th class="sticky-header">Hammadde Adı</th>
                    <th class="sticky-header">Rezerve Miktar (mtül)</th>
                    <th class="sticky-header">Satış Siparişi</th>
                </tr>
            </thead>
            <tbody>`;
        if (data.length === 0) {
            tablo += `<tr><td class="sticky-col" colspan="4" style="text-align:center;">Kayıt bulunamadı</td></tr>`;
        } else {
            data.forEach(row => {
                let salesOrderLink = row.sales_order ? `<a href='/app/sales-order/${encodeURIComponent(row.sales_order)}' target='_blank'>${row.sales_order}</a>` : '';
                tablo += `<tr>
                    <td class="sticky-col">${row.item_code}</td>
                    <td>${row.item_name || ''}</td>
                    <td>${row.quantity}</td>
                    <td>${salesOrderLink}</td>
                </tr>`;
            });
            // Genel toplam satırı
            tablo += `<tr style="font-weight:bold; background:#fff9c4;"><td class="sticky-col" colspan="2" style="text-align:right;">Genel Toplam</td><td>${toplam}</td><td></td></tr>`;
        }
        tablo += '</tbody></table></div>';
        $('#hammadde-rezervleri-tablo').html(tablo);
    }

    // Stil ekle (gerekirse)
    if (!$('style#profil-stok-paneli-table-responsive').length) {
        $("<style id='profil-stok-paneli-table-responsive'>"
        + ".table-responsive{overflow-x:auto;overflow-y:auto;width:100%;max-height:350px;position:relative;}"
        + ".table-responsive table{position:relative;border-collapse:separate;border-spacing:0;}"
        + ".table-responsive thead{position:sticky;top:0;z-index:100;background:#e9ecef!important;}"
        + ".table-responsive thead th{position:sticky;top:0;z-index:101;background:#e9ecef!important;border-bottom:2px solid #dee2e6!important;padding:8px!important;white-space:nowrap;}"
        + ".sticky-col{position:sticky;left:0;background:#fff!important;z-index:11;box-shadow:2px 0 2px -1px rgba(0,0,0,0.1);}"
        + ".sticky-col.sticky-header{background:#e9ecef!important;z-index:102;box-shadow:2px 2px 2px -1px rgba(0,0,0,0.1);}"
        + "</style>").appendTo('head');
    }
}; 