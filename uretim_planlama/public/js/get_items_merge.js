// Merge duplicate item rows after "Get Items From" actions
// Groups by safe key fields and sums quantity fields
// Docstrings and function/variable names are in English per project rules

window.uretim_planlama = window.uretim_planlama || {};

(function () {
	function buildGroupKey(row, keyFields) {
		return keyFields
			.map((field) => (row[field] == null ? "" : String(row[field])))
			.join("||");
	}

	function cloneRowForNewChild(sourceRow) {
		const target = {};
		Object.keys(sourceRow || {}).forEach((key) => {
			if (
				key !== "name" &&
				key !== "doctype" &&
				key !== "owner" &&
				key !== "parent" &&
				key !== "parenttype" &&
				key !== "parentfield" &&
				key !== "idx"
			) {
				target[key] = sourceRow[key];
			}
		});
		return target;
	}

	function sumNumbers(a, b) {
		const x = (typeof a === "number" ? a : (window.flt ? flt(a || 0) : +(a || 0)));
		const y = (typeof b === "number" ? b : (window.flt ? flt(b || 0) : +(b || 0)));
		return (x || 0) + (y || 0);
	}

	/**
	 * Merge duplicate children for a given child table
	 * @param {frappe.ui.form.Form} frm
	 * @param {Object} options
	 * @param {string} options.childFieldname - Child table fieldname (e.g., "items")
	 * @param {Array<string>} options.keyFields - Fields to define grouping key
	 * @param {string} options.qtyField - Quantity field to be summed (e.g., "qty")
	 * @param {string} [options.stockQtyField] - Stock quantity field to be recomputed (e.g., "stock_qty" / "transfer_qty")
	 * @param {string} [options.conversionFactorField] - Conversion factor field (e.g., "conversion_factor")
	 */
	function mergeChildDuplicates(frm, options) {
		if (!frm || !frm.doc) return;
		const childFieldname = options.childFieldname;
		const keyFields = options.keyFields || [];
		const qtyField = options.qtyField;
		const stockQtyField = options.stockQtyField;
		const conversionFactorField = options.conversionFactorField;

		const rows = (frm.doc[childFieldname] || []).filter(Boolean);
		if (!rows.length) return;

		// Avoid re-entrancy
		if (frm.__uretim_planlama_merging__) return;
		frm.__uretim_planlama_merging__ = true;

		try {
			const groupKeyToAgg = {};
			const orderOfKeys = [];

			rows.forEach((row) => {
				const key = buildGroupKey(row, keyFields);
				if (!groupKeyToAgg[key]) {
					groupKeyToAgg[key] = {
						template: row,
						summedQty: row[qtyField] || 0,
					};
					orderOfKeys.push(key);
				} else {
					groupKeyToAgg[key].summedQty = sumNumbers(groupKeyToAgg[key].summedQty, row[qtyField] || 0);
				}
			});

			if (orderOfKeys.length === rows.length) {
				// No duplicates, nothing to do
				return;
			}

			// Clear and rebuild
			if (typeof frm.clear_table === "function") {
				frm.clear_table(childFieldname);
			} else {
				frm.set_value(childFieldname, []);
			}

			orderOfKeys.forEach((key) => {
				const agg = groupKeyToAgg[key];
				const newChild = frm.add_child(childFieldname);
				const cloned = cloneRowForNewChild(agg.template);
				cloned[qtyField] = agg.summedQty;

				if (stockQtyField) {
					const cf = cloned[conversionFactorField] || agg.template[conversionFactorField] || 1;
					cloned[stockQtyField] = (window.flt ? flt(cloned[qtyField]) : +cloned[qtyField] || 0) * (window.flt ? flt(cf) : +cf || 1);
				}

				Object.keys(cloned).forEach((field) => {
					newChild[field] = cloned[field];
				});
			});

			frm.refresh_field(childFieldname);
		} finally {
			frm.__uretim_planlama_merging__ = false;
		}
	}

	function mergeForPurchaseOrder(frm) {
		if (!frm || frm.doc.docstatus !== 0) return;
		mergeChildDuplicates(frm, {
			childFieldname: "items",
			keyFields: ["item_code", "uom", "custom_is_profile", "custom_profile_length_m", "custom_profile_length_qty", "custom_is_jalousie", "custom_jalousie_width", "custom_jalousie_height"],
			qtyField: "qty",
			stockQtyField: "stock_qty",
			conversionFactorField: "conversion_factor",
		});
	}

	function mergeForStockEntry(frm) {
		if (!frm || frm.doc.docstatus !== 0) return;
		mergeChildDuplicates(frm, {
			childFieldname: "items",
			keyFields: [
				"item_code",
				"uom",
				"s_warehouse",
				"t_warehouse",
				"batch_no",
				"serial_and_batch_bundle",
				"custom_is_profile",
				"custom_profile_length_m",
				"custom_profile_length_qty",
				"custom_is_jalousie",
				"custom_jalousie_width",
				"custom_jalousie_height",
			],
			qtyField: "qty",
			stockQtyField: "transfer_qty",
			conversionFactorField: "conversion_factor",
		});
	}

	function mergeForSalesOrder(frm) {
		if (!frm || frm.doc.docstatus !== 0) return;
		mergeChildDuplicates(frm, {
			childFieldname: "items",
			keyFields: ["item_code", "uom", "warehouse", "custom_is_profile", "custom_profile_length_m", "custom_profile_length_qty", "custom_is_jalousie", "custom_jalousie_width", "custom_jalousie_height"],
			qtyField: "qty",
			stockQtyField: "stock_qty",
			conversionFactorField: "conversion_factor",
		});
	}

	function mergeForDeliveryNote(frm) {
		if (!frm || frm.doc.docstatus !== 0) return;
		mergeChildDuplicates(frm, {
			childFieldname: "items",
			keyFields: ["item_code", "uom", "warehouse", "batch_no", "serial_and_batch_bundle", "custom_is_profile", "custom_profile_length_m", "custom_profile_length_qty", "custom_is_jalousie", "custom_jalousie_width", "custom_jalousie_height"],
			qtyField: "qty",
			stockQtyField: "stock_qty",
			conversionFactorField: "conversion_factor",
		});
	}

	function mergeForPurchaseReceipt(frm) {
		if (!frm || frm.doc.docstatus !== 0) return;
		mergeChildDuplicates(frm, {
			childFieldname: "items",
			keyFields: ["item_code", "uom", "warehouse", "batch_no", "serial_and_batch_bundle", "custom_is_profile", "custom_profile_length_m", "custom_profile_length_qty", "custom_is_jalousie", "custom_jalousie_width", "custom_jalousie_height"],
			qtyField: "qty",
			stockQtyField: "stock_qty",
			conversionFactorField: "conversion_factor",
		});
	}

	function mergeForPurchaseInvoice(frm) {
		if (!frm || frm.doc.docstatus !== 0) return;
		mergeChildDuplicates(frm, {
			childFieldname: "items",
			keyFields: ["item_code", "uom", "warehouse", "batch_no", "serial_and_batch_bundle", "custom_is_profile", "custom_profile_length_m", "custom_profile_length_qty", "custom_is_jalousie", "custom_jalousie_width", "custom_jalousie_height"],
			qtyField: "qty",
			stockQtyField: "stock_qty",
			conversionFactorField: "conversion_factor",
		});
	}

	function mergeForSalesInvoice(frm) {
		if (!frm || frm.doc.docstatus !== 0) return;
		mergeChildDuplicates(frm, {
			childFieldname: "items",
			keyFields: ["item_code", "uom", "warehouse", "batch_no", "serial_and_batch_bundle", "custom_is_profile", "custom_profile_length_m", "custom_profile_length_qty", "custom_is_jalousie", "custom_jalousie_width", "custom_jalousie_height"],
			qtyField: "qty",
			stockQtyField: "stock_qty",
			conversionFactorField: "conversion_factor",
		});
	}

	function mergeForMaterialRequest(frm) {
		if (!frm || frm.doc.docstatus !== 0) return;
		mergeChildDuplicates(frm, {
			childFieldname: "items",
			keyFields: ["item_code", "uom", "warehouse", "custom_is_profile", "custom_profile_length_m", "custom_profile_length_qty", "custom_is_jalousie", "custom_jalousie_width", "custom_jalousie_height"],
			qtyField: "qty",
			// Material Request may not maintain stock_qty consistently; sum qty only
		});
	}

	// Expose helpers
	window.uretim_planlama.get_items_merge = {
		mergeChildDuplicates,
		mergeForPurchaseOrder,
		mergeForStockEntry,
		mergeForSalesOrder,
		mergeForDeliveryNote,
		mergeForPurchaseReceipt,
		mergeForPurchaseInvoice,
		mergeForSalesInvoice,
		mergeForMaterialRequest,
	};

	// Bind to doctype refresh events
	frappe.ui.form.on("Purchase Order", {
		refresh: function (frm) {
			mergeForPurchaseOrder(frm);
		},
		validate: function (frm) {
			mergeForPurchaseOrder(frm);
		},
		items_on_form_rendered: function (frm) {
			mergeForPurchaseOrder(frm);
		},
	});

	frappe.ui.form.on("Stock Entry", {
		refresh: function (frm) {
			mergeForStockEntry(frm);
		},
		validate: function (frm) {
			mergeForStockEntry(frm);
		},
		items_on_form_rendered: function (frm) {
			mergeForStockEntry(frm);
		},
	});

	frappe.ui.form.on("Sales Order", {
		refresh: function (frm) {
			mergeForSalesOrder(frm);
		},
		validate: function (frm) {
			mergeForSalesOrder(frm);
		},
		items_on_form_rendered: function (frm) {
			mergeForSalesOrder(frm);
		},
	});

	frappe.ui.form.on("Delivery Note", {
		refresh: function (frm) {
			mergeForDeliveryNote(frm);
		},
		validate: function (frm) {
			mergeForDeliveryNote(frm);
		},
		items_on_form_rendered: function (frm) {
			mergeForDeliveryNote(frm);
		},
	});

	frappe.ui.form.on("Purchase Receipt", {
		refresh: function (frm) {
			mergeForPurchaseReceipt(frm);
		},
		validate: function (frm) {
			mergeForPurchaseReceipt(frm);
		},
		items_on_form_rendered: function (frm) {
			mergeForPurchaseReceipt(frm);
		},
	});

	frappe.ui.form.on("Purchase Invoice", {
		refresh: function (frm) {
			mergeForPurchaseInvoice(frm);
		},
		validate: function (frm) {
			mergeForPurchaseInvoice(frm);
		},
		items_on_form_rendered: function (frm) {
			mergeForPurchaseInvoice(frm);
		},
	});

	frappe.ui.form.on("Sales Invoice", {
		refresh: function (frm) {
			mergeForSalesInvoice(frm);
		},
		validate: function (frm) {
			mergeForSalesInvoice(frm);
		},
		items_on_form_rendered: function (frm) {
			mergeForSalesInvoice(frm);
		},
	});

	frappe.ui.form.on("Material Request", {
		refresh: function (frm) {
			mergeForMaterialRequest(frm);
		},
		validate: function (frm) {
			mergeForMaterialRequest(frm);
		},
		items_on_form_rendered: function (frm) {
			mergeForMaterialRequest(frm);
		},
	});
})();


