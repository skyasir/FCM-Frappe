# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt
# 2.6 Billing Cycle -> Outstanding Report

import frappe


def execute(filters=None):
	columns = [
		{"label": "Invoice", "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 130},
		{"label": "Customer/Tenant", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
		{"label": "Billing Type", "fieldname": "fcm_billing_type", "fieldtype": "Data", "width": 120},
		{"label": "Contract", "fieldname": "fcm_lease_contract", "fieldtype": "Link", "options": "FCM Lease Contract", "width": 140},
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 100},
		{"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
		{"label": "Outstanding", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 120},
	]
	data = frappe.get_all("Sales Invoice",
		filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "customer", "fcm_billing_type", "fcm_lease_contract",
				"posting_date", "due_date", "grand_total", "outstanding_amount"])
	return columns, data
