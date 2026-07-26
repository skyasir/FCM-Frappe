# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, add_months, nowdate


class FCMLeaseContract(Document):
	def validate(self):
		self.validate_dates()
		self.validate_no_overlapping_contract()
		self.set_next_escalation_date()

	def validate_dates(self):
		if getdate(self.contract_start_date) >= getdate(self.contract_end_date):
			frappe.throw(_("Contract End Date must be after Contract Start Date"))

	def validate_no_overlapping_contract(self):
		"""Business Rule: No overlapping contracts. One active contract per unit."""
		overlapping = frappe.db.sql("""
			SELECT name FROM `tabFCM Lease Contract`
			WHERE shop_unit = %(shop_unit)s
				AND name != %(name)s
				AND status in ('Active', 'Draft')
				AND docstatus < 2
				AND (
					(contract_start_date <= %(end)s AND contract_end_date >= %(start)s)
				)
		""", {
			"shop_unit": self.shop_unit,
			"name": self.name or "New FCM Lease Contract",
			"start": self.contract_start_date,
			"end": self.contract_end_date,
		}, as_dict=True)
		if overlapping:
			frappe.throw(_("Overlapping contract {0} already exists for Shop/Unit {1}").format(
				overlapping[0].name, self.shop_unit))

	def set_next_escalation_date(self):
		if self.escalation_frequency == "Annual":
			self.next_escalation_date = add_months(self.contract_start_date, 12)
		elif self.escalation_frequency == "Biennial":
			self.next_escalation_date = add_months(self.contract_start_date, 24)
		elif self.escalation_frequency == "Every 3 Years":
			self.next_escalation_date = add_months(self.contract_start_date, 36)

	def on_submit(self):
		self.status = "Active"
		self.update_shop_unit_status("Occupied")

	def on_cancel(self):
		self.status = "Terminated"
		self.update_shop_unit_status("Vacant")

	def update_shop_unit_status(self, status):
		shop = frappe.get_doc("FCM Shop Unit", self.shop_unit)
		shop.status = status
		shop.current_tenant = self.tenant if status == "Occupied" else None
		shop.current_contract = self.name if status == "Occupied" else None
		shop.save(ignore_permissions=True)

	def before_save(self):
		# Business Rule: Expired contracts cannot generate invoices / be edited to Active
		if self.contract_end_date and getdate(self.contract_end_date) < getdate(nowdate()) and self.status == "Active":
			self.status = "Expired"


def apply_contract_escalations():
	"""Scheduled daily: apply rent escalation on contracts whose next_escalation_date has arrived."""
	contracts = frappe.get_all("FCM Lease Contract",
		filters={"status": "Active", "next_escalation_date": ["<=", nowdate()]},
		fields=["name", "rent_amount", "escalation_percent", "escalation_frequency"])
	for c in contracts:
		if not c.escalation_percent:
			continue
		doc = frappe.get_doc("FCM Lease Contract", c.name)
		new_rent = doc.rent_amount + (doc.rent_amount * doc.escalation_percent / 100)
		doc.db_set("rent_amount", new_rent)
		doc.set_next_escalation_date()
		doc.db_set("next_escalation_date", doc.next_escalation_date)
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": "FCM Lease Contract",
			"reference_name": c.name,
			"content": f"Rent escalated by {doc.escalation_percent}% to {new_rent} on {nowdate()}"
		}).insert(ignore_permissions=True)
	frappe.db.commit()
