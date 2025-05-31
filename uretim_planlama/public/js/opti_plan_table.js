frappe.provide('uretim_planlama');

frappe.ui.form.on('Production Plan', {
    refresh(frm) {
        // Tabloyu oluştur ve veriyi yükle
        setup_opti_plan_table(frm);
    },

    // Başka form olayları gerekirse buraya eklenebilir (e.g., after_save, before_submit)
});

function setup_opti_plan_table(frm) {
    const po_items_wrapper = frm.fields_dict["po_items"].wrapper;

    // Tablonun zaten var olup olmadığını kontrol et
    if ($('#opti-plan-table-wrapper').length) {
        // Varsa sadece veriyi yenile
        load_opti_plan_table(frm);
        return;
    }

    // Tablo container'ını oluştur ve po_items altına ekle
    const $wrapper = $(
        `<div id="opti-plan-table-wrapper" style="
            margin-top: 24px;
            margin-bottom: 24px;
            padding: 16px;
            background: #ffffff;
            border: 1px solid #e3e3e3;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
            width: 100%;
        ">
            <h5 style="margin-bottom: 12px; font-weight: 600;">Optimizasyon Planı Özeti</h5>
            <div id="opti-plan-table"></div>
        </div>`
    ).insertAfter(po_items_wrapper);

    // Veriyi yükle
    load_opti_plan_table(frm);
}

function load_opti_plan_table(frm) {
    const $table_div = $('#opti-plan-table');
    $table_div.empty(); // Mevcut içeriği temizle

    const grouped_data = {};

    // po_items listesini dolaş ve satış siparişine göre grupla
    (frm.doc.po_items || []).forEach(item => {
        // Satış Siparişi bilgisini al (varsayımsal olarak item üzerinde veya parent doc üzerinde)
        // Gerçek alan adı projenize göre değişebilir. Örnek olarak 'sales_order' veya 'custom_sales_order' kullanıyorum.
        // Eğer Sales Order bilgisi po_items üzerinde yoksa, Production Plan dokümanından almanız gerekebilir.
        // Bu örnekte po_items üzerinde olduğunu varsayıyorum.
        const sales_order = item.sales_order || 'Belirtilmemiş Sipariş';
        
        // Diğer sütun bilgileri (varsayımsal alan adları)
        const seri = item.custom_serial || ''; // Corrected field name
        const renk = item.custom_color || ''; // Örnek alan adı
        const workstation = item.custom_workstation || '';
        const planned_qty = item.planned_qty || 0;
        const planned_start_date = item.planned_start_date || '';

        if (!grouped_data[sales_order]) {
            grouped_data[sales_order] = {
                sales_order: sales_order,
                seri: new Set(), // Benzersiz seriler için Set
                renk: new Set(), // Benzersiz renkler için Set
                workstation: new Set(), // Benzersiz iş istasyonları için Set
                total_planned_qty: 0,
                planned_start_date: planned_start_date, // İlk öğenin bilgisini al - Birden fazla tarih olabilir, şimdilik ilkini alıyoruz.
                items: []
            };
        }

        // Benzersiz değerleri Set'lere ekle
        if (seri) grouped_data[sales_order].seri.add(seri);
        if (renk) grouped_data[sales_order].renk.add(renk);
        if (workstation) grouped_data[sales_order].workstation.add(workstation);
        
        // Ensure total_mtul is initialized
        if (grouped_data[sales_order].total_mtul === undefined) {
            grouped_data[sales_order].total_mtul = 0;
        }

        // Calculate MTUL for the current item and add to total
        const mtul_per_piece = parseFloat(item.custom_mtul_per_piece) || 0;
        const planned_qty_item = parseFloat(item.planned_qty) || 0;

        grouped_data[sales_order].total_planned_qty += planned_qty;
        grouped_data[sales_order].total_mtul += mtul_per_piece * planned_qty_item;
        
        grouped_data[sales_order].items.push(item); // Detayları saklamak isterseniz
    });

    //console.log("[Opti Plan Table] Gruplanmış Veri:", grouped_data);

    // Tablo HTML'ini oluştur
    let table_html = `
        <table class="table table-bordered table-sm" style="font-size: 13px; width: 100%; border-collapse: collapse; border: 1px solid #dee2e6;">
            <thead style="background-color: #e9ecef;">
                <tr>
                    <th style="border: 1px solid #dee2e6; padding: 8px; width: 130px; text-align: left;">Satış Siparişi</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; width: 120px; text-align: left;">Seri</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; width: 160px; text-align: left;">Renk</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; width: 130px; text-align: left;">İş İstasyonu</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; width: 110px; text-align: right;">Planlanan Miktar</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; width: 110px; text-align: right;">Toplam MTUL</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; width: 140px; text-align: left;">Planlanan Başlangıç Tarihi</th>
                </tr>
            </thead>
            <tbody>
    `;

    Object.values(grouped_data).forEach((group, index) => {
        // Planlanan Başlangıç Tarihi formatlama (isteğe bağlı)
        let display_date = group.planned_start_date;
        if (display_date) {
             try {
                 display_date = frappe.datetime.obj_to_user(frappe.datetime.str_to_obj(display_date));
             } catch(e) {
                 console.warn("Geçersiz tarih formatı:", group.planned_start_date);
             }
        }

        // Benzersiz değerleri birleştir
        const seri_str = Array.from(group.seri).join(', ');
        const renk_str = Array.from(group.renk).join(', ');
        const workstation_str = Array.from(group.workstation).join(', ');

        // Satır arka plan rengini belirle
        const row_bg_color = index % 2 === 0 ? '#ffffff' : '#f8f9fa'; // Alternatif renkler (beyaz ve hafif gri)

        table_html += `
            <tr style="border-bottom: 1px solid #dee2e6; background-color: ${row_bg_color};">
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">${group.sales_order}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">${seri_str}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">${renk_str}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">${workstation_str}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">${group.total_planned_qty}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">${(group.total_mtul || 0).toFixed(2)}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">${display_date}</td>
            </tr>
        `;
    });

    table_html += `
            </tbody>
        </table>
    `;

    $table_div.html(table_html);

    // Calculate grand totals
    let grand_total_qty = 0;
    let grand_total_mtul = 0;

    Object.values(grouped_data).forEach(group => {
        grand_total_qty += group.total_planned_qty || 0;
        grand_total_mtul += group.total_mtul || 0;
    });

    // Append total row to the table
    const $table = $table_div.find('table');
    $table.append(`
        <tfoot style="font-weight: bold;">
            <tr>
                <td colspan="4" style="text-align: right; border: 1px solid #dee2e6; padding: 8px;">Genel Toplam:</td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">${grand_total_qty}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: right;">${grand_total_mtul.toFixed(2)}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px;"></td>
            </tr>
        </tfoot>
    `);
} 