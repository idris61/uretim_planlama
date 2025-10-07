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
                if (from && to) {
                    if (window.load_cutting_table) window.load_cutting_table(from, to);
                }
            };

            $('#cutting-table-refresh-btn').on('click', refresh_table);
            from_date.$input.on('change', refresh_table);
            to_date.$input.on('change', refresh_table);

            refresh_table();
        }

        // Helper fonksiyonlar
        const sortByDateAndWorkstation = (a, b) => {
            const [da, wsa] = a.split('::');
            const [db, wsb] = b.split('::');
            return new Date(da) - new Date(db) || String(wsa).localeCompare(String(wsb));
        };

        const calculateBarWidths = (mtul, maxMtul) => {
            const BASE_WIDTH_PCT = 70;
            const EXTRA_WIDTH_PCT = 30;
            
            const underWidth = mtul <= 1400 
                ? (mtul / 1400) * BASE_WIDTH_PCT 
                : BASE_WIDTH_PCT;
            const overWidth = mtul > 1400 
                ? Math.min(((mtul - 1400) / (maxMtul - 1400)) * EXTRA_WIDTH_PCT, EXTRA_WIDTH_PCT) 
                : 0;
            
            return { underWidth, overWidth };
        };

        const getWsColors = (ws) => {
            const name = String(ws || '').toLowerCase();
            const colors = {
                kaban: { base: 'linear-gradient(90deg,#76baff 0%, #1976d2 100%)', over: 'linear-gradient(90deg,#ff5858 0%, #f09819 100%)' },
                murat: { base: 'linear-gradient(90deg,#43e97b 0%, #38f9d7 100%)', over: 'linear-gradient(90deg,#ff5858 0%, #f09819 100%)' },
                bottero: { base: 'linear-gradient(90deg,#64b5f6 0%, #1976d2 100%)', over: 'linear-gradient(90deg,#ff5858 0%, #f09819 100%)' }
            };
            
            for (const [key, value] of Object.entries(colors)) {
                if (name.includes(key)) return value;
            }
            return { base: 'linear-gradient(90deg,#43e97b 0%, #38f9d7 100%)', over: 'linear-gradient(90deg,#ff5858 0%, #f09819 100%)' };
        };

        const renderTableRow = (date, workstation, mtul, qty, maxMtul, colors, isGreen = false) => {
            const formattedDate = frappe.datetime.str_to_user(date);
            const { underWidth, overWidth } = calculateBarWidths(mtul, maxMtul);
            const bgColor = isGreen ? 'background-color: #f0fdf4;' : '';
            const baseColor = isGreen ? '#86efac' : colors.base;
            const overColor = isGreen ? '#fbbf24' : colors.over;
            const textColor = isGreen ? 'color:#16a34a;' : 'color:#374151;';
            const label = isGreen ? '(taslak)' : '';

            return `
                <tr style="${bgColor}">
                    <td style="padding: 8px;">${formattedDate}</td>
                    <td style="padding: 8px;">${workstation || '-'}</td>
                    <td style="padding: 8px;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <div style="flex:1; min-width:200px; height:16px; background:#f1f3f5; border-radius:8px; overflow:hidden; position:relative;">
                                <div title="0-1400 MTUL ${label}" style="height:100%; width:${underWidth}%; background:${baseColor};"></div>
                                ${overWidth > 0 ? `<div title="1400+ MTUL ${label}" style="height:100%; width:${overWidth}%; background:${overColor}; position:absolute; left:${underWidth}%; top:0;"></div>` : ''}
                            </div>
                            <div style="white-space:nowrap; font-weight:600; ${textColor}">${mtul.toFixed(0)} MTUL • ${qty}</div>
                        </div>
                    </td>
                </tr>
            `;
        };

        // load_cutting_table fonksiyonunu window'a ekle
        window.load_cutting_table = function(from_date, to_date) {
            frappe.call({
                method: "uretim_planlama.uretim_planlama.api.get_daily_cutting_table",
                args: { from_date, to_date },
                callback: function (r) {
                    const $table = $('#cutting-matrix-table');
                    $table.empty();

                    let backend_data = r.message || [];
                    
                    if (!backend_data || backend_data.length === 0) {
                        $table.html(`
                            <div style="text-align: center; color: #888; padding: 24px;">
                                📊 Seçilen tarih aralığında (${frappe.datetime.str_to_user(from_date)} - ${frappe.datetime.str_to_user(to_date)}) görüntülenecek veri bulunamadı.
                            </div>
                        `);
                        return;
                    }

                    // Üretim türü filtresi
                    const productionType = $('#production-type-select').val && $('#production-type-select').val();
                    const isPVC = productionType === 'pvc';
                    const isCam = productionType === 'cam';
                    if (productionType) {
                    backend_data = backend_data.filter(row => {
                        if (isPVC) return row.workstation && (row.workstation.includes('Murat') || row.workstation.includes('Kaban'));
                        if (isCam) return row.workstation && row.workstation.includes('Bottero');
                        return true;
                    });
                    }

                    // Taslak plan özetini hazırla
                    const draftSummary = {};
                    if (frm && frm.doc && frm.doc.docstatus === 0 && Array.isArray(frm.doc.po_items)) {
                        (frm.doc.po_items || []).forEach(row => {
                            if (!row || !row.custom_workstation || !row.planned_start_date) return;
                            if (isPVC && !(row.custom_workstation.includes('Murat') || row.custom_workstation.includes('Kaban'))) return;
                            if (isCam && !row.custom_workstation.includes('Bottero')) return;

                            const mtulPerPiece = parseFloat(row.custom_mtul_per_piece) || 0;
                            const qty = parseFloat(row.planned_qty) || 0;
                            if (mtulPerPiece <= 0 || qty <= 0) return;

                            const dateObj = frappe.datetime.str_to_obj(row.planned_start_date);
                            if (!dateObj) return;
                            const isoDate = dateObj.toISOString().split('T')[0];
                            const key = `${isoDate}::${row.custom_workstation}`;

                            if (!draftSummary[key]) draftSummary[key] = { date: isoDate, workstation: row.custom_workstation, mtul: 0, qty: 0 };
                            draftSummary[key].mtul += mtulPerPiece * qty;
                            draftSummary[key].qty += qty;
                        });
                    }

                    // Backend map
                    const backendMap = {};
                    backend_data.forEach(r => {
                        const key = `${r.date}::${r.workstation}`;
                        backendMap[key] = { date: r.date, workstation: r.workstation, mtul: Number(r.total_mtul || 0), qty: Number(r.total_quantity || 0) };
                    });

                    // Maksimum MTUL hesapla
                    const allKeys = Array.from(new Set([...Object.keys(backendMap), ...Object.keys(draftSummary)]));
                    const maxTotalMtul = Math.max(2000, ...allKeys.map(k => (backendMap[k]?.mtul || 0) + (draftSummary[k]?.mtul || 0)));

                    // Backend tablosu
                    let tableHTML = `
                        <table class="table table-bordered" style="width: 100%; font-size: 12px; margin-bottom: 16px;">
                            <thead style="background-color: #f8f9fa;">
                                <tr>
                                    <th style="padding: 8px; text-align: left; width: 140px;">Tarih</th>
                                    <th style="padding: 8px; text-align: left; width: 220px;">İstasyon</th>
                                    <th style="padding: 8px; text-align: left;">Toplam MTUL / m2 - Toplam Adet</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    Object.keys(backendMap).sort(sortByDateAndWorkstation).forEach(key => {
                        const b = backendMap[key];
                        const colors = getWsColors(b.workstation);
                        tableHTML += renderTableRow(b.date, b.workstation, b.mtul, b.qty, maxTotalMtul, colors, false);
                    });

                    tableHTML += `</tbody></table>`;

                    // Taslak tablosu
                    const draftKeys = Object.keys(draftSummary);
                    if (draftKeys.length > 0) {
                        tableHTML += `
                            <h6 style="margin-bottom: 8px; font-weight: 600; color: #16a34a;">📋 Yeni Planlama (Taslak)</h6>
                            <table class="table table-bordered" style="width: 100%; font-size: 12px; margin-bottom: 16px;">
                                <thead style="background-color: #dcfce7;">
                                    <tr>
                                        <th style="padding: 8px; text-align: left; width: 140px;">Tarih</th>
                                        <th style="padding: 8px; text-align: left; width: 220px;">İstasyon</th>
                                        <th style="padding: 8px; text-align: left;">Toplam MTUL / m2 - Toplam Adet</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                        `;

                        draftKeys.sort(sortByDateAndWorkstation).forEach(key => {
                            const d = draftSummary[key];
                            const colors = getWsColors(d.workstation);
                            tableHTML += renderTableRow(d.date, d.workstation, d.mtul, d.qty, maxTotalMtul, colors, true);
                        });

                        tableHTML += `</tbody></table>`;
                    }

                    $table.html(tableHTML);
                }
            });
        }
    }
}); 
