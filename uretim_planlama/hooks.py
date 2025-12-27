# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

app_name = "uretim_planlama"
app_title = "Üretim Planlama"
app_publisher = "idris"
app_description = "ERPNext tabanlı üretim planlama uygulaması"
app_email = "idris.gemici61@gmail.com"
app_license = "MIT"

# Fixtures (isteğe bağlı özelleştirilebilir)
fixtures = [
	# Uretim Planlama modülüne ait özelleştirmeler
	{"dt": "Dashboard Chart", "filters": [["module", "=", "Uretim Planlama"]]},
	{"dt": "Number Card", "filters": [["module", "=", "Uretim Planlama"]]},
	{"dt": "Custom HTML Block"},
	{"dt": "Report", "filters": [["module", "=", "Uretim Planlama"]]},
	{"dt": "Workspace", "filters": [["module", "=", "Uretim Planlama"]]},
	{"dt": "Quality Label Items"},
	# Not: Diğer modüllerdeki (Stock, Manufacturing vb.) özelleştirmeler
	# genellikle veritabanında tutulur ve ERPNext güncellemelerinde korunur.
	# Bu modüllerdeki özelleştirmeleri fixture olarak eklemek için
	# export_customizations.sh script'ini kullanarak export edip
	# fixture klasörüne kopyalayabilirsiniz.
	# Custom Field ve Property Setter'lar (çok fazla olduğu için yorum satırında)
	# {"dt": "Custom Field", "filters": [["module", "=", "Uretim Planlama"]]},
	# {"dt": "Property Setter", "filters": [["module", "=", "Uretim Planlama"]]},
	# {"dt": "Client Script", "filters": [["module", "=", "Uretim Planlama"]]},
]

# Uygulama içi JS/CSS dosyaları
app_include_css = [
	"/assets/uretim_planlama/css/sales_order.css",
	"/assets/uretim_planlama/css/profile_buttons.css"
]

app_include_js = [
	"/assets/uretim_planlama/js/item_auto_fill.js",
]

# Not: profile_calculator.js ve jalousie_calculator.js artık DocType-specific olarak yükleniyor (doctype_js)

# Dashboard Chart Sources kaldırıldı


# Sayfa konfigürasyonu
page_js = {
    "uretim-paneli": "uretim_planlama/uretim_planlama/uretim_planlama/page/uretim_paneli/uretim_paneli.js",
    "uretim_planlama_takip": "uretim_planlama/uretim_planlama/uretim_planlama/page/uretim_planlama_takip/uretim_planlama_takip.js",
    "uretim_planlama_paneli": "uretim_planlama/uretim_planlama/uretim_planlama/page/uretim_planlama_paneli/uretim_planlama_paneli.js"
}

doctype_js = {
	"Production Plan": [
		"public/js/production_plan_list.js",
		"public/js/production_plan_chart.js",
		"public/js/production_plan_table.js",
		"public/js/opti_plan_table.js",
		"public/js/production_plan_po_items.js",
		"public/js/production_plan_auto_warehouse.js",
	],
	"Sales Order": [
		"public/js/sales_order/sales_order.js",
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_calculator.js",
		"public/js/jalousie_calculator.js"
	],
	"Accessory Delivery Package": "uretim_planlama/uretim_planlama/doctype/accessory_delivery_package/accessory_delivery_package.js",
	"Delivery Note": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_calculator.js",
		"public/js/jalousie_calculator.js"
	],
	"Purchase Order": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_calculator.js",
		"public/js/jalousie_calculator.js"
	],
	"Purchase Receipt": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_calculator.js",
		"public/js/jalousie_calculator.js"
	],
	"Stock Entry": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_calculator.js",
		"public/js/jalousie_calculator.js"
	],
	"Sales Invoice": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_calculator.js",
		"public/js/jalousie_calculator.js"
	],
	"Purchase Invoice": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_calculator.js",
		"public/js/jalousie_calculator.js"
	],
	"Material Request": [
		"public/js/get_items_merge.js",
		"public/js/uom_filter.js",
		"public/js/profile_calculator.js",
		"public/js/jalousie_calculator.js",
		"public/js/material_request_item_supplier.js"
	],
	"Profile Entry Item": "uretim_planlama/uretim_planlama/doctype/profile_entry_item/profile_entry_item.js",
	"Profile Exit Item": "uretim_planlama/uretim_planlama/doctype/profile_exit_item/profile_exit_item.js",
	"Contract": "uretim_planlama/public/js/contract_custom.js",
}

# DocType Event Hook'ları (yalnızca aktif kullanılanlar)
doc_events = {
	"Production Plan": {
		"on_submit": "uretim_planlama.custom_hooks.production_plan.on_submit.on_submit",
		"on_cancel": "uretim_planlama.custom_hooks.production_plan.on_cancel.on_cancel",
	},
	"Work Order": {
		"before_validate": "uretim_planlama.custom_hooks.work_order.before_validate.auto_wip_warehouse",
	},
	"Sales Order": {
		"on_submit": [
			"uretim_planlama.sales_order_hooks.raw_materials.create_reserved_raw_materials_on_submit",
			"uretim_planlama.sales_order_hooks.raw_materials.handle_child_sales_order_reserves",
			"uretim_planlama.sales_order_hooks.profile_reorder.check_profile_reorder_on_sales_order",
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
	"Work Order": {
		"before_validate": "uretim_planlama.custom_hooks.work_order.before_validate.auto_wip_warehouse",
		"on_cancel": "uretim_planlama.sales_order_hooks.raw_materials.restore_reservations_on_work_order_cancel",
		"on_update_after_submit": [
			"uretim_planlama.custom_hooks.work_order.on_update_after_submit.on_update_after_submit",
			"uretim_planlama.sales_order_hooks.raw_materials.remove_reservations_on_work_order_complete"
		]
	},
	"Delivery Note": {
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": "uretim_planlama.uretim_planlama.utils.validate",
		"on_submit": "uretim_planlama.delivery_note_events.on_submit",
		"on_cancel": "uretim_planlama.delivery_note_events.on_cancel"
	},
	"Purchase Order": {
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": [
			"uretim_planlama.uretim_planlama.utils.validate",
			"uretim_planlama.purchase_order_events.validate"
		],
		"on_submit": "uretim_planlama.purchase_order_events.on_submit",
		"on_cancel": "uretim_planlama.purchase_order_events.on_cancel",
		"on_update_after_submit": "uretim_planlama.purchase_order_events.on_update_after_submit"
	},
	"Purchase Receipt": {
		"validate": [
			"uretim_planlama.uretim_planlama.utils.validate",
			"uretim_planlama.purchase_receipt_events.validate"
		],
		"on_submit": "uretim_planlama.purchase_receipt_events.on_submit",
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save"
	},
	"Stock Entry": {
		"validate": [
			"uretim_planlama.uretim_planlama.utils.validate",
			"uretim_planlama.stock_entry_events.validate"
		],
		"on_submit": [
			"uretim_planlama.sales_order_hooks.raw_materials.release_reservations_on_stock_entry",
			"uretim_planlama.stock_entry_events.on_submit"
		],
		"on_cancel": "uretim_planlama.stock_entry_events.on_cancel",
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save"
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
	"Item Group": {
		"after_insert": "uretim_planlama.uretim_planlama.api.cache_utils.clear_profile_groups_cache",
		"on_update": "uretim_planlama.uretim_planlama.api.cache_utils.clear_profile_groups_cache",
		"on_trash": "uretim_planlama.uretim_planlama.api.cache_utils.clear_profile_groups_cache"
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

# DocType Class Override
# Production Plan'ın set_status() metodunu override edip
# status değişikliklerini workflow_state ile senkronize ediyoruz
# Contract'ın amendment davranışını önlemek için override ediyoruz
override_doctype_class = {
	"Production Plan": "uretim_planlama.manufacturing.doctype.production_plan.production_plan.CustomProductionPlan",
	"Contract": "uretim_planlama.crm.doctype.contract.contract.CustomContract"
}

scheduler_events = {
	"daily": [
		"uretim_planlama.uretim_planlama.api.reorder.profile_reorder_sweep",
	],
	"cron": {
		# Her 5 dakikada cache refresh (yoğun saatlerde)
		"*/5 8-18 * * 1-5": [
			"uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.refresh_cache_background"
		],
		# Her 15 dakikada cache refresh (normal saatlerde)
		"*/15 0-7,19-23 * * *": [
			"uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.refresh_cache_background"
		],
		# Hafta sonları saatlik
		"0 * * * 6,0": [
			"uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.refresh_cache_background"
		]
	}
}
