from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import frappe
from frappe.query_builder import DocType
from frappe.utils import flt, today


def process_due_advance_installments() -> None:
    """
    Create Additional Salary records for due Planned installments.

    TSD section 6.3 behavior:
    - Find active schedules (status = "Active", bulk_paid = 0).
    - For each Planned row with installment_date <= today and no Additional Salary:
      - Create a non-recurring Additional Salary document.
      - Link it back to the installment and mark status = "Paid".
    """
    schedule_doctype = DocType("Employee Advance Repayment Schedule")
    installment_doctype = DocType("Employee Advance Repayment Installment")

    query = (
        frappe.qb.from_(installment_doctype)
        .inner_join(schedule_doctype)
        .on(installment_doctype.parent == schedule_doctype.name)
        .select(
            installment_doctype.name.as_("installment_name"),
            installment_doctype.installment_date,
            installment_doctype.installment_amount,
            schedule_doctype.name.as_("schedule_name"),
            schedule_doctype.employee,
            schedule_doctype.company,
            schedule_doctype.employee_advance,
            schedule_doctype.repayment_salary_component,
        )
        .where(
            (schedule_doctype.status == "Active")
            & (schedule_doctype.bulk_paid == 0)
            & (installment_doctype.status == "Planned")
            & (installment_doctype.installment_date <= today())
            & (installment_doctype.additional_salary.isnull())
        )
        .orderby(installment_doctype.installment_date)
    )

    rows: List[Dict] = query.run(as_dict=True)  # type: ignore[assignment]

    if not rows:
        return

    rows_by_schedule: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        rows_by_schedule[row["schedule_name"]].append(row)

    for schedule_name, schedule_rows in rows_by_schedule.items():
        schedule = frappe.get_doc("Employee Advance Repayment Schedule", schedule_name)

        if not schedule.repayment_salary_component:
            frappe.logger().warning(
                "Skipping schedule %s: repayment_salary_component is not set",
                schedule.name,
            )
            continue

        for row in schedule_rows:
            installment_doc = _get_installment_row(schedule, row["installment_name"])
            if not installment_doc:
                continue

            if installment_doc.additional_salary:
                # Already processed for this row.
                continue

            additional_salary_name = _find_existing_additional_salary(row)
            if not additional_salary_name:
                additional_salary_name = _create_additional_salary_for_installment(row)

            if not additional_salary_name:
                # Creation failed or was skipped due to validation; move on.
                continue

            installment_doc.additional_salary = additional_salary_name
            installment_doc.status = "Paid"

        # Saving the schedule will also recalculate metrics via validate.
        schedule.save(ignore_permissions=True)


def _get_installment_row(schedule, installment_name: str):
    """Return the child row object for the given installment name."""
    for row in schedule.employee_advance_repayment_installment or []:
        if row.name == installment_name:
            return row
    return None


def _find_existing_additional_salary(row: Dict) -> str | None:
    """
    Optionally guard against duplicate Additional Salary creation.

    Checks for an Additional Salary with the same:
    - employee
    - company
    - salary_component
    - payroll_date
    - ref_doctype = "Employee Advance"
    - ref_docname = employee_advance
    """
    return frappe.db.exists(
        "Additional Salary",
        {
            "employee": row["employee"],
            "company": row["company"],
            "salary_component": row["repayment_salary_component"],
            "payroll_date": row["installment_date"],
            "ref_doctype": "Employee Advance",
            "ref_docname": row["employee_advance"],
        },
    )


def _create_additional_salary_for_installment(row: Dict) -> str | None:
    """Create and submit a non-recurring Additional Salary for a due installment."""
    try:
        additional_salary = frappe.new_doc("Additional Salary")
        additional_salary.employee = row["employee"]
        additional_salary.company = row["company"]
        additional_salary.salary_component = row["repayment_salary_component"]
        additional_salary.amount = flt(row["installment_amount"])
        additional_salary.is_recurring = 0
        additional_salary.payroll_date = row["installment_date"]
        additional_salary.ref_doctype = "Employee Advance"
        additional_salary.ref_docname = row["employee_advance"]

        additional_salary.insert(ignore_permissions=True)
        additional_salary.submit()
        return additional_salary.name
    except Exception:
        frappe.logger().exception(
            "Failed to create Additional Salary for Employee Advance %s on %s",
            row["employee_advance"],
            row["installment_date"],
        )
        return None

