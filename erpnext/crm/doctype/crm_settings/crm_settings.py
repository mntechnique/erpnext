# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe,json
from frappe import msgprint, _
from frappe.model.document import Document

class CRMSettings(Document):
	pass

def make_popup(caller_no, comm_details):
	contact_lookup = frappe.get_list("Contact", or_filters={"phone":caller_no, "mobile_no":caller_no}, ignore_permissions=True)

	if len(contact_lookup) > 0:
		contact_doc = frappe.get_doc("Contact", contact_lookup[0].get("name"))

		if(contact_doc.get_link_for('Customer')):
			customer_name = frappe.db.get_value("Dynamic Link", {"parent":contact_doc.get("name")}, "link_name")
			customer_full_name = frappe.db.get_value("Customer", customer_name, "customer_name")
			popup_data = {
				"title": "Customer",
				"number": caller_no,
				"name": customer_full_name,
				"call_timestamp": frappe.utils.datetime.datetime.strftime(frappe.utils.datetime.datetime.today(), '%d/%m/%Y %H:%M:%S')
			}
			popup_data["route_link"] = str(comm_details.get("communication_phone_no") + "/" +
				comm_details.get("communication_name") + "/" +
				comm_details.get("communication_exophone") +  "/" +
				comm_details.get("communication_reference_doctype") + "/" +
				comm_details.get("communication_reference_name"))
			popup_html = render_popup(popup_data)
			return popup_html

		elif(contact_doc.get_link_for('Lead')):
			lead_full_name = frappe.get_doc("Lead",contact_doc.get_link_for('Lead')).lead_name
			popup_data = {
				"title": "Lead",
				"number": caller_no,
				"name": lead_full_name,
				"call_timestamp": frappe.utils.datetime.datetime.strftime(frappe.utils.datetime.datetime.today(), '%d/%m/%Y %H:%M:%S')
			}
			popup_data["route_link"] = str(comm_details.get("communication_phone_no") + "/" +
				comm_details.get("communication_name") + "/" +
				comm_details.get("communication_exophone") +  "/" +
				comm_details.get("communication_reference_doctype") + "/" +
				comm_details.get("communication_reference_name"))
			popup_html = render_popup(popup_data)
			return popup_html
		else:
			has_issues = frappe.get_list("Issue", filters = {"contact":contact_doc.get("name")}, fields=["*"], ignore_permissions=True)
			if(len(has_issues)>0):
				if(has_issues[0].customer):
					customer_full_name = frappe.db.get_value("Customer", has_issues[0].customer, "customer_name")
					popup_data = {
						"title": "Customer",
						"number": caller_no,
						"name": customer_full_name,
						"call_timestamp": frappe.utils.datetime.datetime.strftime(frappe.utils.datetime.datetime.today(), '%d/%m/%Y %H:%M:%S')
					}
				elif(has_issues[0].lead):
					lead_full_name = frappe.db.get_value("Lead", has_issues[0].lead, "lead_name")
					popup_data = {
						"title": "Lead",
						"number": caller_no,
						"name": lead_full_name,
						"call_timestamp": frappe.utils.datetime.datetime.strftime(frappe.utils.datetime.datetime.today(), '%d/%m/%Y %H:%M:%S')
					}
				else:
					popup_data = {
						"title": "Contact",
						"number": caller_no,
						"name": contact_doc.get("first_name") + contact_doc.get("last_name"),
						"call_timestamp": frappe.utils.datetime.datetime.strftime(frappe.utils.datetime.datetime.today(), '%d/%m/%Y %H:%M:%S')
					}
				popup_data["route_link"] = str(comm_details.get("communication_phone_no") + "/" +
					comm_details.get("communication_name") + "/" +
					comm_details.get("communication_exophone") +  "/" +
					comm_details.get("communication_reference_doctype") + "/" +
					comm_details.get("communication_reference_name"))
				popup_html = render_popup(popup_data)
				return popup_html
	else:
		popup_data = {
			"title": "New Caller",
			"number": caller_no,
			"name": "Unknown",
			"call_timestamp": frappe.utils.datetime.datetime.strftime(frappe.utils.datetime.datetime.today(), '%d/%m/%Y %H:%M:%S')
		}
		popup_data["route_link"] = str(comm_details.get("communication_phone_no") + "/" +
			comm_details.get("communication_name") + "/" +
			comm_details.get("communication_exophone") +  "/" +
			comm_details.get("communication_reference_doctype") + "/" +
			comm_details.get("communication_reference_name"))
		popup_html = render_popup(popup_data)
		return popup_html

def render_popup(popup_data):
	html = frappe.render_template("erpnext/public/js/integrations/call_popup.html", popup_data)
	return html

def display_popup(caller_no, comm_details):
	try:
		popup_html = make_popup(caller_no, comm_details)

		try:
			users = frappe.get_all("User", or_filters={"phone":comm_details.get("call_receiver"), "mobile_no":comm_details.get("call_receiver")}, fields=["name"])
			frappe.async.publish_realtime(event="msgprint", message=popup_html, user=users[0].name)

		except Exception as e:
			frappe.log_error(message=frappe.get_traceback(), title="Popup restriction errors")

	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title="Error in popup display")

@frappe.whitelist()
def update_lead_and_make_contact(args):
	args = json.loads(args)

	# update lead name
	lead = frappe.get_doc("Lead",args.get("lead_docname"))
	lead.lead_name = lead.company_name = args.get("first_name") + " " + args.get("last_name")
	lead.save()
	frappe.db.commit()

	# autocreate contact
	contact = frappe.get_doc({
		'doctype': 'Contact',
		'first_name': args.get("first_name"),
		'last_name': args.get("last_name"),
		'mobile_no': args.get("mobile_no"),
		'links': [{
			'link_doctype': "Lead",
			'link_name': args.get("lead_docname")
		}]
	}).insert()

	return contact

@frappe.whitelist()
def link_communication_to_issue(comm_details,issue_name):
	try:	
		if not comm_details:
			return frappe.msgprint(_("No communication available to link. Consider adding manual comments"))

		else:			
			comm_details = json.loads(comm_details)
			issue_doc = frappe.get_doc("Issue",issue_name)
			
			# update and link communication to issue
			comm = frappe.get_doc("Communication",comm_details.get("communication_name"))
			comm.reference_doctype = "Issue"
			comm.reference_name = issue_name
			comm.save(ignore_permissions=True)
			frappe.db.commit()
				
			# if (comm_details.get("communication_phone_no") != (frappe.get_doc("Contact",issue_doc.get("contact")).phone or frappe.get_doc("Contact",issue_doc.get("contact")).mobile_no)):
				# args = {
				# 		"first_name": "",
				# 		"last_name": "",
				# 		"lead_docname": issue_doc.lead,
				# 		"mobile_no": comm_details.get("communication_phone_no")
				# 	}
				# frappe.publish_realtime('basic_details_for_linking', message=args, after_commit=False)

				# # add the unknown/new contact to an already linked Lead on Issue
				# # contact = frappe.get_doc({
				# # 	'doctype': 'Contact',
				# # 	'first_name': "",
				# # 	'last_name': "",
				# # 	'mobile_no': comm_details.get("communication_phone_no"),
				# # 	'links': [{
				# # 		'link_doctype': "Lead",
				# # 		'link_name': issue_doc.lead
				# # 	}]
				# # }).insert()
				# # return contact
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title="Error in linking")		

@frappe.whitelist()
def get_caller_info(caller_no):
	# Fetches caller information from the number in the search bar
	if caller_no and len(caller_no) > 13:
		frappe.msgprint("Please enter a valid number")
		return

	contact_lookup = frappe.get_list("Contact", or_filters={"phone":caller_no, "mobile_no":caller_no}, ignore_permissions=True)

	if len(contact_lookup) > 0:
		contact_doc = frappe.get_doc("Contact", contact_lookup[0].get("name"))
		if(contact_doc.get_link_for('Customer')):
			customer_name = frappe.db.get_value("Dynamic Link", {"parent":contact_doc.get("name")}, "link_name")
			customer_full_name = frappe.db.get_value("Customer", customer_name, "customer_name")
			dashboard_data = {
				"title": "Customer",
				"number": caller_no,
				"name": customer_full_name,
				"call_timestamp": frappe.utils.datetime.datetime.strftime(frappe.utils.datetime.datetime.today(), '%d/%m/%Y %H:%M:%S')
			}

		elif(contact_doc.get_link_for('Lead')):
			lead_doc = frappe.get_doc("Lead",contact_doc.get_link_for('Lead'))
			dashboard_data = {
				"title": "Lead",
				"number": caller_no,
				"route_link":lead_doc.name,
				"name": lead_doc.lead_name or lead_doc.company_name,
				"call_timestamp": frappe.utils.datetime.datetime.strftime(frappe.utils.datetime.datetime.today(), '%d/%m/%Y %H:%M:%S')
			}

		open_issues = frappe.get_all("Issue", filters = {"contact":contact_doc.get("name")}, fields=["*"], ignore_permissions=True)
		dashboard_data["issue_list"] = open_issues
		return dashboard_data

	else:
		open_issues = frappe.get_all("Issue", filters = {"contact":caller_no}, fields=["*"], ignore_permissions=True)

		dashboard_data = {
			"title": "New Caller",
			"number": caller_no,
			"name": "Unknown",
			"call_timestamp": frappe.utils.datetime.datetime.strftime(frappe.utils.datetime.datetime.today(), '%d/%m/%Y %H:%M:%S'),
			"issue_list": open_issues			
		}
		return dashboard_data

@frappe.whitelist()
def get_issue_list(args):
	issue_list = frappe.get_all("Issue", fields=["name","subject"], filters = {"name": ("like", "%{0}%".format(args))})
	return issue_list