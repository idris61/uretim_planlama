frappe.pages['accessory_delivery_package_create'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Aksesuar Teslimat Paketi Oluştur'),
        single_column: true
    });

    $(frappe.render_template('accessory_delivery_package_create', {})).appendTo(page.body);

    // OpTi No dropdown'u doldur
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.api.get_approved_opti_nos',
        callback: function(r) {
            let $select = $('#adp_opti_no');
            $select.empty().append('<option value="">Seçiniz</option>');
            (r.message || []).forEach(function(row) {
                if (row.opti_no) {
                    $select.append(`<option value="${row.name}">${row.opti_no}</option>`);
                }
            });
        }
    });
};

frappe.templates['accessory_delivery_package_create'] =
`<div class="adp-form">
  <div class="row">
    <div class="col-md-6">
      <div class="form-group">
        <label>OpTi No</label>
        <select class="form-control" id="adp_opti_no"><option value="">Seçiniz</option></select>
      </div>
    </div>
    <div class="col-md-6">
      <div class="form-group">
        <label>Satış Siparişi</label>
        <select class="form-control" id="adp_sales_order"><option value="">Seçiniz</option></select>
      </div>
    </div>
  </div>
  <div class="form-group mt-2">
    <button class="btn btn-primary" id="adp_search_btn">Malzeme Listesini Getir</button>
  </div>
  <div id="adp_alert" style="display:none; margin-top:10px;"></div>
  <hr/>
  <div id="adp_materials_section" style="display:none;">
    <h4>Malzeme Listesi</h4>
    <table class="table table-bordered" id="adp_materials_table">
      <thead><tr><th>Ürün Kodu</th><th>Ürün Adı</th><th>Miktar</th><th>Birim</th></tr></thead>
      <tbody></tbody>
    </table>
    <div id="adp_materials_empty" class="text-center text-muted" style="display:none;">Malzeme bulunamadı.</div>
    <div class="form-group">
      <label>Teslim Alan Kişi</label>
      <input type="text" class="form-control" id="adp_delivered_to" placeholder="Teslim alan kişi...">
    </div>
    <div class="form-group">
      <label>Açıklama</label>
      <textarea class="form-control" id="adp_notes" placeholder="Varsa ek açıklama..."></textarea>
    </div>
    <button class="btn btn-success" id="adp_create_btn">Teslimat Paketi Oluştur</button>
  </div>
</div>
`;

// OpTi No seçilince Sales Order dropdown'ı doldur
$(document).on('change', '#adp_opti_no', function() {
    let production_plan = $(this).val();
    let custom_opti_no = $(this).find('option:selected').text();
    $('#adp_opti_no').data('custom_opti_no', custom_opti_no);
    $('#adp_opti_no').data('production_plan', production_plan);
    let $so = $('#adp_sales_order');
    $so.empty().append('<option value="">Seçiniz</option>');
    if (!production_plan) return;
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.api.get_sales_orders_by_opti',
        args: { opti_no: production_plan },
        callback: function(r) {
            (r.message || []).forEach(function(so) {
                $so.append(`<option value="${so}">${so}</option>`);
            });
        }
    });
});

// Malzeme listesini getir
$(document).on('click', '#adp_search_btn', function() {
    let opti_no = $('#adp_opti_no').val();
    let sales_order = $('#adp_sales_order').val();
    let $alert = $('#adp_alert');
    $alert.hide();
    if (!opti_no) {
        $alert.html('<div class="alert alert-danger">Lütfen OpTi No seçiniz.</div>').show();
        return;
    }
    if (!sales_order) {
        $alert.html('<div class="alert alert-danger">Lütfen Satış Siparişi seçiniz.</div>').show();
        return;
    }
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.api.get_bom_materials_by_sales_order',
        args: { sales_order: sales_order },
        callback: function(r) {
            let materials = r.message || [];
            let $tbody = $('#adp_materials_table tbody');
            $tbody.empty();
            if (materials.length === 0) {
                $('#adp_materials_empty').show();
            } else {
                $('#adp_materials_empty').hide();
                materials.forEach(function(item) {
                    $tbody.append(`<tr><td>${item.item_code || ''}</td><td>${item.item_name || ''}</td><td>${item.qty || ''}</td><td>${item.uom || ''}</td></tr>`);
                });
            }
            $('#adp_materials_section').show();
        },
        error: function(err) {
            $alert.html('<div class="alert alert-danger">Malzeme listesi alınamadı.</div>').show();
        }
    });
});

// Teslimat Paketi Oluştur
$(document).on('click', '#adp_create_btn', function() {
    let production_plan = $('#adp_opti_no').data('production_plan');
    let opti_no = $('#adp_opti_no').data('custom_opti_no');
    let sales_order = $('#adp_sales_order').val();
    let delivered_to = $('#adp_delivered_to').val();
    let notes = $('#adp_notes').val();
    let item_list = [];
    let $alert = $('#adp_alert');
    $alert.hide();
    $('#adp_materials_table tbody tr').each(function() {
        let tds = $(this).find('td');
        item_list.push({
            item_code: $(tds[0]).text(),
            item_name: $(tds[1]).text(),
            qty: parseFloat($(tds[2]).text()),
            uom: $(tds[3]).text()
        });
    });
    if (!opti_no || !sales_order) {
        $alert.html('<div class="alert alert-danger">Lütfen OpTi No ve Satış Siparişi seçiniz.</div>').show();
        return;
    }
    if (item_list.length === 0) {
        $alert.html('<div class="alert alert-danger">Malzeme listesi boş, teslimat paketi oluşturulamaz.</div>').show();
        return;
    }
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.api.create_delivery_package',
        args: {
            data: {
                opti_no: opti_no,
                production_plan: production_plan,
                sales_order: sales_order,
                delivered_to: delivered_to,
                notes: notes,
                item_list: item_list
            }
        },
        callback: function(r) {
            if (r.message && r.message.name) {
                $alert.html('<div class="alert alert-success">Teslimat Paketi başarıyla oluşturuldu: ' + r.message.name + '</div>').show();
                // Formu sıfırla
                $('#adp_opti_no').val('');
                $('#adp_sales_order').empty().append('<option value="">Seçiniz</option>');
                $('#adp_materials_section').hide();
                $('#adp_delivered_to').val('');
                $('#adp_notes').val('');
            } else {
                $alert.html('<div class="alert alert-danger">Teslimat Paketi oluşturulamadı.</div>').show();
            }
        },
        error: function(err) {
            $alert.html('<div class="alert alert-danger">Teslimat Paketi oluşturulamadı.</div>').show();
        }
    });
}); 