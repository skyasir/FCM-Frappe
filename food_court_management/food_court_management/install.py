# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt

import frappe


def after_install():
	create_default_naming_series()
	create_default_records()
	frappe.db.commit()


def create_default_naming_series():
	"""Naming series are created automatically from each DocType's
	'naming_series' field options on first migrate; nothing extra required."""
	pass


def create_default_records():
	# Seed common CAM cost categories (3.1 CAM Cost Categories)
	categories = [
		"Cleaning", "Housekeeping", "Security", "Gardening", "Generator",
		"Electricity", "Water", "Fire Fighting", "Pest Control", "Repairs",
		"Civil Maintenance", "Lift Maintenance", "AMC", "Audit Charges",
		"Insurance", "Administration", "Miscellaneous",
	]
	for c in categories:
		if not frappe.db.exists("FCM CAM Cost Category", c):
			frappe.get_doc({
				"doctype": "FCM CAM Cost Category",
				"category_name": c,
				"default_allocation_method": "Square Foot Basis",
			}).insert(ignore_permissions=True)

	# Seed facility services (7.1 Facility Services)
	services = ["Housekeeping", "Security", "Gardening", "Electrical", "Civil",
				"Plumbing", "HVAC", "Generator", "Fire Fighting", "Pest Control",
				"Parking", "Waste Management"]
	for s in services:
		if not frappe.db.exists("FCM Facility Service", s):
			frappe.get_doc({
				"doctype": "FCM Facility Service",
				"service_name": s,
				"service_category": s if s in [
					"Housekeeping", "Security", "Gardening", "Electrical", "Civil",
					"Plumbing", "HVAC", "Generator", "Fire Fighting", "Pest Control",
					"Parking", "Waste Management"] else "Housekeeping",
			}).insert(ignore_permissions=True)

	# Seed complaint categories (8.2 Complaint Categories) with sample SLAs
	complaint_categories = {
		"Cleaning": (2, 8), "Electrical": (1, 4), "Water Leakage": (1, 4),
		"AC": (2, 8), "Security": (0.5, 2), "Parking": (2, 8),
		"Internet": (2, 8), "Washroom": (2, 8), "Food Court": (2, 8), "Others": (4, 24),
	}
	for name, (resp, res) in complaint_categories.items():
		if not frappe.db.exists("FCM Complaint Category", name):
			frappe.get_doc({
				"doctype": "FCM Complaint Category",
				"category_name": name,
				"default_sla_response_hours": resp,
				"default_sla_resolution_hours": res,
			}).insert(ignore_permissions=True)
