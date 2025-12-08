# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
Custom Contract class to prevent amendment behavior.
Allows direct editing of cancelled contracts without creating new documents.

This prevents the creation of new documents (like CON-2025-00001-1) when
editing cancelled contracts (like CON-2025-00001).
"""

import frappe
from erpnext.crm.doctype.contract.contract import Contract as ERPNextContract


class CustomContract(ERPNextContract):
	"""
	Override Contract class to allow editing cancelled documents directly.
	Prevents the creation of new documents with amended_from field.
	"""
	
	def before_insert(self):
		"""
		Override before_insert to prevent amendment.
		Clear amended_from before insert to prevent new document creation.
		"""
		# Always clear amended_from for Contract to prevent amendment
		if self.amended_from:
			self.amended_from = None
		
		# Call parent before_insert if it exists
		if hasattr(super(), 'before_insert'):
			super().before_insert()
	
	def before_naming(self):
		"""
		Override before_naming to prevent amendment naming.
		Clear amended_from before naming to prevent new document creation.
		"""
		# Always clear amended_from for Contract to prevent amendment naming
		if self.amended_from:
			self.amended_from = None
		
		# Call parent before_naming if it exists
		if hasattr(super(), 'before_naming'):
			super().before_naming()
	
	def insert(self, *args, **kwargs):
		"""
		Override insert to prevent amendment.
		Clear amended_from before insert to prevent new document creation.
		"""
		# Clear amended_from before insert to prevent amendment
		if self.amended_from:
			self.amended_from = None
		
		# Call parent insert
		return super().insert(*args, **kwargs)
	
	def validate(self):
		"""
		Override validate to allow editing cancelled documents.
		Clear amended_from if document is being edited directly.
		"""
		# If this is an existing document (has name) and is being edited
		if self.name and not self.get("__islocal"):
			# Get original docstatus from database
			original_docstatus = frappe.db.get_value(self.doctype, self.name, "docstatus")
			
			# If original was cancelled and we're trying to save it (docstatus changed to 0)
			if original_docstatus == 2 and self.docstatus == 0:
				# Clear amended_from to prevent amendment behavior
				# This ensures we're editing the same document, not creating a new one
				if self.amended_from:
					self.amended_from = None
		
		# Call parent validate
		super().validate()
	
	def validate_amended_from(self):
		"""
		Override to prevent amendment validation.
		This allows cancelled documents to be edited directly without creating amendments.
		"""
		# Skip amendment validation - we want to allow direct editing
		# This prevents the error when trying to edit a cancelled document
		pass
	
	def before_save(self):
		"""
		Ensure amended_from is cleared if document is being edited directly.
		This prevents the creation of new documents when editing cancelled ones.
		"""
		# Always clear amended_from for Contract to prevent amendment
		if self.amended_from:
			# If this is an existing document being edited
			if self.name and not self.get("__islocal"):
				# Get original docstatus from database
				original_docstatus = frappe.db.get_value(self.doctype, self.name, "docstatus")
				
				# If original was cancelled and we're saving it (docstatus is 0 now)
				if original_docstatus == 2:
					# Clear amended_from to prevent amendment behavior
					self.amended_from = None
			else:
				# For new documents, also clear amended_from to prevent amendment
				self.amended_from = None
		
		# Call parent before_save if it exists
		if hasattr(super(), 'before_save'):
			super().before_save()

