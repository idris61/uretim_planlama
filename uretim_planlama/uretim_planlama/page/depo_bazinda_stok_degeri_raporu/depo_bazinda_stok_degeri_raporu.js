frappe.pages["depo_bazinda_stok_degeri_raporu"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Depo Bazında Stok Değeri",
        single_column: true,
    });

    $(wrapper).prepend(`
        <div class="container" style="max-width: 1400px; margin: 18px auto 0 auto;">
            <div class="row mb-2 align-items-end flex-nowrap" style="gap: 0.3rem;">
                <div class="col-md-4 col-12 mb-1 mb-md-0">
                    <label for="stok-urun-filter" style="font-weight: 500; color: #333; margin-bottom: 1px; font-size: 0.92rem;">Ürün</label>
                    <select id="stok-urun-filter" class="form-control filter-input" style="border-radius: 6px; border: 1px solid #b3c6e7; background: #f8fafc; font-weight: 400; color: #222; height: 28px; font-size: 0.92rem; padding: 2px 8px;">
                        <option value="">Ürün Seçin</option>
                    </select>
                </div>
                <div class="col-md-3 col-12 mb-1 mb-md-0">
                    <label for="stok-urun-grup-filter" style="font-weight: 500; color: #333; margin-bottom: 1px; font-size: 0.92rem;">Ürün Grubu</label>
                    <select id="stok-urun-grup-filter" class="form-control filter-input" style="border-radius: 6px; border: 1px solid #b3c6e7; background: #f8fafc; font-weight: 400; color: #222; height: 28px; font-size: 0.92rem; padding: 2px 8px;">
                        <option value="">Tümü</option>
                    </select>
                </div>
                <div class="col-md-3 col-12 mb-1 mb-md-0">
                    <label for="stok-depo-filter" style="font-weight: 500; color: #333; margin-bottom: 1px; font-size: 0.92rem;">Depo</label>
                    <select id="stok-depo-filter" class="form-control filter-input" style="border-radius: 6px; border: 1px solid #b3c6e7; background: #f8fafc; font-weight: 400; color: #222; height: 28px; font-size: 0.92rem; padding: 2px 8px;">
                        <option value="">Tümü</option>
                    </select>
                </div>
                <div class="col-md-2 col-12 mb-1 mb-md-0 d-flex align-items-center" style="height: 28px;">
                    <button id="stok-rapor-filtrele-btn" class="btn btn-dark w-100" style="font-weight: 500; border-radius: 6px; padding: 4px 0; font-size: 0.92rem; height: 28px;">Filtrele</button>
                </div>
            </div>
        </div>
    `);

    $(wrapper).append(`
        <div class="container" style="max-width: 1400px; margin: auto;">
            <div class="row mt-4 mb-3">
                <div class="col-md-12">
                    <div class="card mb-3" style="background: #e3f2fd; border-radius: 12px; box-shadow: 0 2px 8px #b3c6e7;">
                        <div class="card-body">
                            <div class="d-flex align-items-center justify-content-between card-title" style="cursor:pointer; font-weight: bold; color: #1565c0;">
                                <span>Depo Bazında Toplam Stok Değeri</span>
                                <span class="toggle-table" data-target="#stok-depo-ozet-tablo" style="font-size:1.2em; user-select:none;">&#9660;</span>
                            </div>
                            <div id="stok-depo-ozet-tablo" class="table-body"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mb-4">
                <div class="col-md-12">
                    <div class="card" style="background: #f1f8e9; border-radius: 12px; box-shadow: 0 2px 8px #b6d7a8;">
                        <div class="card-body">
                            <div class="d-flex align-items-center justify-content-between card-title" style="cursor:pointer; font-weight: bold; color: #388e3c;">
                                <span>Depo / Ürün Bazında Detaylı Stok Değeri</span>
                                <span class="toggle-table" data-target="#stok-depo-detay-tablo" style="font-size:1.2em; user-select:none;">&#9660;</span>
                            </div>
                            <div id="stok-depo-detay-tablo" class="table-body"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);

    $(document).on("click", ".toggle-table, .card-title", function (e) {
        const $target = $(e.target);
        const $icon = $target.hasClass("toggle-table")
            ? $target
            : $target.closest(".card-title").find(".toggle-table");
        const tableId = $icon.data("target");
        const $table = $(tableId);
        $table.slideToggle(180, function () {
            $icon.html($table.is(":visible") ? "&#9660;" : "&#9654;");
        });
        e.stopPropagation();
    });

    $(document).on("click", "#stok-rapor-filtrele-btn", function () {
        load_stock_value_report();
    });

    frappe.require(
        ["/assets/uretim_planlama/js/select2.min.js", "/assets/uretim_planlama/css/select2.min.css"],
        function () {
            $("#stok-urun-filter").select2({
                width: "100%",
                placeholder: "Ürün Seçin",
                allowClear: true,
                ajax: {
                    transport: function (params, success, failure) {
                        frappe.call({
                            method: "frappe.client.get_list",
                            args: {
                                doctype: "Item",
                                fields: ["name", "item_name"],
                                filters: params.data.q
                                    ? [["name", "like", "%" + params.data.q + "%"]]
                                    : [],
                                limit_page_length: 20,
                            },
                            callback: function (r) {
                                success({
                                    results: (r.message || []).map(function (item) {
                                        const label = item.item_name
                                            ? item.name + " - " + item.item_name
                                            : item.name;
                                        return { id: item.name, text: label };
                                    }),
                                });
                            },
                            error: failure,
                        });
                    },
                    delay: 250,
                },
                minimumInputLength: 1,
            });
            $("#stok-depo-filter").select2({
                width: "100%",
                placeholder: "Depo Seçin",
                allowClear: true,
            });
            $("#stok-urun-grup-filter").select2({
                width: "100%",
                placeholder: "Ürün Grubu Seçin",
                allowClear: true,
            });
        }
    );

    fill_filters();
    render_empty_state();

    function fill_filters() {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Warehouse",
                fields: ["name"],
                limit_page_length: 1000,
            },
            callback: function (r) {
                const select = $("#stok-depo-filter");
                select.empty();
                select.append('<option value="">Tümü</option>');
                (r.message || []).forEach((item) => {
                    select.append(`<option value="${item.name}">${item.name}</option>`);
                });
                select.trigger("change.select2");
            },
        });

        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Item Group",
                fields: ["name"],
                filters: { is_group: 0 },
                limit_page_length: 500,
            },
            callback: function (r) {
                const select = $("#stok-urun-grup-filter");
                select.empty();
                select.append('<option value="">Tümü</option>');
                (r.message || []).forEach((item) => {
                    select.append(`<option value="${item.name}">${item.name}</option>`);
                });
                select.trigger("change.select2");
            },
        });
    }

    function render_empty_state() {
        const text =
            '<div style="text-align:center; padding:12px; color:#666;">Filtreleri seçip "Filtrele" butonuna tıklayın.</div>';
        $("#stok-depo-ozet-tablo").html(text);
        $("#stok-depo-detay-tablo").html(text);
    }

    function show_loading() {
        const loading_html =
            '<div style="text-align:center; padding:12px; color:#666;">Veriler yükleniyor...</div>';
        $("#stok-depo-ozet-tablo").html(loading_html);
        $("#stok-depo-detay-tablo").html(loading_html);
    }

    function load_stock_value_report() {
        const item_code = $("#stok-urun-filter").val() || undefined;
        const item_group = $("#stok-urun-grup-filter").val() || undefined;
        const warehouse = $("#stok-depo-filter").val() || undefined;

        show_loading();

        frappe.call({
            method:
                "uretim_planlama.uretim_planlama.api.stock_value_report.get_warehouse_stock_value",
            args: {
                item_code: item_code,
                item_group: item_group,
                warehouse: warehouse,
            },
            timeout: 60,
            callback: function (r) {
                const data = r.message || {};
                render_warehouse_summary(data.warehouse_summary || []);
                render_item_details(data.items || []);
            },
            error: function () {
                const error_html =
                    '<div style="text-align:center; padding:12px; color:red;">Veri alınamadı</div>';
                $("#stok-depo-ozet-tablo").html(error_html);
                $("#stok-depo-detay-tablo").html(error_html);
            },
        });
    }

    function render_warehouse_summary(data) {
        if (!data.length) {
            $("#stok-depo-ozet-tablo").html(
                '<div style="text-align:center; padding:12px; color:#666;">Kayıt bulunamadı</div>'
            );
            return;
        }

        let genelToplamDeger = 0;
        let genelToplamMiktar = 0;

        data.forEach((row) => {
            genelToplamDeger += Number(row.total_stock_value) || 0;
            genelToplamMiktar += Number(row.total_qty) || 0;
        });

        let html = `<div class="table-responsive"><table class="table table-bordered table-hover table-striped" style="background:#fff; border-collapse:separate; border-spacing:0; table-layout:auto; width:100%;">
            <thead style="background:#e9ecef; color:#2c3e50; font-weight:bold;">
                <tr>
                    <th class="sticky-col sticky-header">#</th>
                    <th class="sticky-header">Depo</th>
                    <th class="sticky-header">Toplam Miktar</th>
                    <th class="sticky-header">Ortalama Maliyet</th>
                    <th class="sticky-header">Toplam Stok Değeri</th>
                </tr>
            </thead>
            <tbody>`;

        data.forEach((row, idx) => {
            html += `<tr>
                <td class="sticky-col">${idx + 1}</td>
                <td>${row.warehouse}</td>
                <td>${frappe.format(row.total_qty, { fieldtype: "Float", precision: 2 })}</td>
                <td>${frappe.format(row.avg_valuation_rate, {
                    fieldtype: "Currency",
                    precision: 2,
                })}</td>
                <td>${frappe.format(row.total_stock_value, {
                    fieldtype: "Currency",
                    precision: 2,
                })}</td>
            </tr>`;
        });

        html += `<tr style="font-weight:bold; background:#f5f5f5;">
            <td class="sticky-col"></td>
            <td style="text-align:right;">Genel Toplam</td>
            <td>${frappe.format(genelToplamMiktar, { fieldtype: "Float", precision: 2 })}</td>
            <td></td>
            <td>${frappe.format(genelToplamDeger, { fieldtype: "Currency", precision: 2 })}</td>
        </tr>`;

        html += "</tbody></table></div>";
        $("#stok-depo-ozet-tablo").html(html);
    }

    function render_item_details(data) {
        if (!data.length) {
            $("#stok-depo-detay-tablo").html(
                '<div style="text-align:center; padding:12px; color:#666;">Kayıt bulunamadı</div>'
            );
            return;
        }

        let toplamDeger = 0;
        let toplamMiktar = 0;

        data.forEach((row) => {
            toplamDeger += Number(row.stock_value) || 0;
            toplamMiktar += Number(row.qty) || 0;
        });

        let html = `<div class="table-responsive"><table class="table table-bordered table-hover table-striped" style="background:#fff; border-collapse:separate; border-spacing:0; table-layout:auto; width:100%;">
            <thead style="background:#e9ecef; color:#2c3e50; font-weight:bold;">
                <tr>
                    <th class="sticky-col sticky-header">#</th>
                    <th class="sticky-header">Depo</th>
                    <th class="sticky-header">Ürün Kodu</th>
                    <th class="sticky-header">Ürün Adı</th>
                    <th class="sticky-header">Ürün Grubu</th>
                    <th class="sticky-header">Miktar</th>
                    <th class="sticky-header">Maliyet</th>
                    <th class="sticky-header">Stok Değeri</th>
                </tr>
            </thead>
            <tbody>`;

        data.forEach((row, idx) => {
            html += `<tr>
                <td class="sticky-col">${idx + 1}</td>
                <td>${row.warehouse}</td>
                <td>${row.item_code}</td>
                <td>${row.item_name || ""}</td>
                <td>${row.item_group || ""}</td>
                <td>${frappe.format(row.qty, { fieldtype: "Float", precision: 2 })}</td>
                <td>${frappe.format(row.valuation_rate, {
                    fieldtype: "Currency",
                    precision: 2,
                })}</td>
                <td>${frappe.format(row.stock_value, {
                    fieldtype: "Currency",
                    precision: 2,
                })}</td>
            </tr>`;
        });

        html += `<tr style="font-weight:bold; background:#f5f5f5;">
            <td class="sticky-col"></td>
            <td colspan="3" style="text-align:right;">Genel Toplam</td>
            <td></td>
            <td>${frappe.format(toplamMiktar, { fieldtype: "Float", precision: 2 })}</td>
            <td></td>
            <td>${frappe.format(toplamDeger, { fieldtype: "Currency", precision: 2 })}</td>
        </tr>`;

        html += "</tbody></table></div>";
        $("#stok-depo-detay-tablo").html(html);
    }

    if (!$("style#depo-stok-degeri-table-responsive").length) {
        $(
            "<style id='depo-stok-degeri-table-responsive'>" +
                ".table-responsive{overflow-x:auto;overflow-y:auto;width:100%;max-height:350px;position:relative;}" +
                ".table-responsive table{position:relative;border-collapse:separate;border-spacing:0;}" +
                ".table-responsive thead{position:sticky;top:0;z-index:100;background:#e9ecef!important;}" +
                ".table-responsive thead th{position:sticky;top:0;z-index:101;background:#e9ecef!important;border-bottom:2px solid #dee2e6!important;padding:8px!important;white-space:nowrap;}" +
                ".sticky-col{position:sticky;left:0;background:#fff!important;z-index:11;box-shadow:2px 0 2px -1px rgba(0,0,0,0.1);}" +
                ".sticky-col.sticky-header{background:#e9ecef!important;z-index:102;box-shadow:2px 2px 2px -1px rgba(0,0,0,0.1);}" +
                "</style>"
        ).appendTo("head");
    }
};




