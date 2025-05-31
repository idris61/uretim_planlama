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

        if (!$('#cutting-matrix-wrapper').length) {
            const today = frappe.datetime.get_today();
            const from_date_default = frappe.datetime.add_days(today, -10);
            const to_date_default = frappe.datetime.add_days(today, 10);

            $(
                `<div id="cutting-matrix-wrapper" style="
                    margin-bottom: 24px;
                    padding: 16px;
                    background: #ffffff;
                    border: 1px solid #e3e3e3;
                    border-radius: 8px;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
                    width: 100%;
                ">
                    <div class="field-area" style="margin-bottom: 12px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                        <div class="frappe-control" id="cutting-from-date" style="min-width: 120px; max-width: 120px;"></div>
                        <div class="frappe-control" id="cutting-to-date" style="min-width: 120px; max-width: 120px;"></div>
                        <button class="btn btn-sm btn-light" id="cutting-refresh-btn" style="height: 28px; width: 28px; padding: 0; font-size: 14px;" title="Grafiği Yenile">
                            🔄
                        </button>
                    </div>
                    <div id="cutting-matrix-chart"></div>
                </div>`
            ).insertBefore(po_items_wrapper);

            const from_date = frappe.ui.form.make_control({
                df: {
                    fieldtype: "Date",
                    label: "",
                    fieldname: "cutting_from_date",
                    default: from_date_default,
                    reqd: 1
                },
                parent: $('#cutting-from-date'),
                only_input: true
            });

            const to_date = frappe.ui.form.make_control({
                df: {
                    fieldtype: "Date",
                    label: "",
                    fieldname: "cutting_to_date",
                    default: to_date_default,
                    reqd: 1
                },
                parent: $('#cutting-to-date'),
                only_input: true
            });

            from_date.make_input();
            to_date.make_input();

            const refresh_chart = () => {
                const from = from_date.get_value();
                const to = to_date.get_value();
                if (from && to) load_cutting_chart(from, to);
            };

            $('#cutting-refresh-btn').on('click', refresh_chart);
            from_date.$input.on('change', refresh_chart);
            to_date.$input.on('change', refresh_chart);

            // Sayfa ilk yüklendiğinde çiz
            refresh_chart();
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
    const from_date = $('#cutting-from-date').find('input').val();
    const to_date = $('#cutting-to-date').find('input').val();
    if (from_date && to_date) {
        load_cutting_chart(from_date, to_date);
    }
}

function load_cutting_chart(from_date, to_date) {
    frappe.call({
        method: "uretim_planlama.uretim_planlama.api.get_daily_cutting_matrix",
        args: { from_date, to_date },
        callback: function(r) {
            const $chart = $('#cutting-matrix-chart');
            $chart.empty();

            if (!r.message || r.message.length === 0) {
                $chart.html(`
                    <div style="text-align: center; color: #888; padding: 24px;">
                        📉 Seçilen tarih aralığında (${frappe.datetime.str_to_user(from_date)} - ${frappe.datetime.str_to_user(to_date)}) görüntülenecek veri bulunamadı.
                    </div>
                `);
                return;
            }

            try {
                const raw = r.message;
                const label_map = {};
                raw.forEach(d => {
                    const date = d.date;
                    if (!label_map[date]) {
                        const dt = frappe.datetime.str_to_obj(date);
                        label_map[date] = frappe.datetime.obj_to_user(dt);
                    }
                });

                const dates = Object.keys(label_map).sort();
                const workstations = [...new Set(raw.map(d => d.workstation))].sort();

                // Group data by date and workstation
                const grouped_data = {};
                raw.forEach(d => {
                    if (!grouped_data[d.date]) {
                        grouped_data[d.date] = {};
                    }
                    grouped_data[d.date][d.workstation] = d;
                });

                let table_html = `
                    <style>
                        .cutting-matrix-table {
                            width: 100%;
                            border-collapse: collapse;
                            margin-top: 16px;
                        }
                        .cutting-matrix-table th, .cutting-matrix-table td {
                            border: 1px solid #e3e3e3;
                            padding: 8px;
                            text-align: left;
                        }
                        .cutting-matrix-table th {
                            background-color: #f2f2f2;
                            font-weight: bold;
                        }
                        .cutting-matrix-table tbody tr:nth-child(even) {
                            background-color: #f9f9f9;
                        }
                        .cutting-matrix-table .total-mtul-cell {
                            width: 60%; /* Adjust width as needed */
                        }
                        .cutting-matrix-table .mtul-bar-container {
                            width: 100%;
                            background-color: #ddd;
                            border-radius: 4px;
                            overflow: hidden;
                            position: relative;
                            height: 20px; /* Height of the bar */
                        }
                        .cutting-matrix-table .mtul-bar {
                            height: 100%;
                            background-color: #66bb6a; /* Default green color */
                            text-align: center;
                            color: white;
                            line-height: 20px;
                            font-weight: bold;
                            white-space: nowrap;
                            transition: width 0.5s ease-in-out;
                        }
                        .cutting-matrix-table .mtul-bar.high-value {
                            background-color: #ef5350; /* Red color for high values */
                        }
                         .cutting-matrix-table .total-text {
                            font-weight: bold;
                            margin-left: 8px;
                            color: #333; /* Default text color */
                        }
                         .cutting-matrix-table .high-value-text {
                             color: #ef5350; /* Red color for high values */
                         }
                    </style>
                    <table class="cutting-matrix-table">
                        <thead>
                            <tr>
                                <th>Tarih</th>
                                <th>İstasyon</th>
                                <th class="total-mtul-cell">Toplam MTUL - Toplam Adet</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                // Find the maximum MTUL value for scaling the bars
                const max_mtul = Math.max(...raw.map(d => d.total_mtul));
                const scale_factor = max_mtul > 0 ? 100 / max_mtul : 0;

                dates.forEach(date => {
                    workstations.forEach(workstation => {
                        const data = grouped_data[date] ? grouped_data[date][workstation] : null;
                        const total_mtul = data ? data.total_mtul : 0;
                        const total_quantity = data ? data.total_quantity : 0;
                        const display_date = label_map[date];

                        const bar_width = Math.min(total_mtul * scale_factor, 100); // Cap width at 100%
                        const bar_class = total_mtul > 1400 ? 'high-value' : '';
                        const text_class = total_mtul > 1400 ? 'high-value-text' : '';
                        const display_text = `${total_mtul.toFixed(2)} MTUL - ${total_quantity} Adet`;

                        table_html += `
                            <tr>
                                <td style="width: 20%;">${display_date}</td>
                                <td style="width: 20%;">${workstation}</td>
                                <td class="total-mtul-cell" style="width: 60%;">
                                    <div class="mtul-bar-container">
                                        <div class="mtul-bar ${bar_class}" style="width: ${bar_width}%;"></div>
                                    </div>
                                     <span class="total-text ${text_class}">${display_text}</span>
                                </td>
                            </tr>
                        `;
                    });
                });

                table_html += `
                        </tbody>
                    </table>
                `;

                $chart.html(table_html);

            } catch (error) {
                $chart.html(`
                    <div style="text-align: center; color: #ff0000; padding: 24px;">
                        Grafik oluşturulurken bir hata oluştu: ${error.message}
                    </div>
                `);
            }
        }
    });
}

function add_mtul_threshold_line(chart) {
    // Bu fonksiyonun içeriği mevcut kodda bulunmamaktadır.
    // Bu nedenle, bu fonksiyonun içeriği burada kalacak.
}