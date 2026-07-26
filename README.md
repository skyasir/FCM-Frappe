# Food Court Management (FCM) — ERPNext Custom App

A deployable Frappe/ERPNext custom app implementing the business scope in the *Food Court Management ERP – Business Scope Document* (v1.0, Innosphere Consulting LLP).

It installs cleanly on a standard ERPNext instance (Frappe Cloud or self-hosted) alongside the native **Accounts, Buying (Procurement), HR & Payroll, and CRM** modules. Those modules are reused as-is — ERPNext already covers them fully — and are extended only where the food-court business needs custom fields or workflow. This keeps the app light, upgrade-safe, and fast to deploy.

- **Frappe/ERPNext compatibility:** v15 and v16
- **License:** MIT
- **Module:** `Fcm` &nbsp;|&nbsp; **App name:** `food_court_management`

---

## 1. What's included

| # | Scope section | Implementation |
|---|---------------|----------------|
| 1 | **Lease & Contract Management** | `FCM Food Court`, `FCM Floor`, `FCM Shop Unit`, `FCM Tenant KYC`, `FCM Lease Contract` (submittable, versioned via `amended_from`), `FCM Contract Amendment`, `FCM Security Deposit Transaction`. Business rules enforced in code: no overlapping contracts, one active contract per unit, auto-expiry, auto-escalation. |
| 2 | **Sales & Billing** | `billing.py` engine: `generate_monthly_rent_invoices()` runs daily and bills every contract whose `billing_day_of_month` matches. Creates ERPNext Sales Invoices tagged with custom fields so native GST (India Compliance), AR, and outstanding reports work unmodified. Approval via the `FCM Sales Invoice Approval` workflow. Auto-email on submit (`utils.on_sales_invoice_submit`). |
| 3 | **CAM** | `FCM CAM Cost Category`, `FCM CAM Cost Entry`. `allocate_and_bill_cam()` implements: Total Cost → deduct vacant-area cost → recoverable cost → tenant-wise allocation (sqft / fixed rate) → Sales Invoice. Triggered via the **Run CAM Allocation & Billing** button. |
| 4 | **Utility Billing** | `FCM Utility Meter`, `FCM Meter Reading` (auto-computes consumption, validates against the previous reading). `bill_meter_reading()` raises a metered Sales Invoice per tenant. |
| 5 | **Revenue Sharing** | `FCM Revenue Sales Upload` + `process_revenue_share()`: `(Gross Sales × Rev%)` vs MG → the higher value is invoiced, with duplicate-upload detection and API/CSV/manual entry via `billing_api.upload_tenant_sales` / `bulk_upload_sales_csv`. |
| 6 | **Procurement** | Uses the ERPNext Buying module natively (Purchase Requisition → RFQ → PO → Approval Matrix → Material Receipt → Purchase Invoice) — no rebuild needed. A `fcm_food_court` custom field is added to Purchase Invoice for food-court-wise spend reporting. |
| 7 | **Facility Management** | `FCM Facility Service`, `FCM Checklist Template`, `FCM Checklist Execution` (photo + supervisor verification gate before vendor-bill approval — enforced in `validate()`). Mobile endpoint: `facility_api.complete_checklist`. |
| 8 | **Complaint Management** | `FCM Complaint Category` (with SLA hours), `FCM Complaint` (auto SLA due-dates, breach flagging, daily re-check). Entry points: tenant portal, `facility_api.file_complaint` (mobile/API), reception. |
| 9 | **Finance** | Native ERPNext Accounts module (GL, AR, AP, Banking, Fixed Assets, Financial Reports) — Sales/Purchase Invoices from FCM flow straight into it. Cost Center linked at Food Court level for food-court-wise P&L. |
| 10 | **HR & Payroll** | Native ERPNext HR module. An `attendance_device_id` custom field on Employee + `facility_api.biometric_attendance_webhook` integrates the two biometric devices into Employee Checkin, driving native Attendance/Payroll. |
| 11 | **CRM** | Native ERPNext CRM (Lead → Opportunity → Quotation) reused; `FCM Shop Unit.status` drives Occupancy Management/Availability. The Occupancy Summary report covers Occupancy %. |

**Reports** — 4 ready-made Query Reports: Occupancy Summary, CAM Recovery Report, Revenue Share vs MG Comparison, Outstanding by Food Court. More can be added the same way.

**Integrations** — 12 tenant-brand APIs → `billing_api.upload_tenant_sales`; CSV/Excel bulk → `bulk_upload_sales_csv`; GST IRN → native India Compliance app (install alongside); 2 biometric devices → `facility_api.biometric_attendance_webhook`.

**Security** — Custom roles (`FCM Manager`, `FCM User`, `FCM Facility Supervisor`, `FCM Accounts User`), doctype-level permissions, `track_changes = 1` (audit trail) on all transactional doctypes, and tenant-portal row-level restriction via `permission_query_conditions`.

---

## 2. App structure

19 DocTypes are generated (all with proper fields, naming series, permissions and — where business logic applies — `validate()` / `on_submit()` controllers):

> FCM Food Court · FCM Floor · FCM Shop Unit · FCM Tenant KYC · FCM Tenant KYC Document · FCM Lease Contract · FCM Contract Amendment · FCM Security Deposit Transaction · FCM CAM Cost Category · FCM CAM Cost Entry · FCM Utility Meter · FCM Meter Reading · FCM Revenue Sales Upload · FCM Billing Run Log · FCM Facility Service · FCM Checklist Template · FCM Checklist Execution · FCM Complaint Category · FCM Complaint

```text
food_court_management/                  # repo root
├── pyproject.toml / setup.py / requirements.txt
├── license.txt                         # MIT
├── README.md
└── food_court_management/              # app package
    ├── hooks.py                        # scheduler jobs, fixtures, doc_events, permissions
    ├── patches.txt
    ├── install.py                      # after_install: seeds CAM categories, facility services, complaint SLAs
    ├── modules.txt                     # "Fcm"
    ├── config/desktop.py               # module icon / workspace registration
    ├── fixtures/                       # custom_field.json, role.json, workflow.json
    └── fcm/
        ├── billing.py                  # core billing engine (rent, CAM, utility, revenue share)
        ├── utils.py                    # scheduler helpers, email, permission queries
        ├── api/                        # billing_api.py, facility_api.py (whitelisted REST endpoints)
        ├── report/                     # 4 Query Reports
        └── doctype/                    # 19 DocTypes (JSON + Python controllers)
```

---

## 3. Deployment — step by step

### Prerequisites

A bench with **Frappe + ERPNext** already installed (Frappe Cloud private bench, or self-hosted). For India GST/e-invoicing (GST IRN), also install the **India Compliance** app.

### A. Get the app onto the bench

```bash
# from your bench directory — local copy:
bench get-app food_court_management /path/to/food_court_management

# — or, from a git repo:
bench get-app https://github.com/skyasir/FCM-Frappe.git
```

### B. Install on the target site

```bash
bench --site foodcourt.yoursite.com install-app food_court_management
bench --site foodcourt.yoursite.com migrate     # syncs doctypes, fixtures, custom fields
bench restart
```

`install.py:after_install` runs automatically and seeds:

- 17 CAM cost categories (scope 3.1)
- 12 facility services (scope 7.1)
- 10 complaint categories with default SLA hours (scope 8.2 / 8.4)

### C. Post-install configuration (functional setup, not code)

1. **Company & multi-entity** — Create one ERPNext Company per Food Court (each is an independent legal entity per the scope doc). Set a default Cost Center per company.
2. **Masters** — Create Food Court, Floors, and Shop Units (`FCM Food Court` → `FCM Floor` → `FCM Shop Unit`).
3. **Roles** — Assign `FCM Manager` / `FCM User` / `FCM Facility Supervisor` / `FCM Accounts User` to the relevant Users (fixtures create the roles; permissions can be tuned in Role Permission Manager).
4. **Workflows** — `FCM Sales Invoice Approval` and `FCM Lease Contract Approval` install active — adjust states/transitions in Workflow if your approval matrix differs.
5. **Item master** — Billing items (Rental Charges, CAM Charges, Electricity Charges, Water Charges, Revenue Share / MG Charges) are auto-created on the first invoice run — no manual setup needed.
6. **Enable the scheduler** — required for daily rent billing, escalations, SLA checks, contract expiry, and monthly renewal reminders:
   ```bash
   bench --site foodcourt.yoursite.com enable-scheduler
   ```
7. **Tenant brand API keys** — For each of the 12 tenant integrations, generate an API key/secret in Frappe (User → API Access) and share the upload endpoint:
   ```
   POST /api/method/food_court_management.fcm.api.billing_api.upload_tenant_sales
   ```
8. **Biometric devices** — After mapping each Employee's `attendance_device_id`, point both devices' webhook/push config at:
   ```
   POST /api/method/food_court_management.fcm.api.facility_api.biometric_attendance_webhook
   ```
9. **GST IRN** — Install & configure the India Compliance app per its own docs; FCM's Sales Invoices are standard ERPNext Sales Invoices, so e-invoicing works without changes.

### D. Data migration

Use the standard Frappe Data Import tool (Setup → Data Import) for:

- **Masters:** `FCM Food Court`, `FCM Shop Unit`, Customer / `FCM Tenant KYC`, Supplier, Employee
- **Open transactions:** outstanding Sales / Purchase Invoices (import as-is with an opening flag), active `FCM Lease Contract` records
- **Historical balances:** via ERPNext's standard Opening Invoice Creation Tool / GL opening entries

### E. Rollout to additional Food Courts

Because each Food Court is its own ERPNext Company, rolling out to a new location is **config, not code**: create the Company, the Food Court/Floor/Shop Unit masters, and the lease contracts. The same installed app serves all Food Courts, keeping rollout projects small.

---

## 4. Key business rules encoded in code

These are enforced in code, not just documented:

- **No overlapping contracts / one active contract per unit** — `FCMLeaseContract.validate_no_overlapping_contract()`.
- **Expired contracts cannot generate invoices** — `generate_monthly_rent_invoices()` only queries `status = "Active"`; `expire_ended_contracts()` (daily) flips status automatically.
- **Automatic escalation per contract** — `apply_contract_escalations()` (daily scheduler).
- **CAM vacant-area cost excluded from tenant recovery** — `allocate_and_bill_cam()`.
- **Revenue share = higher of RS or MG** — `process_revenue_share()`.
- **Duplicate/missing sales-upload detection** — `FCMRevenueSalesUpload.validate()`.
- **Meter-reading consumption validation (current ≥ previous)** — `FCMMeterReading.validate()`.
- **Checklist verification gate** (vendor-bill approval requires supervisor verification first) — `FCMChecklistExecution.validate()`.
- **Complaint SLA auto-calculation & breach detection** — `FCMComplaint`.
- **Idempotent billing** — all billing calls are idempotent per `(contract, billing type, period)`, so the scheduler is safe to re-run without double-invoicing.

---

## 5. Out of scope

Per the client's Business Scope Document: tenant POS systems, tenant-side ERPs, and advanced BI/analytics beyond the reports listed above. Standard ERPNext / Frappe Insights can be layered on later if approved separately.

---

## 6. Extending this app

- Add new Query Reports under `fcm/report/<name>/` following the existing pattern.
- Add new custom fields via `fixtures/custom_field.json`, then re-run `bench migrate` to sync.
- Add a Print Format for `FCM Lease Contract` or invoices via the Desk UI, then export it so it ships with the app:
  ```bash
  bench --site <site> export-fixtures
  ```
