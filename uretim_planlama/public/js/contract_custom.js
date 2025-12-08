/**
 * Custom Contract behavior to prevent amendment and allow direct editing
 * of cancelled contracts.
 * 
 * This prevents the creation of new documents (like CON-2025-00001-1) when
 * editing cancelled contracts (like CON-2025-00001).
 */

// Override frappe.model.copy_doc globally to prevent Contract amendments
if (typeof frappe !== 'undefined' && frappe.model && frappe.model.copy_doc) {
	const original_copy_doc = frappe.model.copy_doc;
	frappe.model.copy_doc = function(doc, from_amend, parent_doc, parentfield) {
		// If this is an amendment for Contract, prevent it
		if (from_amend && doc.doctype === "Contract") {
			// Return a copy without amended_from
			const newdoc = original_copy_doc.call(this, doc, false, parent_doc, parentfield);
			// Ensure amended_from is not set
			if (newdoc._amended_from) {
				delete newdoc._amended_from;
			}
			if (newdoc.amended_from) {
				newdoc.amended_from = null;
			}
			return newdoc;
		}
		// For other cases, use original function
		return original_copy_doc.call(this, doc, from_amend, parent_doc, parentfield);
	};
}

frappe.ui.form.on("Contract", {
	onload: function(frm) {
		// Override amend_doc method completely to prevent new document creation
		if (frm.amend_doc) {
			const original_amend_doc = frm.amend_doc.bind(frm);
			frm.amend_doc = function() {
				// For Contract, instead of creating a new document, just enable editing
				if (this.doc.docstatus === 2) {
					// Reset docstatus to allow editing
					this.doc.docstatus = 0;
					// Clear amended_from to prevent amendment behavior
					if (this.doc.amended_from) {
						this.set_value("amended_from", "");
					}
					// Switch to main view to allow editing
					this.page.set_view("main");
					this.dirty();
					frappe.show_alert({
						message: __("Document is now editable. You can make changes and save."),
						indicator: "blue"
					});
					return;
				}
				// For other cases, use original method
				return original_amend_doc.call(this);
			};
		}
		
		// Override copy_doc to prevent amended_from from being set
		if (frm.copy_doc) {
			const original_copy_doc = frm.copy_doc.bind(frm);
			frm.copy_doc = function(onload, from_amend) {
				// For Contract, never allow amendment
				if (from_amend && this.doc.doctype === "Contract") {
					// Don't create amendment, just return error or enable editing
					frappe.msgprint({
						message: __("Amendment is disabled for Contract. Please edit the document directly."),
						indicator: "orange",
						title: __("Amendment Disabled")
					});
					return;
				}
				// For other cases, use original method
				return original_copy_doc.call(this, onload, from_amend);
			};
		}
	},
	
	refresh: function(frm) {
		// Override can_amend to always return false for Contract
		// This prevents the "Amend" button from showing
		if (frm.toolbar) {
			frm.toolbar.can_amend = function() {
				// Always return false for Contract to prevent amendment
				if (this.frm.doc.doctype === "Contract") {
					return false;
				}
				// For other doctypes, use original logic
				return this.frm.doc.docstatus === 2 && this.frm.perm[0].amend && !this.read_only;
			};
		}
		
		// If document is cancelled, show Edit button instead of Amend
		if (frm.doc.docstatus === 2 && frm.perm[0].write && !frm.is_read_only()) {
			// Override get_action_status to return "Edit" for cancelled documents
			if (frm.toolbar && frm.toolbar.get_action_status) {
				const original_get_action_status = frm.toolbar.get_action_status.bind(frm.toolbar);
				frm.toolbar.get_action_status = function() {
					// If cancelled Contract, return "Edit" instead of "Amend"
					if (this.frm.doc.doctype === "Contract" && 
						this.frm.doc.docstatus === 2 && 
						this.frm.perm[0].write && 
						!this.read_only) {
						return "Edit";
					}
					// Otherwise use original logic
					return original_get_action_status.call(this);
				};
			}
			
			// Override set_page_actions to handle Edit for cancelled documents
			if (frm.toolbar && frm.toolbar.set_page_actions) {
				const original_set_page_actions = frm.toolbar.set_page_actions.bind(frm.toolbar);
				frm.toolbar.set_page_actions = function(status) {
					// Handle Edit button for cancelled Contract documents
					if (status === "Edit" && 
						this.frm.doc.doctype === "Contract" && 
						this.frm.doc.docstatus === 2) {
						var me = this;
						this.page.set_primary_action(
							__("Edit"),
							function() {
								// Reset docstatus to allow editing
								me.frm.doc.docstatus = 0;
								// Clear amended_from if it exists to prevent amendment behavior
								if (me.frm.doc.amended_from) {
									me.frm.set_value("amended_from", "");
								}
								// Switch to main view to allow editing
								me.frm.page.set_view("main");
								me.frm.dirty();
							},
							"edit"
						);
						this.current_status = status;
					} else {
						// Use original logic for other statuses
						return original_set_page_actions.call(this, status);
					}
				};
			}
		}
	},
	
	before_save: function(frm) {
		// Ensure amended_from is cleared when saving
		// This prevents the creation of a new document with amended_from set
		if (frm.doc.amended_from) {
			// Always clear amended_from for Contract to prevent amendment
			frm.set_value("amended_from", "");
		}
	}
});

