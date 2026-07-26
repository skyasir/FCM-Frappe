# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate, getdate, add_days, now_datetime


def on_sales_invoice_submit(doc, method):
	"""2.6 Billing Cycle: ... Approval > Email Customer > Accounts Receivable ...
	Auto-email the invoice PDF to the tenant on submit (2.8 Invoice Delivery)."""
	if not doc.get("fcm_lease_contract"):
		return
	tenant_email = frappe.db.get_value("Customer", doc.customer, "email_id")
	if tenant_email:
		frappe.sendmail(
			recipients=[tenant_email],
			subject=f"Invoice {doc.name} - {doc.get('fcm_billing_type') or 'Charges'}",
			message=f"Dear Tenant,<br>Please find attached invoice {doc.name} for "
					f"{doc.get('fcm_billing_type')} amounting to {doc.grand_total}.<br>"
					f"Due date: {doc.due_date}.<br><br>Regards,<br>Food Court Management",
			attachments=[frappe.attach_print("Sales Invoice", doc.name, print_format="Standard")],
		)


def mark_overdue_checklists():
	"""7.2/7.3 Checklist Management: flag past-due, uncompleted checklist executions."""
	frappe.db.sql("""
		UPDATE `tabFCM Checklist Execution`
		SET status = 'Overdue'
		WHERE status = 'Pending' AND due_date < %s
	""", (nowdate(),))
	frappe.db.commit()


def mark_overdue_complaints():
	"""8.4 SLA: recompute breach flag daily for open complaints."""
	open_complaints = frappe.get_all("FCM Complaint",
		filters={"status": ["not in", ["Closed", "Completed"]]}, pluck="name")
	for name in open_complaints:
		doc = frappe.get_doc("FCM Complaint", name)
		doc.check_sla_breach()
		doc.db_update()
	frappe.db.commit()


def expire_ended_contracts():
	"""1.7 Business Rule: Expired contracts cannot generate invoices."""
	ended = frappe.get_all("FCM Lease Contract",
		filters={"status": "Active", "contract_end_date": ["<", nowdate()]}, pluck="name")
	for name in ended:
		frappe.db.set_value("FCM Lease Contract", name, "status", "Expired")
		shop_unit = frappe.db.get_value("FCM Lease Contract", name, "shop_unit")
		if shop_unit:
			frappe.db.set_value("FCM Shop Unit", shop_unit, "status", "Vacant")
	frappe.db.commit()


def send_renewal_reminders():
	"""1.4 Contract Renewals: reminders for contracts ending within 90 days."""
	upcoming = frappe.get_all("FCM Lease Contract",
		filters={"status": "Active", "contract_end_date": ["between", [nowdate(), add_days(nowdate(), 90)]]},
		fields=["name", "tenant", "contract_end_date"])
	for c in upcoming:
		tenant_email = frappe.db.get_value("Customer", c.tenant, "email_id")
		recipients = [tenant_email] if tenant_email else []
		frappe.sendmail(
			recipients=recipients or ["admin@example.com"],
			subject=f"Lease Renewal Reminder - Contract {c.name}",
			message=f"Contract {c.name} is due to expire on {c.contract_end_date}. "
					f"Please initiate renewal discussions.",
		)


def tenant_permission_query(user):
	"""Restrict Tenant Portal users to see only their own records."""
	if not user:
		user = frappe.session.user
	if "System Manager" in frappe.get_roles(user) or "FCM Manager" in frappe.get_roles(user):
		return ""
	customer = frappe.db.get_value("Contact", {"user": user}, "name")
	if not customer:
		return "1=0"
	linked_customer = frappe.db.get_value("Dynamic Link", {"parent": customer, "link_doctype": "Customer"}, "link_name")
	if not linked_customer:
		return "1=0"
	return f"`tabFCM Lease Contract`.tenant = {frappe.db.escape(linked_customer)}"


def tenant_has_permission(doc, user=None, permission_type=None):
	if not user:
		user = frappe.session.user
	if "System Manager" in frappe.get_roles(user) or "FCM Manager" in frappe.get_roles(user):
		return True
	customer = frappe.db.get_value("Contact", {"user": user}, "name")
	if not customer:
		return False
	linked_customer = frappe.db.get_value("Dynamic Link", {"parent": customer, "link_doctype": "Customer"}, "link_name")
	return doc.tenant == linked_customer if hasattr(doc, "tenant") else False
