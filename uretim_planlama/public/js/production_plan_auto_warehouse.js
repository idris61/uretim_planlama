frappe.ui.form.on("Production Plan", {
	custom_get_glass_items(frm) {
		set_for_warehouse_by_group(frm, "Camlar", "CAM ÜRETİM DEPO - O");
	},
	custom_get_pvc_items(frm) {
		set_for_warehouse_by_group(frm, "PVC", "PVC ÜRETİM DEPO - O");
	},
	transfer_materials(frm) {
		try_autoset_for_warehouse_from_po_items(frm);
	}
});

function set_for_warehouse_by_group(frm, groupName, warehouseName) {
	// Hedef depo alanını anında set et
	frm.set_value("for_warehouse", warehouseName);
	frm.refresh_field("for_warehouse");
}

function try_autoset_for_warehouse_from_po_items(frm) {
	if (frm.doc.for_warehouse) return;

	// po_items içindeki herhangi bir satırın item_group'una göre tahmin et
	const items = frm.doc.po_items || [];
	let inferredWarehouse = null;
	for (const row of items) {
		if (row.item_group === "PVC") {
			inferredWarehouse = "PVC ÜRETİM DEPO - O";
			break;
		}
		if (row.item_group === "Camlar") {
			inferredWarehouse = "CAM ÜRETİM DEPO - O";
			break;
		}
	}
	if (inferredWarehouse) {
		frm.set_value("for_warehouse", inferredWarehouse);
		frm.refresh_field("for_warehouse");
	}
}

// Core dialog açıldığında tek modal üzerinde ANA DEPO'yu ekle
$(document).on("shown.bs.modal", function () {
	let attempts = 0;
	const maxAttempts = 10;
	const defaultWarehouse = "ANA DEPO - O";

	function trySet() {
		attempts += 1;
		const dialog = (typeof cur_dialog !== "undefined" && cur_dialog) ? cur_dialog : null;
		if (!dialog || !dialog.fields_dict) return scheduleRetry();
		const warehousesFld = dialog.fields_dict["warehouses"];
		const targetFld = dialog.fields_dict["target_warehouse"];
		if (!warehousesFld || !targetFld) return;

		const current = warehousesFld.get_value && warehousesFld.get_value();
		const hasDefault = Array.isArray(current) && current.some(r => r.warehouse === defaultWarehouse);
		if (hasDefault) return;

		if (warehousesFld.set_value) {
			warehousesFld.set_value([{ warehouse: defaultWarehouse }]);
			warehousesFld.refresh && warehousesFld.refresh();
			return;
		}

		if (dialog.set_value) {
			dialog.set_value("warehouses", [{ warehouse: defaultWarehouse }]);
		}
	}

	function scheduleRetry() {
		if (attempts >= maxAttempts) return;
		setTimeout(trySet, 120);
	}

	setTimeout(trySet, 50);
});


