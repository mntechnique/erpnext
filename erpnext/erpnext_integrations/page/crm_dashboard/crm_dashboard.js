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
		wrapper.page.wrapper.find('.txt-lookup').val(frappe.get_route()[1]);
		frappe.ccc.get_info();
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
		// me.page.add_inner_button(__("Search"), function() {
		// 	console.log("Search");
		// });
		//console.log("Content", me.page)

		var input_html = '<div class="jumbotron"><div class="input-group"><input type="text" class="form-control txt-lookup" placeholder="Search for caller number..."> <span class="input-group-btn"> <button id="btn-lookup" class="btn btn-primary" type="button">Search!</button> </span> </div> </div><div class="clearfix"></div>'
		me.page.main.append(input_html);

		// var text = me.page.main.find(".txt-lookup");

		me.page.main.on("click", "button[id='btn-lookup']", function() {
			me.get_info();
		});

		me.page.main.on("keypress", ".txt-lookup", function(ev) {
			var keycode = (ev.keyCode ? ev.keyCode : ev.which);
			if (keycode == '13') {
				me.get_info();
			}
		});
	},
	get_info: function(comm_details) {
		var me = this;
		if(comm_details){
			me.page.wrapper.find('.txt-lookup').val(comm_details.communication_phone_no);
		}
		else if(frappe.get_route()[1]){
			me.page.wrapper.find('.txt-lookup').val(frappe.get_route()[1]);
		}

		var text = me.page.main.find(".txt-lookup");
		if (text.val() && !isNaN(text.val())) {
			frappe.call({
				method: "erpnext.crm.doctype.crm_settings.crm_settings.get_caller_info",
				args: { "caller_no": text.val().trim() },
				callback: function(r){
					if(r) {
						me.page.main.find("#cc_console").remove("#cc_console");
						console.log("R",r.message);

						content = frappe.render_template('telephony_console', {"info": r.message});
						me.page.main.append(content);

						if (r.message.title == "Lead") {
							me.page.main.find("#callback").on("click", function() {
								me.make_a_call(comm_details,frappe.get_route()[1]);
							});
							me.page.main.find("#lead_to_customer").on("click", function() {
								// me.create_customer(r.message);
							});
							me.page.main.find("#lead_issue").on("click", function() {
								me.create_issue(comm_details,frappe.get_route()[1]);
							});
						} else if(r.message.title == "Customer") {
							me.page.main.find("#callback").on("click", function() {
								me.make_a_call(comm_details,frappe.get_route()[1]);
							});
							me.page.main.find("#customer_issue").on("click", function() {
								me.create_issue(comm_details,frappe.get_route()[1]);
							});
						} else {
							me.page.main.find("#callback").on("click", function() {
								me.make_a_call(comm_details,frappe.get_route()[1]);
							});							
							me.page.main.find("#new_lead").on("click", function() {
								name_details = me.get_basic_details();
								me.create_lead(comm_details,frappe.get_route()[1],name_details);
							});
							me.page.main.find("#new_customer").on("click", function() {
								// me.create_customer(r.message);
							});
							me.page.main.find("#new_caller_issue").on("click", function() {
								me.create_issue(comm_details,frappe.get_route()[1]);
							});						
						}
					}
				}
			});
		} else {
			frappe.show_alert("Please enter a valid number");
		}
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
	get_basic_details:function(){
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
				var data = d.get_values();
				return data;
				d.hide()
			},
			primary_action_label: __('Save')
		});
		d.show();
	},
	make_a_call: function(comm_details,comm_name){
		if(!comm_details){
			console.log("Thamb jara")
		}
		frappe.call({
			method: "erpnext.erpnext_integrations.doctype.exotel_settings.exotel_settings.handle_outgoing_call",
			args: {
				"To": comm_details.communication_phone_no,
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

	create_lead: function(comm_details,comm_name,name_details) {
		var me = this;
		communication_docname = comm_details.communication_name || comm_name;
		frappe.call({
			method: "frappe.email.inbox.make_lead_from_communication",
			args: {
				"communication": communication_docname
			},
			freeze: true,
			freeze_message: __("Making Lead.."),
			callback: function(r) {
				console.log("Lead made",r);
				me.page.main.find("#new_lead").addClass(".hidden");
				me.page.main.find("#linked_lead").removeClass(".hidden");
				me.page.page.main.find("#new_lead")[0].innerHTML = r;
				console.log("ND",name_details);
				args = {
					first_name: name_details.first_name,
					last_name: name_details.last_name,
					lead_docname: r,
					mobile_no: me.page.main.find(".txt-lookup").val().trim()
				}
				me.update_lead_and_make_contact(args);

			}
		});
	},
	update_lead_and_make_contact: function(args) {
		frappe.call({
			method: "erpnext.crm.doctype.crm_settings.crm_settings.update_lead_and_make_contact",
			args: {
				"args": args
			},
			freeze: true,
			freeze_message: __("Making Issue.."),
			callback: function(r) {
				 
			}
		})
	},

	// create_customer: function(resp) {
	// 	var new_customer = frappe.model.make_new_doc_and_get_name('Customer');
	// 	new_customer = locals["Customer"][new_customer];
	// 	new_customer.customer_name = resp.name;
	// 	// new_customer.lead_name = resp.number;
		
	// 	frappe.set_route("Form", "Customer", new_customer.name);
	// },	
	create_issue: function(comm_details,comm_name) {
		communication_docname = comm_details.communication_name || comm_name;
		frappe.call({
			method: "frappe.email.inbox.make_issue_from_communication",
			args: {
				"communication":communication_docname
			},
			freeze: true,
			freeze_message: __("Making Issue.."),
			callback: function(r) {
				console.log("Issue created",r);
				me.page.main.find("#new_caller_issue").addClass(".hidden");
				me.page.main.find("#linked_issue").removeClass(".hidden");
				me.page.page.main.find("#new_caller_issue")[0].innerHTML = r;
				// 
			}
		})
	}
});