frappe.pages['crm-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'CRM Dashboard',
		single_column: true
	});

	frappe.ccc = new frappe.CallCenterConsole(wrapper);

	if (frappe.get_route()[1]) {
		page.wrapper.find('.txt-lookup').val(frappe.get_route()[1]);
		frappe.ccc.get_info();
	}
}

frappe.pages['crm-dashboard'].refresh = function(wrapper) {
	if (frappe.ccc && frappe.get_route()[1]) {
		var comm_details = {
			"communication_phone_no":frappe.get_route()[1],
			"communication_name":frappe.get_route()[2],
			"communication_exophone":frappe.get_route()[3],
			"communication_reference_doctype":frappe.get_route()[4],
			"communication_reference_name":frappe.get_route()[5]
		}

		wrapper.page.wrapper.find('.txt-lookup').val(comm_details.communication_phone_no);
		frappe.ccc.get_info(comm_details);
	}
}

frappe.CallCenterConsole = Class.extend({
	init: function(wrapper) {
		this.page = wrapper.page;
		this.make();
		this.setup_realtime();
	},
	make: function() {
		var me = this;
		// opts = {"doctype":"Issue"};

		var input_html = '<div class="jumbotron"><div class="input-group"><input type="text" class="form-control txt-lookup" placeholder="Search for caller number..." autofocus> <span class="input-group-btn"> <button id="btn-lookup" class="btn btn-primary" type="button">Search!</button> </span> </div> </div><div class="clearfix"></div>'
		me.page.main.append(input_html);

		// contact lookup
		me.page.main.on("click", "button[id='btn-lookup']", function() {
			me.get_info();
		});
		me.page.main.on("keypress", ".txt-lookup", function(ev) {
			var keycode = (ev.keyCode ? ev.keyCode : ev.which);
			if (keycode == '13') {
				me.get_info();
			}
		});

		// Issue lookup
		me.page.main.on("click", "button[id='btn-issue-lookup']", function() {
			me.get_issue_list();
		});
		me.page.main.on("keypress", ".issue-lookup", function(ev) {
			var keycode = (ev.keyCode ? ev.keyCode : ev.which);
			if (keycode == '13') {
				me.get_issue_list();
			}
		});
	
		// new frappe.views.ListView({
		// 	doctype: "Issue",
		// 	parent: me,
		// });
	},
	get_info: function(comm_details) {
		var me = this;
		if(comm_details){
			me.page.wrapper.find('.txt-lookup').val(comm_details.communication_phone_no);
		}

		var text = me.page.main.find(".txt-lookup");
		if (text.val() && !isNaN(text.val())) {
			frappe.call({
				method: "erpnext.crm.doctype.crm_settings.crm_settings.get_caller_info",
				args: { "caller_no": text.val().trim() },
				callback: function(r){
					if(r) {
						var resp = r.message;
						me.page.main.find("#cc_console").remove("#cc_console");
						console.log("R",r.message);

						content = frappe.render_template('telephony_console', {"info": r.message});
						me.page.main.append(content);

						if (r.message.title == "Lead") {
							me.page.main.find("#callback").on("click", function() {
								me.make_a_call(comm_details,resp);
							});

							me.page.main.find("#lead_to_customer").on("click", function() {
								// me.create_customer(r.message);
							});

							// lead creation and re-route buttom for linked issue							
							me.page.main.find("#lead_issue").on("click", function() {
								me.create_issue(comm_details,resp);
							});
							me.page.main.find("#linked_issue").on("click", function() {
								frappe.set_route("Form", "Issue", me.page.main.find("#linked_issue")[0].innerHTML);
							});

							// link communication to an existing Issue
							me.page.main.find(".link_communication").on("click", function() {
								me.link_communication_to_issue(comm_details,this.id);
							});
						} else if(r.message.title == "Customer") {
							me.page.main.find("#callback").on("click", function() {
								me.make_call(comm_details,resp);
							});

							// lead creation and re-route button for linked issue							
							me.page.main.find("#customer_issue").on("click", function() {
								me.create_issue(comm_details,resp);
							});
						} else {
							me.page.main.find("#callback").on("click", function() {
								me.make_call(comm_details,resp);
							});
							
							// lead creation and re-route buttom for linked lead
							me.page.main.find("#new_lead").on("click", function() {
								name_details = me.get_basic_details(comm_details,resp);
							});
							me.page.main.find("#linked_lead").on("click", function() {
								frappe.set_route("Form", "Lead", me.page.main.find("#linked_lead")[0].innerHTML);
							});

							// lead creation and re-route buttom for linked customer
							me.page.main.find("#new_customer").on("click", function() {
								// me.create_customer(r.message);
							});

							// lead creation and re-route buttom for linked issue							
							me.page.main.find("#new_caller_issue").on("click", function() {
								me.create_issue(comm_details,resp);
							});
							me.page.main.find("#linked_issue").on("click", function() {
								frappe.set_route("Form", "Issue", me.page.main.find("#linked_issue")[0].innerHTML);
							});

							// link communication to an existing Issue
							me.page.main.find(".link_communication").on("click", function() {
								me.link_communication_to_issue(comm_details,this.id);
							});
						}
					}
				}
			});
		} else {
			frappe.show_alert("Please enter a valid number");
		}
	},

	get_issue_list: function(){
		var me = this;
		frappe.call({
			method: "erpnext.crm.doctype.crm_settings.crm_settings.get_issue_list",
			args: {
				"args": me.page.main.find(".issue-lookup").val(),
			},
			freeze: true,
			freeze_message: __("Fetching Issue.."),
			callback: function(r) {
				console.log("IL",r);
				me.page.main.find("#issue-list").remove("#issue-list");
				for(i=0;i<=issue_list.length-1;i++){
					me.page.main.find("#issue-list")='<li class="list-group-item"><div class="row"><div class="col-xs-12"><a href="/desk#Form/Issue/{{ issue_list[i].name }}">{{ issue_list[i].subject }}</a><button id="{{ issue_list[i].name }}" class="btn btn-xs link_communication pull-right"><i class="fa fa-link" aria-hidden="true"></i></button></div></div></li>'
				}
			}
		});
	},

	setup_realtime: function(){
		var me = this;
		frappe.realtime.on('new_call', (comm_details) => {
			if(frappe.get_route()[0] == 'crm-dashboard') {
				console.log("comm",comm_details);
				me.get_info(comm_details);
			} else {
				frappe.utils.notify(__("Incoming call"));
			}
		});
	},
	get_basic_details:function(comm_details,resp){
		var me = this;
		var d = new frappe.ui.Dialog({
			title: __('Basic Details'),
			fields: [
				{
					"label": "First Name",
					"fieldname": "first_name",
					"fieldtype": "Data",
					"reqd": 1
				},
				{
					"label": "Last Name",
					"fieldname": "last_name",
					"fieldtype": "Data",
					"reqd": 1
				}				
			],
			primary_action: function() {
				var name_details = d.get_values();
				me.create_lead(comm_details,name_details,resp);
				d.hide()
			},
			primary_action_label: __('Save')
		});
		d.show();
	},

	make_call: function(comm_details,resp){
		if(!comm_details){
			console.log("Minor change is to be done");
			// frappe.set_re_route('Form', doctype);
		}
		frappe.call({
			method: "erpnext.erpnext_integrations.doctype.exotel_settings.exotel_settings.handle_outgoing_call",
			args: {
				"To": comm_details.communication_phone_no || resp.number,
				"CallerId": comm_details.communication_exophone,
				"reference_doctype": comm_details.communication_reference_doctype,
				"reference_name": comm_details.communication_reference_name
			},
			freeze: true,
			freeze_message: __("Calling.."),
			callback: function(r) {
				frappe.msgprint(__("Call Connected"))
				console.log("Outbound calls communication",r);
			}
		});
	},

	create_lead: function(comm_details,name_details,resp) {
		var me = this;
		if(!comm_details){
			var new_lead = frappe.model.make_new_doc_and_get_name('Lead');
			new_lead = locals["Lead"][new_lead];
			new_lead.organization_lead = 1;
			// new_lead.phone = resp.number;
			// new_lead.contact_number = resp.number;
			new_lead.lead_name = new_lead.company_name = name_details.first_name + " " + name_details.last_name;
			new_lead.status = "Lead";
			
			frappe.set_route("Form", "Lead", new_lead.name);
		}
		else{
			frappe.call({
				method: "frappe.email.inbox.make_lead_from_communication",
				args: {
					"communication": comm_details.communication_name
				},
				freeze: true,
				freeze_message: __("Making Lead.."),
				callback: function(r) {
					console.log("Lead made",r);
					me.page.main.find("#new_lead").addClass("hidden");
					me.page.main.find("#linked_lead").removeClass("hidden");
					me.page.main.find("#linked_lead")[0].innerHTML = r.message;
					console.log("ND",name_details);
					args = {
						"first_name": name_details.first_name,
						"last_name": name_details.last_name,
						"lead_docname": r.message,
						"mobile_no": me.page.main.find(".txt-lookup").val().trim()
					}
					me.update_lead_and_make_contact(args);
				}
			});
		}	
	},

	update_lead_and_make_contact: function(args) {
		frappe.call({
			method: "erpnext.crm.doctype.crm_settings.crm_settings.update_lead_and_make_contact",
			args: {
				"args": args
			},
			freeze: true,
			freeze_message: __("Making Contact.."),
			callback: function(r) {
				frappe.msgprint(__("Contact and Lead created."))
			}
		});
	},

	// create_customer: function(resp) {
	// 	var new_customer = frappe.model.make_new_doc_and_get_name('Customer');
	// 	new_customer = locals["Customer"][new_customer];
	// 	new_customer.customer_name = resp.name;
	// 	// new_customer.lead_name = resp.number;
		
	// 	frappe.set_route("Form", "Customer", new_customer.name);
	// },

	create_issue: function(comm_details,resp) {
		var me =this;
		if(!comm_details){
			var new_issue = frappe.model.make_new_doc_and_get_name('Issue');
			new_issue = locals["Issue"][new_issue];

			if (resp.title == "Customer") {
				console.log("Setting customer", resp.customer);
				new_issue.subject = resp.name;
				new_issue.customer = resp.customer;
			} else if (resp.title == "Lead") {
				new_issue.subject = resp.name;
				new_issue.lead = resp.name;
			} else {
				new_issue.subject = resp.title + "-" + resp.number;
			}

			frappe.set_route("Form", "Issue", new_issue.name);
		}
		else{
			frappe.call({
				method: "frappe.email.inbox.make_issue_from_communication",
				args: {
					"communication": comm_details.communication_name
				},
				freeze: true,
				freeze_message: __("Making Issue.."),
				callback: function(r) {
					console.log("Issue created",r);
					me.page.main.find("#new_caller_issue").addClass("hidden");
					me.page.main.find("#lead_issue").addClass("hidden");
					me.page.main.find("#linked_issue").removeClass("hidden");
					me.page.main.find("#linked_issue")[0].innerHTML = r.message;
				}
			});
		}	
	},

	link_communication_to_issue(comm_details,issue_name){
		frappe.call({
			method: "erpnext.crm.doctype.crm_settings.crm_settings.link_communication_to_issue",
			args: {
				"comm_details": comm_details || "",
				"issue_name": issue_name
			},
			freeze: true,
			freeze_message: __("Linking communication.."),
			callback: function(r) {
				console.log("LINK STATUS",r);
			}
		});
	}
});