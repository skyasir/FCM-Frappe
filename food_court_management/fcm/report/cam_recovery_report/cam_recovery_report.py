# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt
# 3.4 CAM Reports: Monthly CAM Cost, Recovery %, Vacant Area Cost, Expense Category Analysis

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Food Court", "fieldname": "food_court", "fieldtype": "Link", "options": "FCM Food Court", "width": 150},
		{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 100},
		{"label": "Year", "fieldname": "year", "fieldtype": "Int", "width": 80},
		{"label": "Cost Category", "fieldname": "cost_category", "fieldtype": "Link", "options": "FCM CAM Cost Category", "width": 150},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
	]
	conditions, values = [], {}
	if filters.get("food_court"):
		conditions.append("food_court = %(food_court)s")
		values["food_court"] = filters["food_court"]
	where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
	data = frappe.db.sql(f"""
		SELECT food_court, month, year, cost_category, amount, status
		FROM `tabFCM CAM Cost Entry`
		{where}
		ORDER BY year DESC, month DESC
	""", values, as_dict=True)
	return columns, data
