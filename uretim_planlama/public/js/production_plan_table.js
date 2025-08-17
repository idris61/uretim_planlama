frappe.provide('uretim_planlama');

frappe.ui.form.on("Production Plan", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) return;

        const po_items_wrapper = frm.fields_dict["po_items"].wrapper;

        if (!$('#cutting-matrix-table-wrapper').length) {
            const today = frappe.datetime.get_today();
            const from_default = frappe.datetime.add_days(today, -10);
            const to_date_default = frappe.datetime.add_days(today, 10);

            $(
                `<div id="cutting-matrix-table-wrapper" style="
                    margin-bottom: 24px;
                    padding: 16px;
                    background: #ffffff;
                    border: 1px solid #e3e3e3;
                    border-radius: 8px;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
                    width: 100%;
                ">
                    <h5 style="margin-bottom: 12px; font-weight: 600;">Günlük Kesim İstasyonu Tablosu</h5>
                    <div class="field-area" style="margin-bottom: 12px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                        <div class="frappe-control" id="cutting-table-from-date" style="min-width: 120px; max-width: 120px;"></div>
                        <div class="frappe-control" id="cutting-table-to-date" style="min-width: 120px; max-width: 120px;"></div>
                        <button class="btn btn-sm btn-light" id="cutting-table-refresh-btn" style="height: 28px; width: 28px; padding: 0; font-size: 14px;" title="Tabloyu Yenile">
                            🔄
                        </button>
                    </div>
                    <div id="cutting-matrix-table"></div>
                </div>`).insertBefore(po_items_wrapper);

            const from_date = frappe.ui.form.make_control({
                df: {
                    fieldtype: "Date",
                    label: "",
                    fieldname: "cutting_table_from_date",
                    default: from_default,
                    reqd: 1
                },
                parent: $('#cutting-table-from-date'),
                only_input: true
            });

            const to_date = frappe.ui.form.make_control({
                df: {
                    fieldtype: "Date",
                    label: "",
                    fieldname: "cutting_table_to_date",
                    default: to_date_default,
                    reqd: 1
                },
                parent: $('#cutting-table-to-date'),
                only_input: true
            });

            from_date.make_input();
            from_date.set_value(from_default);

            to_date.make_input();
            to_date.set_value(to_date_default);

            const refresh_table = () => {
                const from = from_date.get_value();
                const to = to_date.get_value();
                if (from && to) load_cutting_table(from, to);
            };

            $('#cutting-table-refresh-btn').on('click', refresh_table);
            from_date.$input.on('change', refresh_table);
            to_date.$input.on('change', refresh_table);

            refresh_table();
        }

        // load_cutting_table fonksiyonunu window'a ekle
        window.load_cutting_table = function(from_date, to_date) {
            frappe.call({
                method: "uretim_planlama.uretim_planlama.api.get_daily_cutting_matrix",
                args: { from_date, to_date },
                callback: function (r) {
                    const $table = $('#cutting-matrix-table');
                    $table.empty();

                    let backend_data = r.message || [];
                    // Üretim türüne göre filtreleme (grafikteki seçiciye göre)
                    const productionType = $('#production-type-select').val();
                    const isPVC = productionType === 'pvc';
                    const isCam = productionType === 'cam';
                    backend_data = backend_data.filter(row => {
                        if (isPVC) return row.workstation && (row.workstation.includes('Murat') || row.workstation.includes('Kaban'));
                        if (isCam) return row.workstation && row.workstation.includes('Bottero');
                        return true;
                    });

                    // Geçici planları sadece docstatus 0 (taslak) iken ekle
                    let temp_data = [];
                    let temp_summary = {};
                    if (frm.doc.docstatus === 0) {
                        (frm.doc.po_items || []).forEach(row => {
                            if (!(row.custom_workstation && row.planned_start_date && row.custom_mtul_per_piece && row.planned_qty)) return;

                            // Üretim türüne göre filtrele
                            if (isPVC && !(row.custom_workstation.includes('Murat') || row.custom_workstation.includes('Kaban'))) return;
                            if (isCam && !row.custom_workstation.includes('Bottero')) return;

                            const date_obj = frappe.datetime.str_to_obj(row.planned_start_date);
                            if (!date_obj) return;
                            const date = date_obj.toISOString().split('T')[0];
                            const mtul = (parseFloat(row.custom_mtul_per_piece) || 0) * (parseFloat(row.planned_qty) || 0);
                            const quantity = parseFloat(row.planned_qty) || 0;

                            temp_data.push({
                                date: date,
                                workstation: row.custom_workstation,
                                mtul: mtul,
                                quantity: quantity
                            });
                        });

                        // Geçici veriyi tarih ve iş istasyonuna göre topla
                        temp_data.forEach(item => {
                            const key = `${item.date}::${item.workstation}`;
                            if (!temp_summary[key]) {
                                temp_summary[key] = {
                                    date: item.date,
                                    workstation: item.workstation,
                                    total_mtul: 0,
                                    total_quantity: 0,
                                };
                            }
                            temp_summary[key].total_mtul += item.mtul;
                            temp_summary[key].total_quantity += item.quantity;
                        });
                    }

                    // Backend ve geçici veriyi birleştir (Toplam MTUL ve Adet için)
                    const combined = {};

                    backend_data.forEach(row => {
                        const key = `${row.date}::${row.workstation}`;
                        combined[key] = {
                            date: row.date,
                            workstation: row.workstation,
                            total_mtul: row.total_mtul || 0,
                            total_quantity: row.total_quantity || 0,
                        };
                    });

                    Object.values(temp_summary).forEach(temp_row => {
                        const key = `${temp_row.date}::${temp_row.workstation}`;
                        if (!combined[key]) {
                            // Eğer backend'de bu gün/istasyon yoksa, tamamı geçicidir
                            combined[key] = {
                                date: temp_row.date,
                                workstation: temp_row.workstation,
                                total_mtul: temp_row.total_mtul,
                                total_quantity: temp_row.total_quantity,
                            };
                        } else {
                            // Backend'de varsa, geçici veriyi ekle
                            combined[key].total_mtul += temp_row.total_mtul;
                            combined[key].total_quantity += temp_row.total_quantity;
                        }
                    });

                    const rows = Object.values(combined)
                        .sort((a, b) => new Date(a.date) - new Date(b.date))
                        .map(row => {
                        const total_mtul = (row.total_mtul || 0);
                        const total_quantity = (row.total_quantity || 0);

                        // MTUL değerini 1400'e kadar ve 1400 sonrası olarak ayır (toplam değer üzerinden)
                        const mtul_under_1400 = Math.min(total_mtul, 1400);
                        const mtul_over_1400 = total_mtul > 1400 ? total_mtul - 1400 : 0;

                        // Toplam MTUL değeri üzerinden ölçeklendirme için maksimum değer
                        // Ana tabloda kullanılan max değeri burada da kullanalım
                        const max_overall_mtul = Math.max(...Object.values(combined).map(item => item.total_mtul || 0), ...Object.values(temp_summary).map(item => item.total_mtul || 0));
                        const max_mtul_for_scaling = Math.max(2000, max_overall_mtul * 1.1); // 2000 veya max toplamın %10 fazlası

                        // Segment genişliklerini yüzde olarak hesapla
                        const under_1400_percentage = (mtul_under_1400 / max_mtul_for_scaling) * 100;
                        const over_1400_percentage = (mtul_over_1400 / max_mtul_for_scaling) * 100;

                        // Tablo için renk belirleme (iş istasyonuna göre renk)
                        const base_color = row.workstation.includes("Kaban") ? '#944de0' : row.workstation.includes("Murat") ? '#e89225' : '#6c757d';

                        let display_date = row.date;
                        try {
                            const d = frappe.datetime.str_to_obj(row.date);
                            const dayName = d.toLocaleDateString('tr-TR', { weekday: 'long' });
                            display_date = `${frappe.datetime.obj_to_user(d)} (${dayName})`;
                        } catch (e) {
                            // Geçersiz tarih formatı - varsayılan değeri kullan
                        }

                        // Toplam etiketi
                        const total_label = `${total_mtul.toFixed(2)} MTUL - ${total_quantity} Adet`;

                        return `
                            <tr>
                                <td style="white-space: nowrap; font-weight: bold;">${display_date}</td>
                                <td style="color: ${base_color}; font-weight: bold;">${row.workstation}</td>
                                <td>
                                    <div style="position: relative; background: #f5f5f5; border: 1px solid #ddd; height: 24px; border-radius: 4px; overflow: hidden; display: flex; align-items: center;">
                                        ${mtul_under_1400 > 0 ? `<div style="width: ${under_1400_percentage}%; background: ${base_color}; height: 100%;"></div>` : ''}
                                        ${mtul_over_1400 > 0 ? `<div style="width: ${over_1400_percentage}%; background: red; height: 100%;"></div>` : ''}
                                        <span style="position: absolute; left: 8px; top: 0; line-height: 24px; font-size: 13px; font-weight: bold; color: #000; text-shadow: 1px 1px 2px #fff;">
                                            ${total_label}
                                        </span>
                                        ${mtul_over_1400 > 0 ? `
                                            <span style="position: absolute; left: ${under_1400_percentage}%; top: 0; line-height: 24px; font-size: 13px; font-weight: bold; color: white; text-shadow: 1px 1px 2px #000; padding-left: 4px;">
                                                +${mtul_over_1400.toFixed(2)}
                                            </span>
                                        ` : ''}
                                    </div>
                                </td>
                            </tr>
                        `;
                    }).join("\n");

                    const table_html = `
                        <table class="table table-bordered table-sm" style="font-size: 13px;">
                            <thead class="table-light">
                                <tr>
                                    <th style="width: 160px;">Tarih</th>
                                    <th style="width: 150px;">İstasyon</th>
                                    <th>Toplam MTUL / m2 - Toplam Adet</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${rows}
                            </tbody>
                        </table>
                    `;

                    // Yeni Eklenen Planlar listesi (Geçici Planlar)
                    const temp_rows = Object.values(temp_summary)
                        .sort((a, b) => new Date(a.date) - new Date(b.date))
                        .map(item => {
                            const total_mtul = item.total_mtul || 0;
                            const total_quantity = item.total_quantity || 0;

                            // MTUL değerini 1400'e kadar ve 1400 sonrası olarak ayır
                            const mtul_under_1400 = Math.min(total_mtul, 1400);
                            const mtul_over_1400 = total_mtul > 1400 ? total_mtul - 1400 : 0;

                            // Toplam MTUL değeri üzerinden ölçeklendirme için maksimum değer
                            // Ana tabloda kullanılan max değeri burada da kullanalım
                            const max_overall_mtul = Math.max(...Object.values(combined).map(item => item.total_mtul || 0), ...Object.values(temp_summary).map(item => item.total_mtul || 0));
                            const max_mtul_for_scaling = Math.max(2000, max_overall_mtul * 1.1);

                            // Segment genişliklerini yüzde olarak hesapla
                            const under_1400_percentage = (mtul_under_1400 / max_mtul_for_scaling) * 100;
                            const over_1400_percentage = (mtul_over_1400 / max_mtul_for_scaling) * 100;

                            // Tablo için renk belirleme (iş istasyonuna göre renk)
                            const base_color = item.workstation.includes("Kaban") ? '#944de0' : item.workstation.includes("Murat") ? '#e89225' : '#6c757d';

                            let display_date = item.date;
                            try {
                                const d = frappe.datetime.str_to_obj(item.date);
                                const dayName = d.toLocaleDateString('tr-TR', { weekday: 'long' });
                                display_date = `${frappe.datetime.obj_to_user(d)} (${dayName})`;
                            } catch (e) {
                                // Geçersiz tarih formatı - varsayılan değeri kullan
                            }

                            // Toplam etiketi
                            const total_label = `${total_mtul.toFixed(2)} MTUL - ${total_quantity} Adet`;

                            return `
                                <tr>
                                    <td style="white-space: nowrap; font-weight: bold;">${display_date}</td>
                                    <td style="color: ${base_color}; font-weight: bold;">${item.workstation}</td>
                                    <td>
                                        <div style="position: relative; background: #f5f5f5; border: 1px solid #ddd; height: 24px; border-radius: 4px; overflow: hidden; display: flex; align-items: center;">
                                            ${mtul_under_1400 > 0 ? `<div style="width: ${under_1400_percentage}%; background: #4CAF50; height: 100%;"></div>` : ''}
                                            ${mtul_over_1400 > 0 ? `<div style="width: ${over_1400_percentage}%; background: red; height: 100%;"></div>` : ''}
                                            <span style="position: absolute; left: 8px; top: 0; line-height: 24px; font-size: 13px; font-weight: bold; color: #000; text-shadow: 1px 1px 2px #fff;">
                                                ${total_label}
                                            </span>
                                            ${mtul_over_1400 > 0 ? `
                                                <span style="position: absolute; left: ${under_1400_percentage}%; top: 0; line-height: 24px; font-size: 13px; font-weight: bold; color: white; text-shadow: 1px 1px 2px #000; padding-left: 4px;">
                                                    +${mtul_over_1400.toFixed(2)}
                                                </span>
                                            ` : ''}
                                        </div>
                                    </td>
                                </tr>
                            `;
                        }).join("\n");

                    const temp_table_html = `
                        ${temp_rows ? `
                            <div style="margin-top: 24px;">
                                <h5 style="margin-bottom: 12px; font-weight: 600; color: green;">Yeni Eklenen Planlar (Kaydedilmemiş)</h5>
                                <table class="table table-bordered table-sm" style="font-size: 13px;">
                                    <thead class="table-light">
                                        <tr>
                                            <th style="width: 160px;">Tarih</th>
                                            <th style="width: 150px;">İstasyon</th>
                                            <th>Toplam MTUL / m2 - Toplam Adet</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${temp_rows}
                                    </tbody>
                                </table>
                            </div>
                        ` : ''}
                    `;

                    // Tablo ve listeyi container'a ekle
                    $table.html(table_html + temp_table_html);

                }
            });
        }
    }
}); 