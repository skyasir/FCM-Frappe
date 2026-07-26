**Food Court Management (FCM) — ERPNext Custom App**


A deployable Frappe/ERPNext custom app implementing the business scope in Food
Court Management ERP – Business Scope Document (v1.0, Innosphere Consulting LLP).
Built to install cleanly on a standard ERPNext instance (Frappe Cloud or self-hosted on
AWS Mumbai, per the scope doc) alongside the native Accounts, Buying (Procurement),
HR & Payroll, and CRM modules — those modules are reused as-is (ERPNext already
covers them fully) and extended only where the food-court business needs custom fields or
workflow. This keeps the app light, upgrade-safe, and fast to deploy.

1. What's included
Scope Section Implementation
1. Lease &
Contract
Management

FCM Food Court , FCM Floor , FCM Shop Unit , FCM Tenant KYC , FCM
Lease Contract (submittable, versioned via amended_from ), FCM
Contract Amendment , FCM Security Deposit Transaction . Business

rules enforced in code: no overlapping contracts, one active contract/unit, auto-
expiry, auto-escalation.

2. Sales &
Billing

billing.py engine: generate_monthly_rent_invoices() runs daily
and bills every contract whose billing_day_of_month matches. Creates
ERPNext Sales Invoices tagged with custom fields so native GST (India
Compliance), AR, and outstanding reports work unmodified. Approval step via
FCM Sales Invoice Approval workflow. Auto-email on submit
( utils.on_sales_invoice_submit ).

3. CAM FCM CAM Cost Category , FCM CAM Cost Entry .

allocate_and_bill_cam() implements: Total Cost → Deduct Vacant Area
Cost → Recoverable Cost → Tenant-wise Allocation (sqft / fixed rate) → Sales
Invoice. Triggered via the "Run CAM Allocation & Billing" button.

4. Utility
Billing

FCM Utility Meter , FCM Meter Reading (auto-computes consumption,
validates against previous reading). bill_meter_reading() raises a metered
Sales Invoice per tenant.

5. Revenue
Sharing

FCM Revenue Sales Upload + process_revenue_share() : implements

(Gross Sales × Rev% ) vs MG → higher value invoiced , duplicate-
upload detection, and API/CSV/manual entry via

billing_api.upload_tenant_sales / bulk_upload_sales_csv .

6.
Procurement

Uses ERPNext Buying module natively (Purchase Requisition → RFQ → PO →
Approval Matrix → Material Receipt → Purchase Invoice) — no rebuild needed.
fcm_food_court custom field added to Purchase Invoice for food-court-wise
spend reporting.

7. Facility
Management

FCM Facility Service , FCM Checklist Template , FCM Checklist
Execution (photo + supervisor verification gate before vendor bill approval —
enforced in validate() ). Mobile endpoint:
facility_api.complete_checklist .

8. Complaint
Management

FCM Complaint Category (with SLA hours), FCM Complaint (auto SLA
due-dates, breach flagging, daily re-check). Entry points: portal,
facility_api.file_complaint (mobile/API), reception.

Scope Section Implementation
9. Finance Native ERPNext Accounts module (GL, AR, AP, Banking, Fixed Assets, Financial
Reports) — Sales/Purchase Invoices from FCM flow straight into it. Cost Center
linked at Food Court level for Food-Court-wise P&L.

10. HR &
Payroll

Native ERPNext HR module. attendance_device_id custom field on
Employee + facility_api.biometric_attendance_webhook integrates
the 2 biometric devices into Employee Checkin, driving native
Attendance/Payroll.

11. CRM Native ERPNext CRM (Lead → Opportunity → Quotation) reused; FCM Shop
Unit.status drives Occupancy Management/Availability. Occupancy
Summary report covers Occupancy %.

Reports 4 ready-made Query Reports: Occupancy Summary, CAM Recovery Report,
Revenue Share vs MG Comparison, Outstanding by Food Court. More can be
added the same way.

Integrations 12 tenant-brand APIs → billing_api.upload_tenant_sales ; CSV/Excel
bulk → bulk_upload_sales_csv ; GST IRN → native India Compliance app
(install alongside); 2 biometric devices →
facility_api.biometric_attendance_webhook .

Security Custom roles ( FCM Manager , FCM User , FCM Facility Supervisor ,
FCM Accounts User ), doctype-level permissions, track_changes=1 (audit
trail) on all transactional doctypes, tenant-portal row-level restriction via
permission_query_conditions .

2. App structure

19 DocTypes generated (all with proper fields, naming series, permissions and — where
business logic applies — validate() / on_submit() controllers):
FCM Food Court, FCM Floor, FCM Shop Unit, FCM Tenant KYC, FCM Tenant KYC
Document, FCM Lease Contract, FCM Contract Amendment, FCM Security Deposit
Transaction, FCM CAM Cost Category, FCM CAM Cost Entry, FCM Utility Meter, FCM
Meter Reading, FCM Revenue Sales Upload, FCM Billing Run Log, FCM Facility Service,
FCM Checklist Template, FCM Checklist Execution, FCM Complaint Category, FCM
Complaint.
3. Deployment — step by step
Prerequisites
A bench with Frappe + ERPNext already installed (Frappe Cloud private bench, or
self-hosted per the scope doc's AWS Mumbai server). For India GST/e-invoicing (GST
IRN), also install the India Compliance app.
A. Get the app onto the bench
food_court_management/
├── food_court_management/
│ ├── hooks.py # scheduler jobs, fixtures, doc_events,
permissions
│ ├── install.py # after_install: seeds CAM categories,
facility services, complaint SLAs
│ ├── modules.txt # "Fcm"
│ ├── config/desktop.py # module icon/workspace registration
│ ├── fixtures/ # custom_field.json, role.json,
workflow.json
│ └── fcm/
│ ├── billing.py # core billing engine (rent, CAM, utility,
revenue share)
│ ├── utils.py # scheduler helpers, email, permission
queries
│ ├── api/ # billing_api.py, facility_api.py
(whitelisted REST endpoints)
│ ├── report/ # 4 Query Reports
│ └── doctype/ # 19 DocTypes (JSON + Python controllers)
├── setup.py / pyproject.toml / requirements.txt
├── license.txt (MIT)
└── README.md

bash

B.Install on the target site

install.py:after_install runs automatically and seeds:
17 CAM cost categories (3.1)
12 facility services (7.1)
10 complaint categories with default SLA hours (8.2/8.4)
C. Post-install configuration (functional setup, not code)
1. Company & Multi-entity: Create one ERPNext Company per Food Court (each is an
independent legal entity per the scope doc). Set default Cost Center per company.
2. Create Food Court, Floors, Shop Units ( FCM Food Court → FCM Floor → FCM Shop
Unit ).
3. Roles: Assign FCM Manager / FCM User / FCM Facility Supervisor / FCM
Accounts User to relevant Users (fixtures create the roles; permissions can be tuned
in Role Permission Manager).
4. Workflows: FCM Sales Invoice Approval and FCM Lease Contract Approval are
installed active — adjust states/transitions in Workflow if your approval matrix differs.
5. Item master: Billing items (Rental Charges, CAM Charges, Electricity Charges, Water
Charges, Revenue Share / MG Charges) are auto-created on first invoice run — no
manual setup needed.
6. Enable scheduler: bench --site foodcourt.yoursite.com enable-scheduler
(required for daily rent billing, escalations, SLA checks, contract expiry, and monthly
renewal reminders registered in hooks.py ).
7. Tenant brand API keys: For each of the 12 tenant integrations, generate an API
key/secret in Frappe (User → API Access) and share the upload_tenant_sales
endpoint URL: POST
/api/method/food_court_management.fcm.api.billing_api.upload_tenant_sales
8. Biometric devices: Point both devices' webhook/push config at: POST
/api/method/food_court_management.fcm.api.facility_api.biometric_attendanc
e_webhook after mapping each Employee's attendance_device_id .
# from your bench directory
bench get-app food_court_management /path/to/food_court_management # local co
# — or, once pushed to a private git repo —
bench get-app https://github.com/<your-org>/food_court_management.git

bash
bench --site foodcourt.yoursite.com install-app food_court_management
bench --site foodcourt.yoursite.com migrate # syncs doctypes, fixtures, cu
bench restart

9. GST IRN: Install & configure the India Compliance app per its own docs; FCM's Sales
Invoices are standard ERPNext Sales Invoices so e-invoicing works without changes.
D. Data migration (per scope doc Section "Data Migration")
Use standard Frappe Data Import tool (Setup → Data Import) for:
Masters: FCM Food Court , FCM Shop Unit , Customer / FCM Tenant KYC , Supplier ,
Employee
Open transactions: outstanding Sales Invoice / Purchase Invoice (import as-is
with an opening flag), active FCM Lease Contract records
Historical balances: via ERPNext's standard Opening Invoice Creation Tool / GL
opening entries
E. Rollout to additional Food Courts
Because each Food Court is its own ERPNext Company, rolling out to a new location is
config, not code: create the Company, Food Court/Floor/Shop Unit masters, and lease
contracts — the same installed app serves all Food Courts, keeping rollout projects small
per the scope doc's intent.
4. Key business rules encoded in code (not just documentation)
No overlapping contracts / one active contract per unit — enforced in
FCMLeaseContract.validate_no_overlapping_contract() .
Expired contracts cannot generate invoices —
generate_monthly_rent_invoices() only queries status = "Active" ;
expire_ended_contracts() (daily) flips status automatically.
Automatic escalation as per contract — apply_contract_escalations() (daily
scheduler).
CAM vacant-area cost is excluded from tenant recovery —
allocate_and_bill_cam() .
Revenue share formula, higher of RS or MG — process_revenue_share() .
Duplicate/missing sales upload detection — FCMRevenueSalesUpload.validate() .
Meter reading consumption validation (current ≥ previous) —
FCMMeterReading.validate() .
Checklist service verification gate (vendor bill approval requires supervisor
verification first) — FCMChecklistExecution.validate() .
Complaint SLA auto-calculation & breach detection — FCMComplaint .
All billing calls are idempotent per (contract, billing type, period) — safe to re-run
the scheduler without double-invoicing.
5. What's intentionally out of scope (per the client's Business Scope
Document)
Tenant POS systems, tenant-side ERPs, and advanced BI/analytics beyond the reports
listed above — exactly as stated under "Out of Scope" in the source document. Standard

ERPNext/ Frappe Insights can be layered on later if approved separately.
6. Extending this app
Add new Query Reports under fcm/report/<name>/ following the existing pattern.
Add new custom fields via fixtures/custom_field.json (re-run bench migrate to
sync).
Add a Print Format for FCM Lease Contract or invoices via the Desk UI, then export
it to fixtures/ ( bench --site <site> export-fixtures ) so it ships with the app.
