frappe.provide('uretim_planlama');

// Form event'lerini dinle
frappe.ui.form.on("Production Plan", {
    setup: function(frm) {
        // Form yüklendiğinde gerekli değişkenleri tanımla
        frm.cutting_chart = null;
    },

    refresh: function(frm) {
        if (frm.doc.docstatus === 1) return;

        const po_items_wrapper = frm.fields_dict["po_items"].wrapper;

        if (!$('#cutting-matrix-chart-wrapper').length) {
            const today = frappe.datetime.get_today();
            const from_default = frappe.datetime.add_days(today, -10);
            const to_date_default = frappe.datetime.add_days(today, 10);

            // Üretim Türü seçici (tek) - sadece grafiğin üstüne ekle
            $(
                `<div id="production-type-select-wrapper" style="margin-bottom: 12px; display: flex; align-items: center; gap: 12px;">
                    <label for="production-type-select" style="margin-right: 8px; font-weight: 500;">Üretim Türü:</label>
                    <select id="production-type-select" class="form-control" style="width: 120px; display: inline-block;">
                        <option value="pvc">PVC</option>
                        <option value="cam">Cam</option>
                    </select>
                </div>`
            ).insertBefore(po_items_wrapper);

            $(
                `<div id="cutting-matrix-chart-wrapper" style="
                    margin-bottom: 24px;
                    padding: 16px;
                    background: #ffffff;
                    border: 1px solid #e3e3e3;
                    border-radius: 8px;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
                    width: 100%;
                ">
                    <h5 style="margin-bottom: 12px; font-weight: 600;">Kesim Makinesi Plan Grafiği</h5>
                    <div class="field-area" style="margin-bottom: 12px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                        <div class="frappe-control" id="cutting-chart-from-date" style="min-width: 120px; max-width: 120px;"></div>
                        <div class="frappe-control" id="cutting-chart-to-date" style="min-width: 120px; max-width: 120px;"></div>
                        <button class="btn btn-sm btn-light" id="cutting-chart-refresh-btn" style="height: 28px; width: 28px; padding: 0; font-size: 14px;" title="Grafiği Yenile">
                            🔄
                        </button>
                    </div>
                    <div id="cutting-matrix-chart" style="position: relative;"></div>
                </div>`).insertAfter('#production-type-select-wrapper');

            const from_date = frappe.ui.form.make_control({
                df: {
                    fieldtype: "Date",
                    label: "",
                    fieldname: "cutting_chart_from_date",
                    default: from_default,
                    reqd: 1
                },
                parent: $('#cutting-chart-from-date'),
                only_input: true
            });

            const to_date = frappe.ui.form.make_control({
                df: {
                    fieldtype: "Date",
                    label: "",
                    fieldname: "cutting_chart_to_date",
                    default: to_date_default,
                    reqd: 1
                },
                parent: $('#cutting-chart-to-date'),
                only_input: true
            });

            from_date.make_input();
            from_date.set_value(from_default);

            to_date.make_input();
            to_date.set_value(to_date_default);

            const refresh_all = () => {
                const from = from_date.get_value();
                const to = to_date.get_value();
                if (from && to) {
                    load_cutting_chart(from, to);
                    if (window.load_cutting_table) window.load_cutting_table(from, to);
                }
            };

            $('#cutting-chart-refresh-btn').on('click', refresh_all);
            from_date.$input.on('change', refresh_all);
            to_date.$input.on('change', refresh_all);
            // Üretim türü değiştiğinde hem grafik hem tabloyu yenile
            $('#production-type-select').on('change', refresh_all);

            refresh_all();
        }
    },

    before_submit: function(frm) {
        if (!frm?.doc) return;

        frappe.call({
            method: "uretim_planlama.uretim_planlama.api.generate_cutting_plan",
            args: { docname: frm.doc.name },
            callback: function(r) {
                if (r.message?.success) {
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    });
                    refresh_chart_if_dates_exist();
                }
            }
        });
    },

    after_cancel: function(frm) {
        if (!frm?.doc) return;

        frappe.call({
            method: "uretim_planlama.uretim_planlama.api.delete_cutting_plans",
            args: { docname: frm.doc.name },
            callback: function(r) {
                if (r.message?.success) {
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    });
                    refresh_chart_if_dates_exist();
                }
            }
        });
    }
});

function refresh_chart_if_dates_exist() {
    const from_date = $('#cutting-chart-from-date').find('input').val();
    const to_date = $('#cutting-chart-to-date').find('input').val();
    if (from_date && to_date) {
        load_cutting_chart(from_date, to_date);
    }
}

function load_cutting_chart(from_date, to_date) {
    frappe.call({
        method: "uretim_planlama.uretim_planlama.api.get_daily_cutting_matrix",
        args: { from_date, to_date },
        callback: function (r) {
            const $chart = $('#cutting-matrix-chart');
            $chart.empty();

            let backend_data = r.message || [];
            // Üretim türüne göre filtreleme
            const productionType = $('#production-type-select').val();
            const isPVC = productionType === 'pvc';
            const isCam = productionType === 'cam';
            backend_data = backend_data.filter(row => {
                if (isPVC) return row.workstation && (row.workstation.includes('Murat') || row.workstation.includes('Kaban'));
                if (isCam) return row.workstation && row.workstation.includes('Bottero');
                return true;
            });

            const date_labels = [...new Set(backend_data.map(row => row.date))].sort();
            const workstations = [...new Set(backend_data.map(row => row.workstation))].sort();

            const color_palette = [
                '#3f51b5', '#e89225', '#66bb6a', '#ab47bc', '#29b6f6', '#ff7043', '#26c6da', '#d4e157'
            ];

            // Her istasyon için tek dataset (baraj ve kırmızı yok)
            const datasets = workstations.map((ws, idx) => {
                // Bottero için özel renk, diğerleri için palette
                let color = color_palette[idx % color_palette.length];
                if (ws.includes('Bottero')) {
                    color = '#1976d2'; // Belirgin mavi
                }
                return {
                    name: ws,
                    chartType: 'bar',
                    values: date_labels.map(date => {
                        const found = backend_data.find(row => row.date === date && row.workstation === ws);
                        return found ? found.total_mtul : 0;
                    }),
                    color: color
                }
            });

            if (date_labels.length === 0 || datasets.length === 0) {
                $chart.html(`
                    <div style="text-align: center; color: #888; padding: 24px;">
                        📉 Seçilen tarih aralığında (${frappe.datetime.str_to_user(from_date)} - ${frappe.datetime.str_to_user(to_date)}) görüntülenecek veri bulunamadı.
                    </div>
                `);
                return;
            }

            // Frappe Chart ile çiz
            new frappe.Chart("#cutting-matrix-chart", {
                title: "Kesim Makinesi Plan Grafiği",
                data: {
                    labels: date_labels,
                    datasets: datasets
                },
                type: 'bar',
                height: 320,
                colors: datasets.map(ds => ds.color),
                barOptions: { stacked: false, spaceRatio: 0.7 },
                tooltipOptions: { formatTooltipY: d => d + " MTUL" }
            });
        }
    });
}

function add_mtul_threshold_line(chart) {
    // Bu fonksiyonun içeriği mevcut kodda bulunmamaktadır.
    // Bu nedenle, bu fonksiyonun içeriği burada kalacak.
}