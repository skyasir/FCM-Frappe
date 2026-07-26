# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class FCMMeterReading(Document):
	def validate(self):
		self.fetch_previous_reading()
		self.validate_consumption()
		self.calculate_amount()

	def fetch_previous_reading(self):
		prev = frappe.db.sql("""
			SELECT current_reading FROM `tabFCM Meter Reading`
			WHERE meter = %s AND name != %s AND reading_date < %s
			ORDER BY reading_date DESC LIMIT 1
		""", (self.meter, self.name or "New FCM Meter Reading", self.reading_date))
		self.previous_reading = flt(prev[0][0]) if prev else 0

	def validate_consumption(self):
		# Consumption Validation (Section 4): current must not be less than previous
		if flt(self.current_reading) < flt(self.previous_reading):
			frappe.throw(_("Current Reading ({0}) cannot be less than Previous Reading ({1})").format(
				self.current_reading, self.previous_reading))
		self.consumption = flt(self.current_reading) - flt(self.previous_reading)

	def calculate_amount(self):
		if self.rate_per_unit:
			self.amount = flt(self.consumption) * flt(self.rate_per_unit)
