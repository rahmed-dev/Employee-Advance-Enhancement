app_name = "eae"
app_title = "Employee Advance Enhanced"
app_publisher = "https://github.com/rahmed-dev"
app_description = "Enhancement to Frappe HRMS Employee Advance. That makes return on employee advance easier."
app_email = "rizwanazmat2000+eae@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "eae",
# 		"logo": "/assets/eae/logo.png",
# 		"title": "Employee Advance Enhanced",
# 		"route": "/eae",
# 		"has_permission": "eae.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/eae/css/eae.css"
# app_include_js = "/assets/eae/js/eae.js"

# include js, css files in header of web template
# web_include_css = "/assets/eae/css/eae.css"
# web_include_js = "/assets/eae/js/eae.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "eae/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "eae/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "eae.utils.jinja_methods",
# 	"filters": "eae.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "eae.install.before_install"
# after_install = "eae.install.after_install"

# Uninstallation
# ------------

# after_uninstall = "eae.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "eae.utils.before_app_install"
# after_app_install = "eae.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "eae.utils.before_app_uninstall"
# after_app_uninstall = "eae.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "eae.notifications.get_notification_config"

override_doctype_dashboards = {
	"Employee Advance": [
		"eae.employee_advance_enhanced.employee_advance_dashboard.get_data"
	]
}

# Document Events
# ---------------
doc_events = {
	"Employee Advance": {
		"on_update": "eae.employee_advance_enhanced.employee_advance_events.on_employee_advance_update"
	}
}

# Scheduled Tasks
# ---------------
scheduler_events = {
	"daily": [
		"eae.employee_advance_enhanced.repayment_schedule_jobs.process_due_advance_installments"
	]
}

# Testing
# -------

# before_tests = "eae.install.before_tests"

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]
# Request Events
# ----------------
# before_request = ["eae.utils.before_request"]
# after_request = ["eae.utils.after_request"]

# Job Events
# ----------
# before_job = ["eae.utils.before_job"]
# after_job = ["eae.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"eae.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Doctype JS
# ----------
doctype_js = {
	"Employee Advance": "public/js/employee_advance.js",
}

# Fixtures
# --------
# Export only Custom Fields belonging to this app's module so that
# our Employee Advance / Salary Component customizations travel with
# the app without pulling in unrelated fields.
fixtures = [
	{
		"doctype": "Custom Field",
		"filters": [["module", "=", "Employee Advance Enhanced"]],
	},
]
