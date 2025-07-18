# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

app_name = "uretim_planlama"
app_title = "Üretim Planlama"
app_publisher = "idris"
app_description = "ERPNext tabanlı üretim planlama uygulaması"
app_email = "idris@example.com"
app_license = "MIT"

# Fixtures (isteğe bağlı özelleştirilebilir)
fixtures = [
	{"dt": "Custom Field", "filters": [["module", "=", "Uretim Planlama"]]},
	{"dt": "Property Setter", "filters": [["module", "=", "Uretim Planlama"]]},
	# {"dt": "Workflow"},
	# {"dt": "Workflow State"},
	# {"dt": "Item", "filters": [["custom_poz_id", "=", ""], ["custom_serial", "=", ""]]},
	# {"dt": "Item Group"},
	# {"dt": "Workstation"},
	# {"dt": "Operation"},
	# {"dt": "UOM"},
	# {"dt": "Cam"},
	# {"dt": "Profile Type"},
	# {"dt": "Cam Recipe"},
]

# Uygulama içi JS/CSS dosyaları
app_include_js = ["/assets/uretim_planlama/js/purchase_receipt_profile_fields.js"]

app_include_css = ["/assets/uretim_planlama/css/sales_order.css"]

doctype_js = {
	"Production Plan": [
		"public/js/production_plan_chart.js",
		"public/js/production_plan_table.js",
		"public/js/opti_plan_table.js",
		"public/js/production_plan_po_items.js",
	],
	"Sales Order": "public/js/sales_order/sales_order.js",
	"Accessory Delivery Package": "uretim_planlama/uretim_planlama/doctype/accessory_delivery_package/accessory_delivery_package.js",
	"Delivery Note": "public/js/delivery_note_assembly_accessory_html.js",
}

# DocType Event Hook'ları (yalnızca aktif kullanılanlar)
doc_events = {
	"Sales Order": {
		"on_submit": [
			"uretim_planlama.sales_order_hooks.raw_materials.create_reserved_raw_materials_on_submit",
			"uretim_planlama.sales_order_hooks.raw_materials.handle_child_sales_order_reserves",
		],
		"on_cancel": [
			"uretim_planlama.sales_order_hooks.raw_materials.delete_reserved_raw_materials_on_cancel",
			"uretim_planlama.sales_order_hooks.raw_materials.delete_long_term_reserve_usage_on_cancel",
		],
		"before_submit": "uretim_planlama.sales_order_hooks.raw_materials.check_raw_material_stock_on_submit",
	},
	
	"Profile Stock Ledger": {
		"after_import": "uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger.after_import"
	},
	# "Job Card": {
	# 	"on_update": "uretim_planlama.sales_order_hooks.raw_materials.release_reservations_on_job_card_complete"
	# },
	"Stock Entry": {
		"on_submit": "uretim_planlama.sales_order_hooks.raw_materials.release_reservations_on_stock_entry"
	},
	"Work Order": {
		"on_cancel": "uretim_planlama.sales_order_hooks.raw_materials.restore_reservations_on_work_order_cancel"
	},
}

# after_import işlemi
after_import = "uretim_planlama.uretim_planlama.doctype.profile_stock_ledger.profile_stock_ledger.after_import_profile_stock_ledger"

# Modül konfigürasyonu
modules = {
	"Uretim Planlama": {
		"color": "grey",
		"icon": "octicon octicon-file-directory",
		"label": "Üretim Planlama",
	}
}
