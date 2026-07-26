# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt
# 11.5 CRM Reports: Occupancy %

import frappe


def execute(filters=None):
	columns = [
		{"label": "Food Court", "fieldname": "food_court", "fieldtype": "Link", "options": "FCM Food Court", "width": 180},
		{"label": "Total Units", "fieldname": "total_units", "fieldtype": "Int", "width": 100},
		{"label": "Occupied", "fieldname": "occupied", "fieldtype": "Int", "width": 100},
		{"label": "Vacant", "fieldname": "vacant", "fieldtype": "Int", "width": 100},
		{"label": "Reserved", "fieldname": "reserved", "fieldtype": "Int", "width": 100},
		{"label": "Occupancy %", "fieldname": "occupancy_pct", "fieldtype": "Percent", "width": 120},
	]
	data = frappe.db.sql("""
		SELECT food_court,
			COUNT(*) as total_units,
			SUM(CASE WHEN status='Occupied' THEN 1 ELSE 0 END) as occupied,
			SUM(CASE WHEN status='Vacant' THEN 1 ELSE 0 END) as vacant,
			SUM(CASE WHEN status='Reserved' THEN 1 ELSE 0 END) as reserved
		FROM `tabFCM Shop Unit`
		GROUP BY food_court
	""", as_dict=True)
	for row in data:
		row["occupancy_pct"] = round((row["occupied"] / row["total_units"]) * 100, 2) if row["total_units"] else 0
	return columns, data
