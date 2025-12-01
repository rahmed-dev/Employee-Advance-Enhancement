from __future__ import annotations

"""
Dashboard extension for Employee Advance.

This is wired via the `override_doctype_dashboards` hook so that it
receives the standard HRMS Employee Advance dashboard data, then adds
our repayment schedule connection on top.
"""

from typing import Any, Dict


def get_data(data: Dict[str, Any] | None = None) -> Dict[str, Any]:
	"""
	Extend the Employee Advance dashboard to show repayment schedules.

	- Adds "Employee Advance Repayment Schedule" to the Transactions list
	  under a "Repayment" group (creates the group if needed).
	- Registers "employee_advance" as the link field used for navigation.
	"""
	if not data:
		# Fallback: load the base dashboard definition from HRMS if not provided.
		from hrms.hr.doctype.employee_advance.employee_advance_dashboard import (  # type: ignore[import]
			get_data as hrms_get_data,
		)

		data = hrms_get_data() or {}

	transactions = list(data.get("transactions") or [])
	repayment_doctype = "Employee Advance Repayment Schedule"

	# Ensure the repayment schedule appears in the Transactions groups.
	if not _transactions_contains(transactions, repayment_doctype):
		# Try to append to an existing "Repayment" group first.
		for group in transactions:
			if group.get("label") == "Repayment":
				items = group.get("items") or []
				if repayment_doctype not in items:
					items.append(repayment_doctype)
					group["items"] = items
				break
		else:
			# No existing Repayment group; create a new one.
			transactions.append({"label": "Repayment", "items": [repayment_doctype]})

	data["transactions"] = transactions

	# Register the non-standard link field so Frappe knows how to link back.
	non_standard_fieldnames = dict(data.get("non_standard_fieldnames") or {})
	if repayment_doctype not in non_standard_fieldnames:
		non_standard_fieldnames[repayment_doctype] = "employee_advance"
	data["non_standard_fieldnames"] = non_standard_fieldnames

	return data


def _transactions_contains(transactions: list[Dict[str, Any]], doctype: str) -> bool:
	for group in transactions:
		items = group.get("items") or []
		if doctype in items:
			return True
	return False

