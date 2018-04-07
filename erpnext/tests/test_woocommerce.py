import unittest, frappe, requests, os, time, erpnext

class TestWoocommerce(unittest.TestCase):

	def setUp(self):
		# Set Secret in Woocommerce Settings
		company = frappe.new_doc("Company")
		company.company_name = "Woocommerce"
		company.abbr = "W"
		company.default_currency = "INR"
		company.save()
		frappe.db.commit()

		default = frappe.get_doc("Global Defaults")
		self.old_default_company = default.default_company
		default.default_company = "Woocommerce"
		default.save()

		frappe.db.commit()

		time.sleep(5)

		woo_settings = frappe.get_doc("Woocommerce Settings")
		woo_settings.secret = "ec434676aa1de0e502389f515c38f89f653119ab35e9117c7a79e576"
		woo_settings.woocommerce_server_url = "https://woocommerce.mntechnique.com/"
		woo_settings.api_consumer_key = "ck_fd43ff5756a6abafd95fadb6677100ce95a758a1"
		woo_settings.api_consumer_secret = "cs_94360a1ad7bef7fa420a40cf284f7b3e0788454e"
		woo_settings.enable_sync = 1
		woo_settings.tax_account = "Expenses - W"
		woo_settings.f_n_f_account = "Sales - W"
		woo_settings.save(ignore_permissions=True)

		frappe.db.commit()

	def test_woocommerce_request(self):
		r = emulate_request()
		self.assertTrue(r.status_code == 200)
		self.assertTrue(frappe.get_value("Customer",{"woocommerce_email":"newcaptain@gmail.com"}))
		self.assertTrue(frappe.get_value("Item",{"woocommerce_id": 374}))
		self.assertTrue(frappe.get_value("Sales Order",{"woocommerce_id":702}))

		# cancel & delete order
		cancel_and_delete_order()

		# Emulate Request when Customer, Address, Item data exists
		r = emulate_request()
		self.assertTrue(r.status_code == 200)
		self.assertTrue(frappe.get_value("Sales Order",{"woocommerce_id":702}))

	def tearDown(self):
		default = frappe.get_doc("Global Defaults")
		default.default_company = self.old_default_company
		default.save()
		frappe.db.commit()



def emulate_request():
	# Emulate Woocommerce Request
	headers = {
		"X-Wc-Webhook-Event":"created",
		"X-Wc-Webhook-Signature":"eBrvZ2+DR3S2hhEsxMoB4jCItmVykxZ/MHj/2qIJbrk="
	}
	# Emulate Request Data
	data = """{"id":702,"parent_id":0,"number":"702","order_key":"wc_order_5ac8b51aa2518","created_via":"checkout","version":"3.3.4","status":"processing","currency":"INR","date_created":"2018-04-07T12:10:02","date_created_gmt":"2018-04-07T12:10:02","date_modified":"2018-04-07T12:10:02","date_modified_gmt":"2018-04-07T12:10:02","discount_total":"0.00","discount_tax":"0.00","shipping_total":"100.00","shipping_tax":"12.00","cart_tax":"53.46","total":"611.00","total_tax":"65.46","prices_include_tax":true,"customer_id":21,"customer_ip_address":"103.54.96.14","customer_user_agent":"mozilla\/5.0 (x11; linux x86_64) applewebkit\/537.36 (khtml, like gecko) chrome\/65.0.3325.146 safari\/537.36","customer_note":"","billing":{"first_name":"New","last_name":"Captain","company":"","address_1":"Mumbai","address_2":"Dadar","city":"Thane","state":"MH","postcode":"123","country":"IN","email":"newcaptain@gmail.com","phone":"12345789123"},"shipping":{"first_name":"New","last_name":"Captain","company":"","address_1":"Mumbai","address_2":"Dadar","city":"Thane","state":"MH","postcode":"123","country":"IN"},"payment_method":"cod","payment_method_title":"Cash on delivery","transaction_id":"","date_paid":null,"date_paid_gmt":null,"date_completed":null,"date_completed_gmt":null,"cart_hash":"372f905c47a84bc1d08f20e59f4a449d","meta_data":[],"line_items":[{"id":266,"name":"Moon phases T shirt | Black colour","product_id":374,"variation_id":0,"quantity":1,"tax_class":"","subtotal":"445.54","subtotal_tax":"53.46","total":"445.54","total_tax":"53.46","taxes":[{"id":1,"total":"26.732143","subtotal":"26.732143"},{"id":3,"total":"26.732143","subtotal":"26.732143"}],"meta_data":[],"sku":"PT-0001","price":445.535714}],"tax_lines":[{"id":268,"rate_code":"IN-MH-SGST-1","rate_id":1,"label":"SGST","compound":false,"tax_total":"26.73","shipping_tax_total":"6.00","meta_data":[]},{"id":269,"rate_code":"IN-MH-CGST-2","rate_id":3,"label":"CGST","compound":false,"tax_total":"26.73","shipping_tax_total":"6.00","meta_data":[]}],"shipping_lines":[{"id":267,"method_title":"Flat rate","method_id":"flat_rate:1","total":"100.00","total_tax":"12.00","taxes":[{"id":1,"total":"6","subtotal":""},{"id":3,"total":"6","subtotal":""}],"meta_data":[{"id":1878,"key":"Items","value":"Moon phases T shirt | Black colour &times; 1"}]}],"fee_lines":[],"coupon_lines":[],"refunds":[]}"""

	# Build URL
	port = frappe.get_site_config().webserver_port or '8000'

	if os.environ.get('CI'):
		host = 'localhost'
	else:
		host = frappe.local.site

	url = "http://{site}:{port}/api/method/erpnext.erpnext_integrations.connectors.woocommerce_connection.order".format(site=host, port=port)

	r = requests.post(url=url, headers=headers, data=data)

	time.sleep(2)
	return r

def cancel_and_delete_order():
	# cancel & delete order
	try:
		so = frappe.get_doc("Sales Order",{"woocommerce_id":702})
		if isinstance(so, erpnext.selling.doctype.sales_order.sales_order.SalesOrder):
			so.cancel()
			so.delete()
		frappe.db.commit()
	except frappe.DoesNotExistError:
		pass