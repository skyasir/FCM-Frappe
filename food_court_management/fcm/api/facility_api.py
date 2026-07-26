# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt
"""Mobile app endpoints for facility checklist completion and complaint filing."""

import frappe
from frappe import _
from frappe.utils.file_manager import save_file


@frappe.whitelist(methods=["POST"])
def complete_checklist(checklist_execution, remarks=None):
	"""Mobile app: mark a checklist task complete with a photo (7.3 Service Verification)."""
	doc = frappe.get_doc("FCM Checklist Execution", checklist_execution)
	if "photo" in frappe.request.files:
		saved = save_file(
			frappe.request.files["photo"].filename,
			frappe.request.files["photo"].read(),
			"FCM Checklist Execution", checklist_execution, is_private=0)
		doc.photo = saved.file_url
	doc.status = "Completed"
	doc.completion_date = frappe.utils.nowdate()
	if remarks:
		doc.remarks = remarks
	doc.save(ignore_permissions=True)
	return {"status": "ok", "name": doc.name}


@frappe.whitelist(methods=["POST"])
def file_complaint(food_court, complaint_category, description, shop_unit=None,
					tenant=None, complaint_source="Mobile App"):
	"""8.1 Complaint Sources: Customer Portal / Mobile App / Email / Phone -> single entry point."""
	doc = frappe.get_doc({
		"doctype": "FCM Complaint",
		"food_court": food_court,
		"complaint_category": complaint_category,
		"description": description,
		"shop_unit": shop_unit,
		"tenant": tenant,
		"complaint_source": complaint_source,
	}).insert(ignore_permissions=True)
	return {"status": "ok", "name": doc.name}


@frappe.whitelist(methods=["POST"])
def biometric_attendance_webhook(employee_biometric_id, timestamp, device_id, log_type="IN"):
	"""10.2 Attendance: Biometric Integration. Receives punches from the 2 biometric
	devices and creates ERPNext Employee Checkin records."""
	employee = frappe.db.get_value("Employee", {"attendance_device_id": employee_biometric_id}, "name")
	if not employee:
		frappe.throw(_("No employee mapped to biometric device ID {0}").format(employee_biometric_id))
	checkin = frappe.get_doc({
		"doctype": "Employee Checkin",
		"employee": employee,
		"time": timestamp,
		"log_type": log_type,
		"device_id": device_id,
	}).insert(ignore_permissions=True)
	return {"status": "ok", "name": checkin.name}
