# Technical Specification Document

**Project:** Employee Advance Enhanced (App: `eae`)  
**Date:** 2025-12-01  
**Prepared By:** Riz (Frappe Architect)  
**Status:** Draft  
**Based On:** `apps/eae/docs/requirements/Employee Advance Enhancement-requirements-2025-12-01.md`

---

## 1. Executive Summary

This Technical Specification defines a general-purpose Employee Advance Enhancement for ERPNext/HRMS that automates and structures advance repayments while staying as close as possible to standard HRMS behavior.

Key goals:

- Keep **Employee Advance** as the financial source of truth, using standard fields:
  - `paid_amount` (amount disbursed to the employee)
  - `return_amount` (amount returned from all channels)
- Introduce a dedicated **Repayment Schedule** model that:
  - Plans installment dates and amounts
  - Surfaces schedule progress to HR/Payroll/Finance and employees
  - Drives automatic **Additional Salary** creation for advance repayments
- Use **Additional Salary** and **Salary Component** as the only integration point into payroll (no custom payroll engine).
- Provide a native Frappe UX: Desk-based, with a clear “Repayment Schedule” tab on Employee Advance, and minimal configuration burden.

The result: HR configures a schedule once; the system generates one Additional Salary per installment due date, which flows into Salary Slips and increments `return_amount` automatically. Bulk repayments (e.g. via Payment Entry/Journal Entry) are still supported and will close the schedule cleanly.

---

## 2. 4‑Tier Framework Analysis

### 2.1 Requirements in Scope (Refined)

From the BRD, the solution focuses on these refined requirements:

1. Unified remaining balance per Employee Advance, using existing `paid_amount` and `return_amount`.
2. Repayment schedule generation by **fixed number of installments**.
3. Repayment schedule generation by **fixed installment amount**.
4. Support for multiple repayment frequencies: **Monthly, Semi-monthly, Every 3 Months**.
5. Adjustable schedules with automatic recalculation of **future** installments only.
6. Automatic closure of advance and schedule once fully settled.
7. Resignation/termination and other bulk repayment scenarios handled via **return_amount** only (no special Final Settlement hooks).
8. Clear roles/permissions across HR, Payroll, Finance, and employees (via Desk).
9. Dedicated **Repayment Schedule DocType** per Employee Advance.
10. Repayment schedule preview tab/section inside Employee Advance (used by HR/Payroll/Finance and employees).
11. Automatic creation of **Additional Salary** entries per installment so repayments flow into Salary Slip in a standard way.

(The BRD’s original “multi-channel settlement” requirement is implicitly satisfied by HRMS: any repayment channel that updates `return_amount` is considered; this TSD does not introduce new channels.)

### 2.2 Tier Mapping Summary

- **Tier 1 – Standard:**
  - Employee Advance, Additional Salary, Salary Component, Employee, Company, Salary Slip, Payroll Entry remain standard.

- **Tier 2 – Configuration:**
  - Custom field on `Salary Component` to mark **repayment components**.
  - Role and permission configuration for the new schedule DocType.
  - Form layout updates: “Repayment Schedule” tab on Employee Advance.

- **Tier 3 – Scripts:**
  - Server logic on Employee Advance to react to `return_amount` changes and close the advance/schedule.
  - Background job that creates **non-recurring Additional Salary** entries from due schedule rows.
  - Server methods for schedule preview and on-the-fly schedule generation.
  - Client scripts for Employee Advance to drive dialogs and UI behavior.

- **Tier 4 – Custom App:**
  - New DocTypes:
    - `Employee Advance Repayment Schedule` (parent)
    - `Employee Advance Repayment Installment` (child)
  - All schedule generation, adjustment, and schedule UI logic lives in app `eae`.

---

## 3. Architectural Decisions (Key ADRs)

### ADR‑1: Dedicated Repayment Schedule DocType

- **Context:** We need a structured, auditable home for the repayment plan per Employee Advance.
- **Decision:** Create `Employee Advance Repayment Schedule` with a child table for installments, linked 1:1 to Employee Advance.
- **Rationale:**
  - Keeps Employee Advance relatively clean and focused on financial truth (`paid_amount`, `return_amount`).
  - Makes it easy to add schedule-related metrics, history, and future enhancements.
  - Aligns with BRD requirement for a separate schedule record and on-form schedule preview.

### ADR‑2: Money Truth Lives on Employee Advance

- **Context:** HRMS already maintains `paid_amount` and `return_amount` on Employee Advance, and Additional Salary updates `return_amount` via standard logic.
- **Decision:**
  - Keep `paid_amount` and `return_amount` as the **only** financial truth for disbursal vs repayment.
  - Schedule and child rows are **representations of the plan**, not an alternate ledger.
- **Rationale:**
  - Avoids duplicating or diverging from standard HRMS behavior.
  - Simplifies validation and reporting—remaining balance is always `paid_amount - return_amount`.

### ADR‑3: Additional Salary as the Only Payroll Integration

- **Context:** Payroll already consumes Additional Salary with `payroll_date` or recurring ranges.
- **Decision:**
  - For each due installment, create exactly **one non-recurring Additional Salary**.
  - Link it to Employee Advance via existing `ref_doctype` / `ref_docname` fields.
- **Rationale:**
  - Reuses the standard payroll pipeline; no custom hooks inside Salary Slip needed.
  - Leverages existing HRMS logic to increment/decrement `return_amount` when Additional Salary is submitted or canceled.

### ADR‑4: Non‑Recurring Additional Salary per Installment

- **Context:** We could use recurring Additional Salary, but it complicates schedule changes and partial periods.
- **Decision:**
  - Always create **non-recurring** Additional Salary for each installment due date.
  - Use `payroll_date = installment_date`.
- **Rationale:**
  - 1:1 mapping between schedule row and Additional Salary → easier to reason about.
  - Schedule changes only require generating/canceling discrete Additional Salary records.

---

## 4. DocType Designs (Tier 4)

### 4.1 Employee Advance Repayment Schedule (Parent)

- **Module:** Employee Advance Enhanced (app `eae`)
- **Naming:**
  - 1:1 with Employee Advance. Option A: name from `employee_advance`. Option B: naming series with enforced uniqueness on `employee_advance`.

- **Core Fields:**
  - `employee_advance` (Link, Employee Advance, **reqd, unique**)
  - `employee` (Link, Employee, read-only; fetched from Employee Advance)
  - `company` (Link, Company, read-only; fetched from Employee Advance)
  - `status` (Select: Draft, Active, Paused, Closed, Cancelled)
  - `schedule_type` (Select: Fixed Number of Installments, Fixed Installment Amount, Manual)
  - `repayment_frequency` (Select: Monthly, Semi-monthly, Every 3 Months)
  - `start_date` (Date) or `start_pay_period` (Link: Payroll Period) – implementer chooses one; TSD allows either.
  - `repayment_salary_component` (Link, Salary Component, **reqd**)
    - Must point to a component of `type = "Deduction"` with repayment flag (see configuration).

- **Schedule Metrics (all derived from child rows):**
  - `total_installments` (Int)
  - `paid_installments` (Int)
  - `remaining_installments` (Int)
  - `scheduled_total_amount` (Currency)
  - `scheduled_remaining_amount` (Currency)
  - `bulk_paid` (Check) – indicates closure via bulk repayment on Employee Advance, not via the schedule flow.

- **Behavior (high level):**
  - Enforce exactly **one active schedule** per Employee Advance.
  - On save/validate:
    - Derive header metrics from child rows (see 4.2).
  - When Employee Advance closes due to full repayment (see Section 6):
    - Set `status = "Closed"`.
    - Set `bulk_paid = 1`.
    - Mark all future Planned rows as `Skipped` (see 4.2).

### 4.2 Employee Advance Repayment Installment (Child)

- **Parent:** Employee Advance Repayment Schedule

- **Fields:**
  - `installment_date` (Date)
  - `installment_amount` (Currency)
  - `status` (Select: Planned, Paid, Skipped)
  - `additional_salary` (Link, Additional Salary, read-only)
  - `remarks` (Small Text)

- **Behavior:**
  - Initial schedule generation:
    - All rows created as `status = "Planned"`, `additional_salary = null`.
  - When background job creates an Additional Salary for a row:
    - Set `additional_salary = <name>`.
    - Set `status = "Paid"`.
  - When Employee Advance is closed via bulk repayment:
    - For all child rows where `status = "Planned"` and `additional_salary` is null:
      - Set `status = "Skipped"`.

---

## 5. Configuration Design (Tier 2)

### 5.1 Salary Component – Repayment Flag
NOTE: This will be added via a patch durring app installment.

Add a **Custom Field** on `Salary Component` (DocType: HRMS, not modified directly):

- **Field:** `is_employee_advance_repayment`
- **Type:** Check
- **Label:** “Is Employee Advance Repayment Component”
- **Depends On:** `doc.type == "Deduction"`

Usage rules:

- At least one Salary Component of type Deduction should be flagged as a repayment component.
- During schedule creation, the system:
  - Filters Salary Components to those with `type = "Deduction"` and `is_employee_advance_repayment = 1`.
  - If only one exists, it will be pre-selected in the dialog; user can still confirm.
  - Stores the chosen component in `repayment_salary_component` on the schedule.

### 5.2 Roles & Permissions

- **Employee Advance Repayment Schedule**
  - HR / Payroll / Finance roles: Read + Write + Create (according to project policy).
  - Employee role: No direct access to the Schedule DocType (they only use the preview on Employee Advance).

- **Employee Advance**
  - HR / Payroll / Finance: existing standard permissions.
  - Employee: read-only access to their own Employee Advances (standard ERPNext/HRMS pattern).

### 5.3 Form Layout
NOTE: This will be added via a patch durring app installment.

- Employee Advance:
  - Add a **“Repayment Schedule”** tab with:
    - Summary fields (derived; read-only).
    - HTML preview block for schedule.
    - A “Create Repayment Schedule” action (button) shown only when:
      - No existing schedule, and
      - `paid_amount > 0`, and
      - Advance in a state that allows scheduling (e.g. Submitted).
  - For employees:
    - The tab is visible but read-only.
    - No buttons or editing controls.

---

## 6. Script Designs (Tier 3)

### 6.1 Employee Advance – Server Logic

**Hook:** `on_update` (or equivalent)

- Fetch current `paid_amount` and `return_amount`.
- Compute `remaining = paid_amount - return_amount`.
- If `remaining <= 0` and advance is not already fully settled:
  - Mark Employee Advance as fully settled (use HRMS standard status logic).
  - If a schedule exists:
    - Set schedule `status = "Closed"`.
    - Set `bulk_paid = 1`.
    - Mark schedule’s future `Planned` rows (no `additional_salary`) as `Skipped`.

> Note: The actual increment/decrement of `return_amount` remains in HRMS’ `Additional Salary` logic (`update_return_amount_in_employee_advance`).

### 6.2 Repayment Schedule – Generation & Adjustment Service

**Server method:** `generate_schedule(employee_advance, params)` (in app `eae`)

- Inputs:
  - Employee Advance name.
  - `schedule_type` (fixed number / fixed amount / manual).
  - `repayment_frequency` (monthly / semi-monthly / every 3 months).
  - Starting date/period.
  - Either number of installments or installment amount.
  - Repayment Salary Component.
- Process:
  - Read Employee Advance’s `paid_amount` and `return_amount`.
  - Compute `remain_for_schedule = max(paid_amount - return_amount, 0)`.
  - Generate a set of installment rows (date + amount) such that:
    - Sum(amount) ≤ `remain_for_schedule`.
    - Final installment is adjusted to cover any rounding residue.
  - Do **not** save immediately when called in “preview” mode (see 7.2).
  - When user confirms, create or update the schedule document and its child rows:
    - Past rows untouched; future rows (`status = Planned`) replaced according to new parameters.

### 6.3 Background Job – Additional Salary Creation

**Scheduled job:** `process_due_advance_installments()`

- Frequency: Daily (or per payroll frequency; daily is safe and simple).
- Steps:
  1. Query all active schedules:
     - `status = "Active"`
     - `bulk_paid = 0`
  2. Join their child rows where:
     - `status = "Planned"`
     - `installment_date <= today`
     - `additional_salary IS NULL`
  3. For each schedule, ensure `repayment_salary_component` is set.
  4. For each due child row:
     - Create a non-recurring `Additional Salary`:
       - `employee = schedule.employee`
       - `company = schedule.company`
       - `salary_component = schedule.repayment_salary_component`
       - `amount = installment_amount`
       - `is_recurring = 0`
       - `payroll_date = installment_date`
       - `ref_doctype = "Employee Advance"`
       - `ref_docname = employee_advance`
     - Submit the Additional Salary.
       - HRMS will automatically update `return_amount` on Employee Advance.
     - Update child row:
       - `additional_salary = <created name>`
       - `status = "Paid"`.
  5. After processing, recompute schedule header metrics.
- Safeguards:
  - Before creating, check that the row still has `additional_salary` empty.
  - Optionally, double-check that no existing Additional Salary exists with:
    - Same employee, same component, same payroll_date, same ref_doctype/ref_docname.

### 6.4 Schedule Metrics Recalculation

**Hook on schedule:** `validate` / `before_save`

- For each schedule:
  - `total_installments` = count of all child rows.
  - `paid_installments` = count where `status = "Paid"`.
  - `remaining_installments` = count where `status = "Planned"`.
  - `scheduled_total_amount` = sum of `installment_amount` for all rows.
  - `scheduled_remaining_amount` = sum of `installment_amount` for rows not `Paid` or `Skipped`.

---

## 7. UX Design (Frappe Native)

### 7.1 Employee Advance – “Repayment Schedule” Tab

- **Summary card** (top of tab; HTML using Frappe theme classes):
  - Remaining Balance: `paid_amount - return_amount`
  - Schedule Status (with badge coloring)
  - Total / Paid / Remaining installments
  - Scheduled Remaining Amount

- **Schedule preview table**:
  - Rendered via an HTML field, populated by a server method:
    - Columns: Installment Date, Amount, Status (badge), Additional Salary (link), Remarks.
  - Uses compact, readable styling—not bare HTML skeleton.

- **Actions:**
  - When **no schedule** and `paid_amount > 0`:
    - Show `Create Repayment Schedule` button (HR/Payroll only).
  - When schedule exists:
    - Show `Open Schedule` button (HR/Payroll).
  - For employees:
    - Summary + table only; all actions hidden.

### 7.2 “Create Repayment Schedule” Dialog

- Implemented via `frappe.ui.Dialog` in a client script on Employee Advance.
- Fields:
  - `Schedule Type` (Fixed Number / Fixed Amount / Manual)
  - `Repayment Frequency` (Monthly / Semi-Monthly / Every 3 Months)
  - `Start Date` / `Start Payroll Period`
  - `Repayment Salary Component` (Link Salary Component)
    - Filtered: `type = "Deduction"` and `is_employee_advance_repayment = 1`.
    - If only one exists → pre-selected.
  - Depending on schedule type:
    - Fixed Number: `Number of Installments`
    - Fixed Amount: `Installment Amount`

- Flow:
  1. User fills fields.
  2. User clicks `Preview Schedule`:
     - Calls `generate_schedule(..., preview=True)` to compute rows without saving.
     - Renders a child-table-like preview inside the dialog:
       - date, amount, status = Planned.
  3. User clicks `Create Schedule`:
     - Calls `generate_schedule(..., preview=False)`:
       - Creates/updates the schedule + child rows.
     - Reloads Employee Advance; “Repayment Schedule” tab now shows summary and preview.

### 7.3 Schedule Form

- Standard Frappe form:
  - Header shows employee, company, employee advance, status, schedule type, frequency, repayment component, and metrics.
  - Child table lists installments (date, amount, status, additional_salary, remarks).
- No buttons for Additional Salary creation:
  - All Additional Salary documents are created by the background job.
  - Users can click the `additional_salary` link to inspect/cancel a specific deduction using standard UI.

---

## 8. Performance Considerations

- **Efficient queries:**
  - Add indexes on:
    - Schedule: `employee_advance`, `status`, `bulk_paid`.
    - Installment child: `parent`, `installment_date`, `status`, `additional_salary`.
  - Use these fields in WHERE clauses when selecting due installments.

- **Batch processing:**
  - Background job should process installments in batches and commit periodically (e.g. after every 50–100 Additional Salary creates) to avoid long transactions.

- **Idempotent behavior:**
  - Guard against duplicate Additional Salary creation:
    - Check `additional_salary` is null for the row.
    - Optionally ensure no existing Additional Salary exists with the same employee, component, payroll_date and reference.

---

## 9. Upgrade Safety

- **Standard HRMS preserved:**
  - Additional Salary and Salary Component behavior remain unchanged.
  - Employee Advance’s `paid_amount` and `return_amount` remain the only financial truth; we only react to them.

- **Isolation in custom app:**
  - New DocTypes live in `eae`.
  - Hooks and jobs are registered via `eae`’s `hooks.py`, not via modifications to HRMS core.

- **Config-driven, not hardcoded:**
  - Repayment Salary Component is selected via a checkbox and dialog selection, not by name or ID.

- **Minimal coupling:**
  - The only assumption on HRMS internals is that Additional Salary:
    - updates `return_amount` when `ref_doctype == "Employee Advance"`, and
    - is pulled into Salary Slip based on `payroll_date` and standard logic.
  - Any future HRMS upgrades that change this behavior can be checked against this TSD.

---

## 10. Implementation Notes & Next Steps

- Implementation should follow this order:
  1. Add Salary Component custom field (`is_employee_advance_repayment`) and configure a repayment component.
  2. Create `Employee Advance Repayment Schedule` + child DocTypes.
  3. Add Employee Advance client script for:
     - “Repayment Schedule” tab preview.
     - “Create Repayment Schedule” dialog + preview.
  4. Implement schedule generation service and metrics recalculation.
  5. Implement Employee Advance server logic to react to `return_amount` and close schedule on full repayment.
  6. Implement background job to create Additional Salary from due installments.
  7. Validate behavior against typical HRMS payroll flows (including cancellation and bulk repayment).

- Once this TSD is approved, it can be handed to the **Planner** to create a dependency-aware implementation plan (phases, user configuration tasks vs developer tasks).

