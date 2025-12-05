# Copyright (c) 2025, https://github.com/rahmed-dev and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, flt, getdate


class EmployeeAdvanceRepaymentSchedule(Document):
	def validate(self) -> None:
		"""
		Keep schedule metrics in sync with child installments.

		All header metrics are derived from the child table so that the
		Employee Advance summary and background job can rely on them.
		"""
		self.update_schedule_metrics()

	def update_schedule_metrics(self) -> None:
		"""Recalculate totals and remaining amounts from child rows."""
		rows = self.employee_advance_repayment_installment or []

		total_installments = len(rows)
		paid_installments = len([row for row in rows if row.status == "Paid"])
		remaining_installments = len([row for row in rows if row.status == "Planned"])

		schedule_total_amount = sum(flt(row.installment_amount) for row in rows)
		schedule_remaining_amount = sum(
			flt(row.installment_amount)
			for row in rows
			if row.status not in ("Paid", "Skipped")
		)

		self.total_installments = total_installments
		self.paid_installments = paid_installments
		self.remaining_installments = remaining_installments
		self.schedule_total_amount = schedule_total_amount
		self.schedule_remaining_amount = schedule_remaining_amount


@frappe.whitelist()
def generate_schedule(
	employee_advance: str,
	schedule_type: str,
	repayment_frequency: str,
	start_date: str | None = None,
	number_of_installments: int | str | None = None,
	installment_amount: float | str | None = None,
	repayment_salary_component: str | None = None,
	preview: int | str | None = 0,
) -> dict:
	"""
	Generate or update a repayment schedule for a given Employee Advance.

	This implements the behavior described in section 6.2 of the TSD:

	- Reads paid_amount and return_amount from Employee Advance.
	- Computes remain_for_schedule = max(paid_amount - return_amount, 0).
	- Builds installment rows based on schedule_type and repayment_frequency.
	- In preview mode, returns rows without saving.
	- In confirm mode, creates/updates the Employee Advance Repayment Schedule:
	  - Past rows are preserved.
	  - Future Planned rows are replaced with the new pattern.
	"""
	if not employee_advance:
		frappe.throw(_("Employee Advance is required to generate a schedule."))

	if not schedule_type:
		frappe.throw(_("Schedule Type is required to generate a schedule."))

	if not repayment_frequency:
		frappe.throw(_("Repayment Frequency is required to generate a schedule."))

	if not start_date:
		frappe.throw(_("Start Date is required to generate a schedule."))

	is_preview = bool(int(preview)) if preview not in (None, "", 0, "0") else False

	schedule_type = schedule_type.strip()
	repayment_frequency = repayment_frequency.strip()

	advance = frappe.get_doc("Employee Advance", employee_advance)

	paid_amount = flt(advance.paid_amount)
	return_amount = flt(advance.return_amount)
	remain_for_schedule = max(paid_amount - return_amount, 0)

	if remain_for_schedule <= 0:
		frappe.throw(
			_("Employee Advance {0} has no remaining balance to schedule.").format(advance.name),
			title=_("No Remaining Balance"),
		)

	if schedule_type == "Fixed Number of Installments":
		if not number_of_installments:
			frappe.throw(_("Number of Installments is required for this schedule type."))
		try:
			number_of_installments = int(number_of_installments)
		except (TypeError, ValueError):
			frappe.throw(_("Number of Installments must be an integer."))
		if number_of_installments <= 0:
			frappe.throw(_("Number of Installments must be greater than zero."))

		base_amount = remain_for_schedule / number_of_installments
		installment_amounts = [base_amount] * number_of_installments
		# Adjust final installment for any rounding residue.
		difference = remain_for_schedule - sum(installment_amounts)
		installment_amounts[-1] += difference

	elif schedule_type == "Fixed Installment Amount":
		if not installment_amount:
			frappe.throw(_("Installment Amount is required for this schedule type."))
		try:
			installment_amount_value = flt(installment_amount)
		except (TypeError, ValueError):
			frappe.throw(_("Installment Amount must be a number."))

		if installment_amount_value <= 0:
			frappe.throw(_("Installment Amount must be greater than zero."))

		full_installments = int(remain_for_schedule // installment_amount_value)
		installment_amounts = [installment_amount_value] * max(full_installments, 0)
		remainder = remain_for_schedule - (full_installments * installment_amount_value)
		# Always add a final installment when there is a positive remainder.
		if remainder > 0:
			installment_amounts.append(remainder)

		if not installment_amounts:
			# Remaining amount is smaller than the requested installment;
			# create a single installment for the remaining amount.
			installment_amounts = [remain_for_schedule]

	else:
		frappe.throw(_("Unsupported schedule type: {0}").format(schedule_type))

	start = getdate(start_date)
	installments = []

	for index, amount in enumerate(installment_amounts):
		if repayment_frequency in ("Monthly",):
			installment_date = add_months(start, index)
		elif repayment_frequency in ("Semi-monthly", "Semi-Monthly", "Semi Monthly"):
			# Approximate semi-monthly behavior as every 15 days.
			installment_date = add_days(start, index * 15)
		elif repayment_frequency in ("Every 3 Months", "Quarterly"):
			installment_date = add_months(start, index * 3)
		else:
			frappe.throw(_("Unsupported repayment frequency: {0}").format(repayment_frequency))

		installments.append(
			{
				"installment_date": installment_date,
				"installment_amount": flt(amount),
				"status": "Planned",
				"additional_salary": None,
				"remarks": None,
			}
		)

	if is_preview:
		return {
			"preview": True,
			"employee_advance": advance.name,
			"remain_for_schedule": remain_for_schedule,
			"installments": installments,
		}

	if not repayment_salary_component:
		frappe.throw(_("Repayment Salary Component is required to create a schedule."))

	component_type, is_repayment_component = frappe.db.get_value(
		"Salary Component",
		repayment_salary_component,
		["type", "custom_is_employee_advance_repayment"],
	)
	if component_type != "Deduction" or not is_repayment_component:
		frappe.throw(
			_(
				'Repayment Salary Component must be a Deduction component with '
				'"Is Employee Advance Repayment Component" enabled.'
			)
		)

	existing_schedules = frappe.db.get_all(
		"Employee Advance Repayment Schedule",
		filters={"employee_advance": advance.name},
		pluck="name",
	)

	if len(existing_schedules) > 1:
		frappe.throw(
			_(
				"Multiple Employee Advance Repayment Schedules exist for this Employee Advance. "
				"Please keep only one schedule record."
			)
		)

	schedule_name = existing_schedules[0] if existing_schedules else None

	if schedule_name:
		schedule = frappe.get_doc("Employee Advance Repayment Schedule", schedule_name)
	else:
		schedule = frappe.new_doc("Employee Advance Repayment Schedule")
		schedule.employee_advance = advance.name
		schedule.employee = advance.employee
		schedule.company = advance.company

	schedule.schedule_type = schedule_type
	schedule.repayment_frequency = repayment_frequency
	schedule.start_date = start
	schedule.repayment_salary_component = repayment_salary_component

	# Preserve non-Planned rows; replace all Planned rows with the new pattern.
	existing_rows = list(schedule.employee_advance_repayment_installment or [])
	schedule.set("employee_advance_repayment_installment", [])

	for row in existing_rows:
		if row.status != "Planned" or row.additional_salary:
			schedule.append(
				"employee_advance_repayment_installment",
				{
					"installment_date": row.installment_date,
					"installment_amount": row.installment_amount,
					"status": row.status,
					"additional_salary": row.additional_salary,
					"remarks": row.remarks,
				},
			)

	for installment in installments:
		schedule.append("employee_advance_repayment_installment", installment)

	# Status remains under user control; default to Active when there are
	# Planned installments and the document is submitted.
	if not schedule.status:
		schedule.status = "Draft"

	if schedule.is_new():
		schedule.insert()
	else:
		schedule.save()

	if schedule.docstatus == 0:
		# Submit newly created schedules so that they behave as an active plan.
		schedule.status = "Active"
		schedule.submit()

	return {
		"preview": False,
		"schedule": schedule.name,
		"employee_advance": advance.name,
		"remain_for_schedule": remain_for_schedule,
	}
