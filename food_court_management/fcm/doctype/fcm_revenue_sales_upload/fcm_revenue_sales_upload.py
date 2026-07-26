# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FCMRevenueSalesUpload(Document):
	def validate(self):
		# Duplicate Invoice Check (5.2 Validation)
		dup = frappe.db.exists("FCM Revenue Sales Upload", {
			"lease_contract": self.lease_contract, "month": self.month, "year": self.year,
			"name": ["!=", self.name or "New FCM Revenue Sales Upload"],
		})
		self.is_duplicate = 1 if dup else 0
