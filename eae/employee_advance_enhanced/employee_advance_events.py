import frappe
from frappe.utils import flt


def on_employee_advance_update(doc, method: str | None = None) -> None:
    """
    React to Employee Advance updates and close schedules on full repayment.

    TSD section 6.1 defines the behavior:
    - Compute remaining = paid_amount - return_amount.
    - When remaining <= 0, mark the related repayment schedule as:
      status = "Closed", bulk_paid = 1.
    - Mark future Planned rows without Additional Salary as "Skipped".
    """
    paid_amount = flt(getattr(doc, "paid_amount", 0))
    return_amount = flt(getattr(doc, "return_amount", 0))
    remaining = paid_amount - return_amount

    if remaining > 0:
        return

    schedule_name = frappe.db.get_value(
        "Employee Advance Repayment Schedule",
        {"employee_advance": doc.name},
        "name",
    )

    if not schedule_name:
        return

    schedule = frappe.get_doc("Employee Advance Repayment Schedule", schedule_name)

    if schedule.status == "Closed" and schedule.bulk_paid:
        # Already processed.
        return

    schedule.status = "Closed"
    schedule.bulk_paid = 1

    for row in schedule.employee_advance_repayment_installment or []:
        if row.status == "Planned" and not row.additional_salary:
            row.status = "Skipped"

    schedule.save(ignore_permissions=True)

