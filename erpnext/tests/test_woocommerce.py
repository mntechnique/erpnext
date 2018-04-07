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
		self.assertTrue(frappe.get_value("Customer",{"woocommerce_email":"tony@gmail.com"}))
		self.assertTrue(frappe.get_value("Item",{"woocommerce_id": 56}))
		self.assertTrue(frappe.get_value("Sales Order",{"woocommerce_id":74}))

		# cancel & delete order
		cancel_and_delete_order()

		# Emulate Request when Customer, Address, Item data exists
		r = emulate_request()
		self.assertTrue(r.status_code == 200)
		self.assertTrue(frappe.get_value("Sales Order",{"woocommerce_id":74}))

	def tearDown(self):
		default = frappe.get_doc("Global Defaults")
		default.default_company = self.old_default_company
		default.save()
		frappe.db.commit()



def emulate_request():
	# Emulate Woocommerce Request
	headers = {
		"X-Wc-Webhook-Event":"created",
		"X-Wc-Webhook-Signature":"A2//zEZfIeNgY9kOTfp5zXWHH2yxivqV1HMpWNNgJ+o="
	}
	# Emulate Request Data
	data = """{u'date_completed_gmt': None, u'date_modified_gmt': u'2018-04-07T10:39:33', u'payment_method': u'cod', u'discount_tax': u'0.00', u'number': u'685', u'currency': u'INR', u'cart_hash': u'612642db682c427f58b298aef373ec5b', u'total': u'911.00', u'shipping_tax': u'12.00', u'id': 685, u'customer_ip_address': u'103.54.96.14', u'prices_include_tax': True, u'coupon_lines': [], u'billing': {u'city': u'Thane', u'first_name': u'New', u'last_name': u'Captain', u'country': u'IN', u'company': u'', u'phone': u'12345789123', u'state': u'MH', u'address_1': u'Mumbai', u'address_2': u'Dadar', u'email': u'newcaptain@gmail.com', u'postcode': u'123'}, u'customer_user_agent': u'mozilla/5.0 (x11; linux x86_64) applewebkit/537.36 (khtml, like gecko) chrome/65.0.3325.146 safari/537.36', u'date_paid_gmt': None, u'parent_id': 0, u'created_via': u'checkout', u'version': u'3.3.4', u'fee_lines': [], u'customer_id': 21, u'transaction_id': u'', u'status': u'processing', u'total_tax': u'97.60', u'customer_note': u'', u'tax_lines': [{u'tax_total': u'42.80', u'shipping_tax_total': u'6.00', u'label': u'SGST', u'meta_data': [], u'compound': False, u'rate_id': 1, u'rate_code': u'IN-MH-SGST-1', u'id': 249}, {u'tax_total': u'42.80', u'shipping_tax_total': u'6.00', u'label': u'CGST', u'meta_data': [], u'compound': False, u'rate_id': 3, u'rate_code': u'IN-MH-CGST-2', u'id': 250}], u'shipping_total': u'100.00', u'payment_method_title': u'Cash on delivery', u'meta_data': [], u'discount_total': u'0.00', u'order_key': u'wc_order_5ac89fe599930', u'line_items': [{u'sku': u'Green Color Cotton Leggings', u'total_tax': u'32.14', u'product_id': 281, u'price': 267.857143, u'tax_class': u'', u'variation_id': 289, u'taxes': [{u'total': u'16.071429', u'subtotal': u'16.071429', u'id': 1}, {u'total': u'16.071429', u'subtotal': u'16.071429', u'id': 3}], u'name': u'Cotton Leggings - L, GREEN', u'meta_data': [{u'value': u'L', u'id': 1746, u'key': u'size'}, {u'value': u'GREEN', u'id': 1747, u'key': u'color'}], u'subtotal_tax': u'32.14', u'total': u'267.86', u'subtotal': u'267.86', u'id': 246, u'quantity': 1}, {u'sku': u'PT-0001', u'total_tax': u'53.46', u'product_id': 374, u'price': 445.535714, u'tax_class': u'', u'variation_id': 0, u'taxes': [{u'total': u'26.732143', u'subtotal': u'26.732143', u'id': 1}, {u'total': u'26.732143', u'subtotal': u'26.732143', u'id': 3}], u'name': u'Moon phases T shirt | Black colour', u'meta_data': [], u'subtotal_tax': u'53.46', u'total': u'445.54', u'subtotal': u'445.54', u'id': 247, u'quantity': 1}], u'shipping_lines': [{u'total_tax': u'12.00', u'method_id': u'flat_rate:1', u'method_title': u'Flat rate', u'taxes': [{u'total': u'6', u'subtotal': u'', u'id': 1}, {u'total': u'6', u'subtotal': u'', u'id': 3}], u'meta_data': [{u'value': u'Moon phases T shirt | Black colour &times; 1', u'id': 1761, u'key': u'Items'}], u'total': u'100.00', u'id': 248}], u'date_completed': None, u'refunds': [], u'date_modified': u'2018-04-07T10:39:33', u'date_created_gmt': u'2018-04-07T10:39:33', u'shipping': {u'city': u'Thane', u'first_name': u'New', u'last_name': u'Captain', u'country': u'IN', u'company': u'', u'state': u'MH', u'address_1': u'Mumbai', u'address_2': u'Dadar', u'postcode': u'123'}, u'date_paid': None, u'date_created': u'2018-04-07T10:39:33', u'cart_tax': u'85.60'}"""

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
		so = frappe.get_doc("Sales Order",{"woocommerce_id":74})
		if isinstance(so, erpnext.selling.doctype.sales_order.sales_order.SalesOrder):
			so.cancel()
			so.delete()
		frappe.db.commit()
	except frappe.DoesNotExistError:
		pass