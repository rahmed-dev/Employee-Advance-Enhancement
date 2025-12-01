from __future__ import annotations

from typing import Dict, List

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_repayment_schedule_preview(employee_advance: str) -> Dict:
    """
    Return HTML preview content for the Employee Advance repayment schedule tab.

    Includes:
    - Remaining balance
    - Schedule status and metrics (if schedule exists)
    - A compact table of installments (date, amount, status, additional salary)
    """
    if not employee_advance:
        frappe.throw("Employee Advance is required to build the schedule preview.")

    advance = frappe.get_doc("Employee Advance", employee_advance)
    remaining_balance = flt(advance.paid_amount) - flt(advance.return_amount)

    schedule_name = frappe.db.get_value(
        "Employee Advance Repayment Schedule",
        {"employee_advance": advance.name},
        "name",
    )

    schedule = None
    installments: List = []
    if schedule_name:
        schedule = frappe.get_doc("Employee Advance Repayment Schedule", schedule_name)
        installments = schedule.employee_advance_repayment_installment or []

    html = _build_preview_html(advance, remaining_balance, schedule, installments)

    return {
        "html": html,
        "schedule_name": schedule_name,
    }


def _build_preview_html(advance, remaining_balance: float, schedule, installments) -> str:
    """Compose a small HTML block for the summary card and schedule table."""
    status_label = "No Schedule"
    status_color = "gray"
    totals = {
        "total": 0,
        "paid": 0,
        "remaining": 0,
        "scheduled_total": 0.0,
        "scheduled_remaining": 0.0,
    }

    if schedule:
        status_label = schedule.status or "Draft"
        status_color = _status_color(status_label)
        totals["total"] = schedule.total_installments or 0
        totals["paid"] = schedule.paid_installments or 0
        totals["remaining"] = schedule.remaining_installments or 0
        totals["scheduled_total"] = schedule.schedule_total_amount or 0.0
        totals["scheduled_remaining"] = schedule.schedule_remaining_amount or 0.0

    summary_html = f"""
<div class="frappe-card" style="margin-bottom: 1rem;">
  <div class="frappe-card-body">
    <div class="row">
      <div class="col-sm-3">
        <div class="text-muted small">Remaining Balance</div>
        <div class="h6">{remaining_balance:.2f}</div>
      </div>
      <div class="col-sm-3">
        <div class="text-muted small">Schedule Status</div>
        <span class="indicator-pill {status_color}">{status_label}</span>
      </div>
      <div class="col-sm-3">
        <div class="text-muted small">Installments</div>
        <div class="h6">{totals["paid"]}/{totals["total"]} paid</div>
      </div>
      <div class="col-sm-3">
        <div class="text-muted small">Scheduled Remaining</div>
        <div class="h6">{totals["scheduled_remaining"]:.2f}</div>
      </div>
    </div>
  </div>
</div>
"""

    table_html = _build_installments_table(installments)

    return summary_html + table_html


def _build_installments_table(installments) -> str:
    if not installments:
        return """
<div class="text-muted">
  No repayment schedule exists for this Employee Advance yet.
</div>
"""

    rows = []
    for row in installments:
        badge_class = _status_color(row.status)
        additional_salary = row.additional_salary or ""
        rows.append(
            f"""
<tr>
  <td>{frappe.format(row.installment_date, {"fieldtype": "Date"})}</td>
  <td style="text-align: right;">{flt(row.installment_amount):.2f}</td>
  <td><span class="indicator-pill {badge_class}">{row.status}</span></td>
  <td>{additional_salary}</td>
  <td>{frappe.utils.escape_html(row.remarks or "")}</td>
</tr>
"""
        )

    return f"""
<div class="mt-3">
  <div class="text-muted small" style="margin-bottom: 0.5rem;">Repayment Schedule</div>
  <div class="table-responsive">
    <table class="table table-bordered table-sm">
      <thead>
        <tr>
          <th style="width: 20%;">Installment Date</th>
          <th style="width: 20%; text-align: right;">Amount</th>
          <th style="width: 15%;">Status</th>
          <th style="width: 20%;">Additional Salary</th>
          <th>Remarks</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
</div>
"""


def _status_color(status: str) -> str:
    """Map logical status to a standard indicator color class."""
    status = (status or "").lower()
    if status in ("active", "paid"):
        return "green"
    if status in ("draft", "planned"):
        return "blue"
    if status in ("paused", "skipped"):
        return "orange"
    if status in ("closed", "cancelled", "canceled"):
        return "red"
    return "gray"

