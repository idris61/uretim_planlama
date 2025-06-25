function get_and_render_panel() {
    const args = {
        profil: $('#profil-filter').val() || undefined,
        depo: $('#depo-filter').val() || undefined,
        scrap: $('#scrap-filter').is(':checked') ? 1 : undefined
    };
    // ERPNext toplam stok tablosu
    if (!args.scrap) {
        frappe.call({
            method: 'uretim_planlama.uretim_planlama.api.get_total_stock_summary',
            args: { profil: args.profil, depo: args.depo },
            callback: function(r) {
                console.log('API get_total_stock_summary response:', r.message);
                render_erpnext_stok_tablo(r.message || []);
            }
        });
    } else {
        $('#erpnext-stok-tablo').html('');
    }
    // Boy bazında stok tablosu (parça profilleri hariç)
    if (!args.scrap) {
        frappe.call({
            method: 'uretim_planlama.uretim_planlama.api.get_profile_stock_by_length',
            args: { profil: args.profil, scrap: 0 },
            callback: function(r) {
                console.log('API get_profile_stock_by_length response:', r.message);
                render_boy_bazinda_tablo(r.message || []);
            }
        });
    } else {
        $('#profil-boy-tablo').html('');
    }
    // Parça profil kayıtları tablosu
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.api.get_scrap_profile_entries',
        args: { profile_code: args.profil },
        callback: function(r) {
            console.log('API get_scrap_profile_entries response:', r.message);
            render_scrap_profile_tablo(r.message || []);
        }
    });
}

function render_erpnext_stok_tablo(data) {
    console.log('render_erpnext_stok_tablo data:', data);
    let toplam = 0, toplam_rezerv = 0, toplam_kullanilabilir = 0;
    data.forEach(row => {
        toplam += Number(row.toplam_stok_mtul) || 0;
        toplam_rezerv += Number(row.rezerv_mtul) || 0;
        toplam_kullanilabilir += Number(row.kullanilabilir_mtul) || 0;
    });
    let tablo = `<table class="table table-bordered table-hover table-striped" style="background: #fff; border-radius: 8px; overflow: hidden;">
        <thead style="background: #e9ecef; color: #2c3e50; font-weight: bold;">
            <tr>
                <th>#</th>
                <th>Depo</th>
                <th>Profil</th>
                <th>Profil Adı</th>
                <th>Toplam Stok (mtül)</th>
                <th>Toplam Rezerv (mtül)</th>
                <th>Kullanılabilir (mtül)</th>
            </tr>
        </thead>
        <tbody>`;
    data.forEach((row, i) => {
        let kullanilabilir = Number(row.kullanilabilir_mtul) || 0;
        let rezerv = Number(row.rezerv_mtul) || 0;
        let rowClass = '';
        if (kullanilabilir <= 0) {
            rowClass = 'table-danger';
        } else if (rezerv > 0) {
            rowClass = 'table-warning';
        }
        tablo += `<tr class='${rowClass}'>
            <td>${i+1}</td>
            <td>${row.depo}</td>
            <td>${row.profil}</td>
            <td>${row.profil_adi}</td>
            <td>${row.toplam_stok_mtul}</td>
            <td>${row.rezerv_mtul}</td>
            <td>${row.kullanilabilir_mtul}</td>
        </tr>`;
    });
    // Genel toplam satırı
    tablo += `<tr style="font-weight:bold; background:linear-gradient(90deg,#e3f2fd 60%,#b3c6e7 100%); font-size:1.08em;">
        <td colspan="4" style="text-align:right;">Genel Toplam</td>
        <td>${toplam}</td>
        <td>${toplam_rezerv}</td>
        <td>${toplam_kullanilabilir}</td>
    </tr>`;
    tablo += '</tbody></table>';
    $('#erpnext-stok-tablo').html(tablo);
    console.log('Profil Stok Paneli JS loaded');
} 
