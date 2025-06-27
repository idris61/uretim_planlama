frappe.ui.form.on('Purchase Receipt Item', {
    is_profile: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.is_profile) {
            frappe.msgprint(__('Profil ile ilgili alanları doldurmak için satır detayına (kalem simgesi) tıklayın.'));
        }
    },
    validate: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (!row.is_profile && (row.profile_length || row.profile_length_qty)) {
            frappe.model.set_value(cdt, cdn, 'profile_length', null);
            frappe.model.set_value(cdt, cdn, 'profile_length_qty', null);
            frappe.msgprint(__('"Profile Length" ve "Profile Length Qty" alanlarını doldurmak için önce "Is Profile" kutucuğunu işaretleyin.'));
        }
    },
    form_render: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        var grid_row = frm.fields_dict.items.grid.grid_rows_by_docname[cdn];
        if (grid_row && typeof grid_row.toggle_field === "function") {
            var show = !!row.is_profile;
            grid_row.toggle_field('profile_length', show);
            grid_row.toggle_field('profile_length_qty', show);
        }
    },
    items_add: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        var show = !!row.is_profile;
        frm.fields_dict.items.grid.toggle_field('profile_length', show);
        frm.fields_dict.items.grid.toggle_field('profile_length_qty', show);
    },
    items_on_form_rendered: function(frm, grid_row) {
        var row = grid_row.doc;
        var show = !!row.is_profile;
        grid_row.toggle_field('profile_length', show);
        grid_row.toggle_field('profile_length_qty', show);
    }
}); 