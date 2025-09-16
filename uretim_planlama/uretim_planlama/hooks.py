# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

# DocType Events
doc_events = {
	"Purchase Receipt": {
		"on_submit": "uretim_planlama.purchase_receipt_events.on_submit"
	},
	"Delivery Note": {
		"before_save": "uretim_planlama.uretim_planlama.utils.before_save",
		"validate": "uretim_planlama.uretim_planlama.utils.validate",
		"on_submit": "uretim_planlama.delivery_note_events.on_submit",
		"on_cancel": "uretim_planlama.delivery_note_events.on_cancel"
	},
	"Boy": {
		"before_save": "uretim_planlama.uretim_planlama.doctype.boy.boy.Boy.before_save",
		"validate": "uretim_planlama.uretim_planlama.doctype.boy.boy.Boy.validate"
	}
}

# App Hooks
app_name = "uretim_planlama"
app_title = "Üretim Planlama"
app_publisher = "idris"
app_description = "Üretim Planlama Modülü"
app_email = "idris@example.com"
app_license = "MIT"

# Website Hooks
website_route_rules = [
	{"from_route": "/uretim-paneli", "to_route": "uretim_planlama_paneli"},
]

# Scheduled Tasks
scheduler_events = {
	"daily": [
		"uretim_planlama.uretim_planlama.api.reorder.profile_reorder_sweep"
	]
}




