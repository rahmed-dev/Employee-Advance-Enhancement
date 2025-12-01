# Employee Advance Enhanced – Module Layout

This package contains all implementation code for the **Employee Advance Enhanced**
feature as defined in:

- `apps/eae/docs/Employee Advance Enhanced-tsd.md`

## DocType Controllers

- `doctype/employee_advance_repayment_schedule/employee_advance_repayment_schedule.py`  
  - DocType class and schedule metrics recalculation.  
  - Whitelisted `generate_schedule(...)` for creating/updating schedules.

- `doctype/employee_advance_repayment_installment/employee_advance_repayment_installment.py`  
  - Child table DocType; no extra logic yet.

## Employee Advance Integration

- `employee_advance_events.py`  
  - Hooked via `hooks.py` on `Employee Advance.on_update`.  
  - Closes schedules and marks future installments as Skipped on full repayment.

- `employee_advance_preview.py`  
  - Whitelisted `get_repayment_schedule_preview(...)` used by the
    `repayment_schedule_preview` HTML field and client script.

- `public/js/employee_advance.js`  
  - Client script for Employee Advance:  
    - Loads preview HTML.  
    - Shows "Create/Open Repayment Schedule" buttons.  
    - Implements the schedule creation dialog and preview.

## Background Jobs

- `repayment_schedule_jobs.py`  
  - `process_due_advance_installments()` scheduled daily via `scheduler_events`.  
  - Creates Additional Salary records for due installments and updates rows to Paid.

## Dashboards & Connections

- Dashboard connection from Employee Advance → Employee Advance Repayment Schedule is
  added via the dashboard extension:
  - `employee_advance_dashboard.py` (hooked via `override_doctype_dashboards` in `hooks.py`)
