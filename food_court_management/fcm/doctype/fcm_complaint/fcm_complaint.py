# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, add_to_date, get_datetime


class FCMComplaint(Document):
	def validate(self):
		if not self.raised_on:
			self.raised_on = now_datetime()
		self.set_sla_due_dates()
		self.check_sla_breach()

	def set_sla_due_dates(self):
		if not self.complaint_category:
			return
		cat = frappe.get_doc("FCM Complaint Category", self.complaint_category)
		if cat.default_sla_response_hours and not self.sla_response_due:
			self.sla_response_due = add_to_date(self.raised_on, hours=cat.default_sla_response_hours)
		if cat.default_sla_resolution_hours and not self.sla_resolution_due:
			self.sla_resolution_due = add_to_date(self.raised_on, hours=cat.default_sla_resolution_hours)

	def check_sla_breach(self):
		self.is_sla_breached = 0
		if self.sla_resolution_due and self.status not in ("Closed", "Completed"):
			if get_datetime() > get_datetime(self.sla_resolution_due):
				self.is_sla_breached = 1
		if self.resolved_on and self.sla_resolution_due:
			if get_datetime(self.resolved_on) > get_datetime(self.sla_resolution_due):
				self.is_sla_breached = 1

	def on_update(self):
		# 8.3 Workflow: Complaint > Assign Vendor > Start Work > Complete > Inspection > Customer Feedback > Closure
		if self.status == "Completed" and not self.resolved_on:
			self.db_set("resolved_on", now_datetime())
