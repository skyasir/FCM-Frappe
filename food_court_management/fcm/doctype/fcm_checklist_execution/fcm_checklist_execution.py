# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class FCMChecklistExecution(Document):
	def validate(self):
		if self.status == "Completed" and not self.photo:
			frappe.msgprint(_("It is recommended to attach a completion photo for audit purposes."), alert=True)
		if self.vendor_bill_approved and not self.supervisor_verified:
			frappe.throw(_("Vendor bill cannot be approved before Supervisor Verification "
							"(Service Verification flow: Checklist > Photo Upload > Supervisor Verification > Vendor Bill Approval)"))
