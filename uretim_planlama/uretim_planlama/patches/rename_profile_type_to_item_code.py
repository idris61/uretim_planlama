import frappe
from frappe.model.utils.rename_field import rename_field

def execute():
	"""
	Rename profile_type to item_code in Profile Stock Ledger, Profile Reorder Rule
	and rename profile_code to item_code in Scrap Profile Entry
	"""
	
	try:
		# Profile Stock Ledger: profile_type -> item_code
		if frappe.db.exists("DocType", "Profile Stock Ledger"):
			if frappe.db.has_column("Profile Stock Ledger", "profile_type"):
				frappe.logger().info("Renaming profile_type to item_code in Profile Stock Ledger")
				rename_field("Profile Stock Ledger", "profile_type", "item_code")
				frappe.logger().info("✅ Profile Stock Ledger: profile_type -> item_code completed")
		
		# Profile Reorder Rule: profile_type -> item_code
		if frappe.db.exists("DocType", "Profile Reorder Rule"):
			if frappe.db.has_column("Profile Reorder Rule", "profile_type"):
				frappe.logger().info("Renaming profile_type to item_code in Profile Reorder Rule")
				rename_field("Profile Reorder Rule", "profile_type", "item_code")
				frappe.logger().info("✅ Profile Reorder Rule: profile_type -> item_code completed")
		
		# Scrap Profile Entry: profile_code -> item_code
		if frappe.db.exists("DocType", "Scrap Profile Entry"):
			if frappe.db.has_column("Scrap Profile Entry", "profile_code"):
				frappe.logger().info("Renaming profile_code to item_code in Scrap Profile Entry")
				rename_field("Scrap Profile Entry", "profile_code", "item_code")
				frappe.logger().info("✅ Scrap Profile Entry: profile_code -> item_code completed")
		
		frappe.db.commit()
		frappe.logger().info("🎉 All field renames completed successfully")
		
	except Exception as e:
		frappe.logger().error(f"Error during field rename: {str(e)}")
		frappe.db.rollback()
		raise


