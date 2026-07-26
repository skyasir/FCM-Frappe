# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt
"""
Whitelisted REST endpoints consumed by: tenant brand POS integrations (5.1 Sales
Collection - API), the mobile app (checklist photo upload, PO approvals, complaint
filing), and 2 biometric device integrations (10.2 Attendance).

All endpoints are exposed at:
  /api/method/food_court_management.fcm.api.billing_api.<function_name>
"""

import json
import frappe
from frappe import _
from frappe.utils.file_manager import save_file
from food_court_management.fcm.billing import process_revenue_share, allocate_and_bill_cam


@frappe.whitelist(methods=["POST"])
def upload_tenant_sales(lease_contract, month, year, gross_sales, upload_method="API"):
	"""5.1 Sales Collection: tenant brand systems POST daily/monthly gross sales here."""
	if not frappe.db.exists("FCM Lease Contract", lease_contract):
		frappe.throw(_("Invalid Lease Contract"))
	doc = frappe.get_doc({
		"doctype": "FCM Revenue Sales Upload",
		"lease_contract": lease_contract,
		"month": month,
		"year": year,
		"gross_sales": gross_sales,
		"upload_method": upload_method,
	}).insert(ignore_permissions=True)
	return process_revenue_share(doc.name)


@frappe.whitelist(methods=["POST"])
def bulk_upload_sales_csv():
	"""5.1 Sales Collection - CSV/Excel Upload. Accepts an uploaded file (multipart)
	with columns: lease_contract, month, year, gross_sales."""
	import csv
	from io import StringIO

	if "file" not in frappe.request.files:
		frappe.throw(_("No file uploaded"))
	f = frappe.request.files["file"]
	content = f.stream.read().decode("utf-8")
	reader = csv.DictReader(StringIO(content))

	results = []
	for row in reader:
		try:
			doc = frappe.get_doc({
				"doctype": "FCM Revenue Sales Upload",
				"lease_contract": row["lease_contract"],
				"month": row["month"],
				"year": int(row["year"]),
				"gross_sales": float(row["gross_sales"]),
				"upload_method": "CSV Upload",
			}).insert(ignore_permissions=True)
			result = process_revenue_share(doc.name)
			results.append({"row": row, "status": "success", "result": result})
		except Exception as e:
			results.append({"row": row, "status": "error", "error": str(e)})
	return results


@frappe.whitelist(methods=["POST"])
def run_cam_allocation(food_court, month, year):
	"""Manually trigger CAM allocation & billing for a period (also runnable from UI button)."""
	return allocate_and_bill_cam(food_court, month, year)


@frappe.whitelist()
def get_outstanding_summary(tenant=None):
	"""2.6 Billing Cycle -> Outstanding Report, exposed for the tenant portal / mobile app."""
	filters = {"outstanding_amount": [">", 0], "docstatus": 1}
	if tenant:
		filters["customer"] = tenant
	return frappe.get_all("Sales Invoice", filters=filters,
		fields=["name", "customer", "posting_date", "due_date", "grand_total",
				"outstanding_amount", "fcm_billing_type", "fcm_lease_contract"])
