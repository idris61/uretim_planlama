// Custom script for Delivery Note: Show Assembly/Accessory Materials as HTML table

frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        update_assembly_accessory_html(frm);
    },
    items_on_form_rendered: function(frm) {
        update_assembly_accessory_html(frm);
    }
});

function update_assembly_accessory_html(frm) {
    let sales_orders = [];
    if (frm.doc.items && frm.doc.items.length > 0) {
        frm.doc.items.forEach(function(row) {
            if (row.against_sales_order && !sales_orders.includes(row.against_sales_order)) {
                sales_orders.push(row.against_sales_order);
            }
        });
    }
    if (sales_orders.length === 0) {
        if (frm.fields_dict.assembly_accessory_html) {
            frm.fields_dict.assembly_accessory_html.$wrapper.html("");
        }
        return;
    }
    frappe.call({
        method: "uretim_planlama.uretim_planlama.api.get_assembly_accessory_materials",
        args: { sales_orders: JSON.stringify(sales_orders) },
        callback: function(r) {
            if(r.message && r.message.length > 0) {
                // Siparişe göre satır renkleri için sales_order -> renk eşlemesi
                let orderColors = {};
                let colorPalette = ["#fff", "#f9f9fc", "#f3f7fa", "#f8f5f2", "#f6f6fa"];
                let orderList = [];
                r.message.forEach(function(item) {
                    if (!orderList.includes(item.sales_order)) {
                        orderList.push(item.sales_order);
                    }
                });
                orderList.forEach(function(order, idx) {
                    orderColors[order] = colorPalette[idx % colorPalette.length];
                });
                let html = `
                    <div style="font-weight:bold; color:#b71c1c; font-size:1.2rem; margin-bottom:10px;">Montaj / Yardımcı Malzeme Tablosu</div>
                    <div style="background:#ffebee; border-left:4px solid #b71c1c; color:#b71c1c; font-weight:bold; padding:10px 16px; margin-bottom:12px; border-radius:6px; display:flex; align-items:center;">
                        <span style="font-size:1.2em; margin-right:8px;">&#9888;</span>
                        Montaj / Yardımcı Malzeme teslimatını unutmayın!!!
                    </div>
                    <table class="table table-bordered" style="background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 2px 8px #eee;">
                        <thead style="background:#f5f5f5;">
                            <tr>
                                <th>Satış Siparişi</th>
                                <th>Ürün Kodu</th>
                                <th>Ürün Adı</th>
                                <th style="text-align:left">Miktar</th>
                                <th>Birim</th>
                            </tr>
                        </thead>
                        <tbody>`;
                r.message.forEach(function(item) {
                    let bg = orderColors[item.sales_order] || "#fff";
                    html += `<tr style="background:${bg}">
                        <td>${frappe.utils.escape_html(item.sales_order)}</td>
                        <td>${frappe.utils.escape_html(item.stock_code)}</td>
                        <td>${frappe.utils.escape_html(item.stock_name)}</td>
                        <td style="text-align:left">${frappe.utils.escape_html(item.qty)}</td>
                        <td>${frappe.utils.escape_html(item.uom || "")}</td>
                    </tr>`;
                });
                html += `</tbody></table>`;
                if (frm.fields_dict.assembly_accessory_html) {
                    frm.fields_dict.assembly_accessory_html.$wrapper.html(html);
                }
            } else {
                if (frm.fields_dict.assembly_accessory_html) {
                    frm.fields_dict.assembly_accessory_html.$wrapper.html('<div style="color: #888;">Bu sipariş(ler) için montaj/yardımcı malzeme bulunamadı.</div>');
                }
            }
        }
    });
} 