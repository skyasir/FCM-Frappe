app_name = "food_court_management"
app_title = "Food Court Management"
app_publisher = "Innosphere Consulting LLP"
app_description = "ERPNext-based Food Court Management System: Lease & Contract, Billing, CAM, Utility Billing, Revenue Sharing, Facility & Complaint Management"
app_email = "support@innosphereconsulting.com"
app_license = "MIT"
app_version = "1.0.0"

# Apps
# ------------------
required_apps = ["frappe", "erpnext"]

# Includes in <head>
# ------------------
app_include_css = "/assets/food_court_management/css/fcm.css"

# Fixtures - exported/synced on `bench migrate` so custom fields, roles,
# print formats and workflow ship with the app for every install.
# ------------------------------------------------------------------
fixtures = [
	{"dt": "Custom Field", "filters": [["module", "=", "Food Court Management"]]},
	{"dt": "Property Setter", "filters": [["module", "=", "Food Court Management"]]},
	{"dt": "Role", "filters": [["name", "in", ["FCM Manager", "FCM User", "FCM Facility Supervisor", "FCM Accounts User"]]]},
	{"dt": "Workflow", "filters": [["name", "in", ["FCM Sales Invoice Approval", "FCM Lease Contract Approval"]]]},
	{"dt": "Workflow State"},
	{"dt": "Workflow Action Master"},
	{"dt": "Print Format", "filters": [["module", "=", "Food Court Management"]]},
]

# Document Events
# ------------------------------------------------------------------
doc_events = {
	"Sales Invoice": {
		"on_submit": "food_court_management.fcm.utils.on_sales_invoice_submit",
	},
}

# Scheduled Tasks
# ------------------------------------------------------------------
scheduler_events = {
	"daily": [
		"food_court_management.fcm.billing.generate_monthly_rent_invoices",
		"food_court_management.fcm.doctype.fcm_lease_contract.fcm_lease_contract.apply_contract_escalations",
		"food_court_management.fcm.utils.mark_overdue_checklists",
		"food_court_management.fcm.utils.mark_overdue_complaints",
		"food_court_management.fcm.utils.expire_ended_contracts",
	],
	"monthly": [
		"food_court_management.fcm.utils.send_renewal_reminders",
	],
}

# Website Route Rules for Tenant Self-Service Portal
# ------------------------------------------------------------------
website_route_rules = [
	{"from_route": "/tenant-portal", "to_route": "tenant-portal"},
	{"from_route": "/tenant-portal/<path:app_path>", "to_route": "tenant-portal"},
]

# Permission query conditions to restrict tenants (Portal Users) to their own records
permission_query_conditions = {
	"FCM Complaint": "food_court_management.fcm.utils.tenant_permission_query",
	"FCM Lease Contract": "food_court_management.fcm.utils.tenant_permission_query",
}

has_permission = {
	"FCM Complaint": "food_court_management.fcm.utils.tenant_has_permission",
}

# Installation
# ------------------------------------------------------------------
after_install = "food_court_management.install.after_install"
