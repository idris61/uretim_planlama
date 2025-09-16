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
app_include_css = ["/assets/uretim_planlama/css/sales_order.css"]

# Sayfa konfigürasyonu
page_js = {
    "uretim-paneli": "uretim_planlama/uretim_planlama/uretim_planlama/page/uretim_paneli/uretim_paneli.js",
    "uretim_planlama_takip": "uretim_planlama/uretim_planlama/uretim_planlama/page/uretim_planlama_takip/uretim_planlama_takip.js",
    "uretim_planlama_paneli": "uretim_planlama/uretim_planlama/uretim_planlama/page/uretim_planlama_paneli/uretim_planlama_paneli.js"
}

doctype_js = {
	"Production Plan": [
		"public/js/production_plan_chart.js",
		"public/js/production_plan_table.js",
		"public/js/opti_plan_table.js",
		"public/js/production_plan_po_items.js",
	],
	"Sales Order": [
		"public/js/sales_order/sales_order.js",
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_quantity_calculator.js"
	],
	"Accessory Delivery Package": "uretim_planlama/uretim_planlama/doctype/accessory_delivery_package/accessory_delivery_package.js",
	"Delivery Note": [
		"public/js/delivery_note_assembly_accessory_html.js",
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_quantity_calculator.js"
	],
	"Purchase Order": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_quantity_calculator.js"
	],
	"Purchase Receipt": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_quantity_calculator.js"
	],
	"Stock Entry": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_quantity_calculator.js"
	],
	"Sales Invoice": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_quantity_calculator.js"
	],
	"Purchase Invoice": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_quantity_calculator.js"
	],
	"Material Request": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_quantity_calculator.js"
	],
}

# DocType Event Hook'ları (yalnızca aktif kullanılanlar)
doc_events = {
	"Production Plan": {
		"on_submit": "uretim_planlama.custom_hooks.production_plan.on_submit.on_submit",
		"on_cancel": "uretim_planlama.custom_hooks.production_plan.on_cancel.on_cancel",
	},
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
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": "uretim_planlama.uretim_planlama.utils.validate"
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
	"Delivery Note": {
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": "uretim_planlama.uretim_planlama.utils.validate",
		"on_submit": "uretim_planlama.delivery_note_events.on_submit",
		"on_cancel": "uretim_planlama.delivery_note_events.on_cancel"
	},
	"Purchase Order": {
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": "uretim_planlama.uretim_planlama.utils.validate"
	},
	# Purchase Receipt: tüm eventleri TEK blokta topla (çift tanımı engelle)
	"Purchase Receipt": {
		"on_submit": "uretim_planlama.purchase_receipt_events.on_submit",
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": "uretim_planlama.uretim_planlama.utils.validate"
	},
	"Stock Entry": {
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": "uretim_planlama.uretim_planlama.utils.validate"
	},
	"Sales Invoice": {
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": "uretim_planlama.uretim_planlama.utils.validate"
	},
	"Purchase Invoice": {
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": "uretim_planlama.uretim_planlama.utils.validate"
	},
	"Material Request": {
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": "uretim_planlama.uretim_planlama.utils.validate"
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


scheduler_events = {
	"daily": [
		"uretim_planlama.uretim_planlama.api.reorder.profile_reorder_sweep",
	]
}

