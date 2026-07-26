# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt
# 5.4 Reports: Tenant Sales, Revenue Share, MG Comparison, Recovery Analysis

import frappe


def execute(filters=None):
	columns = [
		{"label": "Contract", "fieldname": "lease_contract", "fieldtype": "Link", "options": "FCM Lease Contract", "width": 150},
		{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 100},
		{"label": "Year", "fieldname": "year", "fieldtype": "Int", "width": 80},
		{"label": "Gross Sales", "fieldname": "gross_sales", "fieldtype": "Currency", "width": 120},
		{"label": "Revenue Share Amt", "fieldname": "revenue_share_amount", "fieldtype": "Currency", "width": 140},
		{"label": "MG", "fieldname": "minimum_guarantee", "fieldtype": "Currency", "width": 120},
		{"label": "Net Invoiced", "fieldname": "net_invoice_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Basis", "fieldname": "basis", "fieldtype": "Data", "width": 100},
	]
	data = frappe.get_all("FCM Revenue Sales Upload",
		fields=["lease_contract", "month", "year", "gross_sales", "revenue_share_amount",
				"minimum_guarantee", "net_invoice_amount"])
	for row in data:
		row["basis"] = "Revenue Share" if row["revenue_share_amount"] >= row["minimum_guarantee"] else "MG"
	return columns, data
