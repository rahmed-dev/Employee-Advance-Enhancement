frappe.ui.form.on("Employee Advance", {
	refresh(frm) {
		if (!frm.doc || frm.is_new()) {
			return;
		}

		load_repayment_schedule_preview(frm);
		setup_repayment_schedule_buttons(frm);
	},
});

function load_repayment_schedule_preview(frm) {
	frappe.call({
		method: "eae.employee_advance_enhanced.employee_advance_preview.get_repayment_schedule_preview",
		args: {
			employee_advance: frm.doc.name,
		},
		callback: function (r) {
			if (!r.message) {
				return;
			}

			const html = r.message.html || "";
			const field = frm.get_field("custom_repayment_schedule_preview");
			if (field && field.$wrapper) {
				field.$wrapper.html(html);
			}

			frm.repayment_schedule_name = r.message.schedule_name || null;
			setup_repayment_schedule_buttons(frm);
		},
	});
}

function setup_repayment_schedule_buttons(frm) {
	// Remove only our own custom buttons so standard HRMS buttons remain intact.
	if (frm.remove_custom_button) {
		frm.remove_custom_button(__("Create Repayment Schedule"), __("Repayment Schedule"));
		frm.remove_custom_button(__("Open Repayment Schedule"), __("Repayment Schedule"));
	}

	if (!frm.doc || !frm.doc.name || frm.doc.docstatus !== 1) {
		return;
	}

	const has_schedule = !!frm.repayment_schedule_name;
	const has_paid_amount = parseFloat(frm.doc.paid_amount) > 0;

	if (!has_schedule && has_paid_amount) {
		frm.add_custom_button(
			__("Create Repayment Schedule"),
			() => show_create_repayment_schedule_dialog(frm),
			__("Repayment Schedule")
		);
	}

	if (has_schedule) {
		frm.add_custom_button(
			__("Open Repayment Schedule"),
			() => {
				frappe.set_route(
					"Form",
					"Employee Advance Repayment Schedule",
					frm.repayment_schedule_name
				);
			},
			__("Repayment Schedule")
		);
	}
}

function show_create_repayment_schedule_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Create Repayment Schedule"),
		fields: [
			{
				fieldname: "schedule_type",
				fieldtype: "Select",
				label: __("Schedule Type"),
				options: [
					"",
					"Fixed Number of Installments",
					"Fixed Installment Amount",
				],
				reqd: 1,
			},
			{
				fieldname: "repayment_frequency",
				fieldtype: "Select",
				label: __("Repayment Frequency"),
				options: ["", "Monthly", "Semi-monthly", "Every 3 Months"],
				reqd: 1,
			},
			{
				fieldname: "start_date",
				fieldtype: "Date",
				label: __("Start Date"),
				reqd: 1,
				default: frm.doc.posting_date,
			},
			{
				fieldname: "number_of_installments",
				fieldtype: "Int",
				label: __("Number of Installments"),
				depends_on: "eval:doc.schedule_type=='Fixed Number of Installments'",
			},
			{
				fieldname: "installment_amount",
				fieldtype: "Currency",
				label: __("Installment Amount"),
				depends_on: "eval:doc.schedule_type=='Fixed Installment Amount'",
			},
			{
				fieldname: "repayment_salary_component",
				fieldtype: "Link",
				label: __("Repayment Salary Component"),
				options: "Salary Component",
				reqd: 1,
				get_query() {
					return {
						filters: {
							type: "Deduction",
							custom_is_employee_advance_repayment: 1,
						},
					};
				},
			},
			{
				fieldname: "preview_html",
				fieldtype: "HTML",
				label: __("Preview"),
			},
		],
		primary_action_label: __("Create Schedule"),
		primary_action(values) {
			create_repayment_schedule(frm, dialog, values);
		},
	});

	dialog.set_secondary_action_label(__("Preview Schedule"));
	dialog.set_secondary_action(() => preview_repayment_schedule(frm, dialog));

	dialog.show();
}

function preview_repayment_schedule(frm, dialog) {
	const values = dialog.get_values();
	if (!values) {
		return;
	}

	frappe.call({
		method:
			"eae.employee_advance_enhanced.doctype.employee_advance_repayment_schedule.employee_advance_repayment_schedule.generate_schedule",
		args: {
			employee_advance: frm.doc.name,
			schedule_type: values.schedule_type,
			repayment_frequency: values.repayment_frequency,
			start_date: values.start_date,
			number_of_installments: values.number_of_installments,
			installment_amount: values.installment_amount,
			repayment_salary_component: values.repayment_salary_component,
			preview: 1,
		},
		callback: function (r) {
			if (!r.message) {
				return;
			}

			const preview_field = dialog.fields_dict.preview_html;
			const installments = r.message.installments || [];
			let rows = "";

			installments.forEach((row) => {
				rows += `<tr>
					<td>${frappe.datetime.str_to_user(row.installment_date)}</td>
					<td style="text-align: right;">${format_currency(
						row.installment_amount
					)}</td>
					<td>${__("Planned")}</td>
				</tr>`;
			});

			const html = `
				<div class="mt-3">
					<div class="text-muted small" style="margin-bottom: 0.5rem;">
						${__("Preview Installments")}
					</div>
					<div class="table-responsive">
						<table class="table table-bordered table-sm">
							<thead>
								<tr>
									<th style="width: 40%;">${__("Installment Date")}</th>
									<th style="width: 40%; text-align: right;">${__("Amount")}</th>
									<th>${__("Status")}</th>
								</tr>
							</thead>
							<tbody>${rows}</tbody>
						</table>
					</div>
				</div>`;

			if (preview_field && preview_field.$wrapper) {
				preview_field.$wrapper.html(html);
			}
		},
	});
}

function create_repayment_schedule(frm, dialog, values) {
	if (!values) {
		return;
	}

	frappe.call({
		method:
			"eae.employee_advance_enhanced.doctype.employee_advance_repayment_schedule.employee_advance_repayment_schedule.generate_schedule",
		args: {
			employee_advance: frm.doc.name,
			schedule_type: values.schedule_type,
			repayment_frequency: values.repayment_frequency,
			start_date: values.start_date,
			number_of_installments: values.number_of_installments,
			installment_amount: values.installment_amount,
			repayment_salary_component: values.repayment_salary_component,
			preview: 0,
		},
		callback: function (r) {
			if (!r.exc) {
				dialog.hide();
				frm.reload_doc();
			}
		},
	});
}
