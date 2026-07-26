# Copyright (c) 2026, Innosphere Consulting LLP and contributors
# For license information, please see license.txt
"""
Core Billing Engine for Food Court Management.
Implements: 2.6 Billing Cycle -> Contract > Scheduler > Invoice Creation >
Approval > Email Customer > Accounts Receivable > Collection > Receipt > Outstanding Report

All functions are idempotent per (contract, month, year) to allow safe re-runs.
"""

import json
import frappe
from frappe import _
from frappe.utils import nowdate, getdate, flt, add_days, today, get_first_day, get_last_day


# ---------------------------------------------------------------------------
# 1. RENT / MINIMUM GUARANTEE BILLING
# ---------------------------------------------------------------------------

def generate_monthly_rent_invoices(posting_date=None):
	"""Scheduled monthly (or callable via API): auto-generate rent/MG invoices
	for every Active contract whose billing_day_of_month == today's date.
	Business Rule: Expired contracts cannot generate invoices."""
	posting_date = getdate(posting_date or nowdate())
	day = posting_date.day

	contracts = frappe.get_all("FCM Lease Contract",
		filters={"status": "Active", "billing_day_of_month": day},
		fields=["name", "tenant", "food_court", "shop_unit", "rent_amount",
				"minimum_guarantee", "payment_terms_days", "company" if frappe.db.has_column("FCM Lease Contract", "company") else "name"])

	created, errors = [], []
	for c in contracts:
		try:
			if _invoice_already_exists(c.name, "Rent/MG", posting_date):
				continue
			si = _make_sales_invoice(
				customer=c.tenant,
				items=[{
					"item_code": _get_or_create_billing_item("Rental Charges", "Services"),
					"qty": 1,
					"rate": flt(c.rent_amount),
					"description": f"Rent for {posting_date.strftime('%B %Y')} - Contract {c.name}",
				}],
				due_days=c.payment_terms_days or 7,
				reference_contract=c.name,
				billing_type="Rent/MG",
			)
			created.append(si)
		except Exception as e:
			errors.append({"contract": c.name, "error": str(e)})
			frappe.log_error(title="FCM Rent Billing Error", message=frappe.get_traceback())

	_log_billing_run("Rent/MG", posting_date, len(contracts), created, errors)
	return {"created": created, "errors": errors}


# ---------------------------------------------------------------------------
# 2. CAM BILLING (3.2 Allocation Methods, 3.3 CAM Recovery)
# ---------------------------------------------------------------------------

def allocate_and_bill_cam(food_court, month, year):
	"""3.3 CAM Recovery: Total CAM Cost > Deduct Vacant Area Cost >
	Calculate Recoverable Cost > Allocate Tenant-wise > Generate CAM Invoice"""
	cost_entries = frappe.get_all("FCM CAM Cost Entry",
		filters={"food_court": food_court, "month": month, "year": year, "status": "Pending Allocation"},
		fields=["name", "amount", "allocation_method", "cost_category"])
	if not cost_entries:
		return {"message": "No pending CAM cost entries for this period"}

	total_cost = sum(flt(e.amount) for e in cost_entries)

	fc = frappe.get_doc("FCM Food Court", food_court)
	total_leasable = flt(fc.leasable_area_sqft) or 1

	active_contracts = frappe.get_all("FCM Lease Contract",
		filters={"food_court": food_court, "status": "Active", "cam_applicable": 1},
		fields=["name", "tenant", "shop_unit", "cam_rate_per_sqft", "payment_terms_days"])

	# fetch chargeable area per shop unit
	occupied_area = 0
	unit_area_map = {}
	for c in active_contracts:
		area = frappe.db.get_value("FCM Shop Unit", c.shop_unit, "chargeable_area_sqft") or 0
		unit_area_map[c.name] = area
		occupied_area += area

	vacant_area = max(total_leasable - occupied_area, 0)
	vacant_area_cost = total_cost * (vacant_area / total_leasable) if total_leasable else 0
	recoverable_cost = total_cost - vacant_area_cost

	created, errors = [], []
	for c in active_contracts:
		try:
			if _invoice_already_exists(c.name, "CAM", getdate(f"{year}-{_month_num(month):02d}-01")):
				continue
			area = unit_area_map.get(c.name, 0)
			# Square Foot Basis allocation (primary method); rate override supported
			if c.cam_rate_per_sqft:
				tenant_share = flt(c.cam_rate_per_sqft) * area
			else:
				tenant_share = recoverable_cost * (area / occupied_area) if occupied_area else 0

			si = _make_sales_invoice(
				customer=c.tenant,
				items=[{
					"item_code": _get_or_create_billing_item("CAM Charges", "Services"),
					"qty": 1,
					"rate": flt(tenant_share),
					"description": f"CAM Charges for {month} {year} - Contract {c.name}",
				}],
				due_days=c.payment_terms_days or 7,
				reference_contract=c.name,
				billing_type="CAM",
			)
			created.append(si)
		except Exception as e:
			errors.append({"contract": c.name, "error": str(e)})
			frappe.log_error(title="FCM CAM Billing Error", message=frappe.get_traceback())

	for e in cost_entries:
		frappe.db.set_value("FCM CAM Cost Entry", e.name, "status", "Allocated")

	_log_billing_run("CAM", getdate(), len(active_contracts), created, errors, food_court=food_court)
	return {
		"total_cost": total_cost, "vacant_area_cost": vacant_area_cost,
		"recoverable_cost": recoverable_cost, "invoices_created": created, "errors": errors,
	}


# ---------------------------------------------------------------------------
# 3. UTILITY BILLING (Electricity / Water - Meter Based)
# ---------------------------------------------------------------------------

def bill_meter_reading(meter_reading_name):
	"""4. Utility Billing: Meter Reading Entry > Consumption Validation > Allocation > Sales Invoice"""
	mr = frappe.get_doc("FCM Meter Reading", meter_reading_name)
	if mr.billed:
		frappe.throw(_("This meter reading is already billed"))

	meter = frappe.get_doc("FCM Utility Meter", mr.meter)
	if not meter.shop_unit:
		frappe.throw(_("Cannot bill a common-area meter directly to a tenant; use CAM allocation instead"))

	contract = frappe.db.get_value("FCM Lease Contract",
		{"shop_unit": meter.shop_unit, "status": "Active"}, ["name", "tenant", "payment_terms_days"], as_dict=True)
	if not contract:
		frappe.throw(_("No active contract found for Shop/Unit {0}").format(meter.shop_unit))

	item_name = "Electricity Charges" if meter.meter_type == "Electricity" else "Water Charges"
	si = _make_sales_invoice(
		customer=contract.tenant,
		items=[{
			"item_code": _get_or_create_billing_item(item_name, "Services"),
			"qty": flt(mr.consumption),
			"rate": flt(mr.rate_per_unit),
			"uom": meter.uom,
			"description": f"{item_name} - Meter {meter.name} - Reading {mr.reading_date}",
		}],
		due_days=contract.payment_terms_days or 7,
		reference_contract=contract.name,
		billing_type=meter.meter_type,
	)
	mr.db_set("billed", 1)
	return si


# ---------------------------------------------------------------------------
# 4. REVENUE SHARE (5.3 Formula: (Gross Sales x Rev% ) less MG = Net Invoice)
# ---------------------------------------------------------------------------

def process_revenue_share(revenue_upload_name):
	"""5.2 Validation + 5.3 Revenue Share Formula + Sales Invoice creation."""
	doc = frappe.get_doc("FCM Revenue Sales Upload", revenue_upload_name)

	# 5.2 Validation: Duplicate check
	dup = frappe.db.exists("FCM Revenue Sales Upload", {
		"lease_contract": doc.lease_contract, "month": doc.month, "year": doc.year,
		"name": ["!=", doc.name],
	})
	doc.is_duplicate = 1 if dup else 0

	contract = frappe.get_doc("FCM Lease Contract", doc.lease_contract)
	rev_share_pct = flt(doc.revenue_share_percent or contract.revenue_share_percent)
	revenue_share_amount = flt(doc.gross_sales) * rev_share_pct / 100
	mg = flt(doc.minimum_guarantee or contract.minimum_guarantee)

	# Net Invoice = Higher of Revenue Share or Minimum Guarantee
	net_invoice = max(revenue_share_amount, mg)

	doc.revenue_share_amount = revenue_share_amount
	doc.net_invoice_amount = net_invoice
	doc.is_validated = 1
	doc.save(ignore_permissions=True)

	if doc.is_duplicate:
		frappe.throw(_("Duplicate sales upload detected for this contract/period. Not invoicing."))

	if _invoice_already_exists(contract.name, "Revenue Share", getdate(f"{doc.year}-{_month_num(doc.month):02d}-01")):
		return {"message": "Already invoiced for this period"}

	si = _make_sales_invoice(
		customer=contract.tenant,
		items=[{
			"item_code": _get_or_create_billing_item("Revenue Share / MG Charges", "Services"),
			"qty": 1,
			"rate": net_invoice,
			"description": f"Revenue Share for {doc.month} {doc.year} (Gross Sales: {doc.gross_sales}, "
						   f"Rev Share: {revenue_share_amount}, MG: {mg})",
		}],
		due_days=contract.payment_terms_days or 7,
		reference_contract=contract.name,
		billing_type="Revenue Share",
	)
	doc.db_set("sales_invoice_reference", si)
	return {"sales_invoice": si, "revenue_share_amount": revenue_share_amount, "net_invoice_amount": net_invoice}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _month_num(month_name):
	months = ["January","February","March","April","May","June","July",
			  "August","September","October","November","December"]
	return months.index(month_name) + 1 if month_name in months else 1


def _invoice_already_exists(contract, billing_type, period_date):
	"""Idempotency guard so re-running the scheduler never double-bills."""
	return frappe.db.exists("Sales Invoice", {
		"fcm_lease_contract": contract,
		"fcm_billing_type": billing_type,
		"fcm_billing_period": period_date.strftime("%Y-%m"),
		"docstatus": ["!=", 2],
	})


def _get_or_create_billing_item(item_name, item_group="Services"):
	if not frappe.db.exists("Item", item_name):
		frappe.get_doc({
			"doctype": "Item",
			"item_code": item_name,
			"item_name": item_name,
			"item_group": item_group,
			"is_stock_item": 0,
			"is_sales_item": 1,
		}).insert(ignore_permissions=True)
	return item_name


def _make_sales_invoice(customer, items, due_days, reference_contract, billing_type):
	"""Creates a draft Sales Invoice. Custom fields fcm_lease_contract / fcm_billing_type /
	fcm_billing_period are added via fixtures (see fixtures/custom_field.json) so that
	standard ERPNext Accounts Receivable, GST (India Compliance), and Outstanding
	Reports work without any change to core Sales Invoice logic."""
	si = frappe.new_doc("Sales Invoice")
	si.customer = customer
	si.due_date = add_days(nowdate(), due_days)
	si.fcm_lease_contract = reference_contract
	si.fcm_billing_type = billing_type
	si.fcm_billing_period = nowdate()[:7]
	for row in items:
		si.append("items", row)
	si.insert(ignore_permissions=True)
	# 2.6 Billing Cycle: Approval step left to workflow (see fixtures/workflow.json);
	# submit only when approved. Draft invoices appear in the Approval worklist.
	return si.name


def _log_billing_run(billing_type, run_date, processed, created, errors, food_court=None):
	frappe.get_doc({
		"doctype": "FCM Billing Run Log",
		"billing_type": billing_type,
		"food_court": food_court,
		"run_date": frappe.utils.now_datetime(),
		"period_month": run_date.strftime("%B"),
		"period_year": run_date.year,
		"total_contracts_processed": processed,
		"total_invoices_created": len(created),
		"total_amount": 0,
		"errors": json.dumps(errors),
		"status": "Success" if not errors else "Completed with Errors",
	}).insert(ignore_permissions=True)
	frappe.db.commit()
