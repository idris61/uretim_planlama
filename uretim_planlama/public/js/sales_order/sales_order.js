frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        if (!frm.doc.__islocal && frm.fields_dict['custom_raw_materials_html']) {
            frappe.call({
                method: "uretim_planlama.sales_order_hooks.raw_materials.get_sales_order_raw_materials",
                args: { sales_order: frm.doc.name },
                callback: function(r) {
                    if (r.message) {
                        let html = `
                        <div style=\"display:flex;gap:10px;align-items:center;\">
                        <button class=\"btn btn-default\" type=\"button\" data-toggle=\"collapse\" data-target=\"#raw_materials_table\" aria-expanded=\"false\" aria-controls=\"raw_materials_table\">
                            Gerekli Hammaddeler ve Stoklar
                        </button>
                        </div>
                        <div class=\"collapse\" id=\"raw_materials_table\">
                        <table class=\"table table-bordered\"><tr>
                            <th>Hammadde Kodu</th><th>Hammadde Adı</th><th>Sipariş Ürünleri</th><th>Toplam İhtiyaç Miktarı</th><th>Toplam Stok</th><th>Rezerve Miktar</th><th>Rezerv Depo Stok</th></tr>`;
                        r.message.forEach(row => {
                            let rowClass = (parseFloat(row.qty) > parseFloat(row.stock)) ? 'table-danger' : '';
                            let qtyFormatted = (row.qty !== undefined && row.qty !== null) ? parseFloat(row.qty).toFixed(2) : '';
                            let reservedQtyFormatted = (row.reserved_qty !== undefined && row.reserved_qty !== null) ? parseFloat(row.reserved_qty).toFixed(2) : '';
                            let itemLink = `<a href='/app/item/${encodeURIComponent(row.raw_material)}' target='_blank'>${row.raw_material}</a>`;
                            html += `<tr class='${rowClass}'>
                                <td>${itemLink}</td>
                                <td>${row.item_name || ''}</td>
                                <td>${row.so_items}</td>
                                <td>${qtyFormatted}</td>
                                <td>${row.stock}</td>
                                <td>${reservedQtyFormatted}</td>
                                <td>${row.reserve_warehouse_stock}</td>
                            </tr>`;
                        });
                        html += "</table></div>";
                        frm.fields_dict['custom_raw_materials_html'].wrapper.innerHTML = html;
                    }
                }
            });
        }
    },
    validate: function(frm) {
        frappe.call({
            method: "uretim_planlama.sales_order_hooks.raw_materials.get_sales_order_raw_materials",
            args: { sales_order: frm.doc.name },
            async: false,
            callback: function(r) {
                if (r.message) {
                    let uyarilar = [];
                    r.message.forEach(row => {
                        let toplam_ihtiyac = parseFloat(row.qty) || 0;
                        let rezerve = parseFloat(row.reserved_qty) || 0;
                        let stok = parseFloat(row.stock) || 0;
                        if ((toplam_ihtiyac + rezerve) > stok) {
                            uyarilar.push(
                                `${row.raw_material} için toplam ihtiyaç (${toplam_ihtiyac}) + rezerve (${rezerve}) > stok (${stok})!`
                            );
                        }
                    });
                    if (uyarilar.length > 0) {
                        frappe.msgprint({
                            title: __('Stok Yetersiz!'),
                            message: uyarilar.join('<br>'),
                            indicator: 'red'
                        });
                        frappe.validated = false;
                    }
                }
            }
        });
    }
}); 