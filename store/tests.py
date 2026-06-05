from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from livestock.models import LivestockCategory, LivestockSpecies

from .models import Cart, CartItem, ContactMessage, Order, Product, Promotion


class CheckoutFlowTests(TestCase):
	def setUp(self):
		self.User = get_user_model()
		self.user = self.User.objects.create_user(
			username='buyer1',
			email='buyer1@example.com',
			password='StrongPass123!',
			role='customer',
		)
		self.category = LivestockCategory.objects.create(name='Poultry')
		self.species = LivestockSpecies.objects.create(category=self.category, name='Layer')
		self.product = Product.objects.create(
			livestock_species=self.species,
			name='Fresh Eggs',
			description='Test product',
			price=Decimal('2500.00'),
			unit='dozen',
			stock_quantity=10,
			is_available=True,
		)

	def test_checkout_redirects_when_cart_is_empty(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse('store:checkout'), secure=True)
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, reverse('store:cart'), fetch_redirect_response=False)

	def test_checkout_blocks_when_stock_is_insufficient(self):
		cart = Cart.objects.create(user=self.user)
		CartItem.objects.create(cart=cart, product=self.product, quantity=12)

		self.client.force_login(self.user)
		response = self.client.get(reverse('store:checkout'), secure=True)
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, reverse('store:cart'), fetch_redirect_response=False)
		self.assertEqual(Order.objects.count(), 0)

	def test_checkout_creates_order_and_clears_cart(self):
		cart = Cart.objects.create(user=self.user)
		CartItem.objects.create(cart=cart, product=self.product, quantity=2)

		self.client.force_login(self.user)
		response = self.client.post(reverse('store:checkout'), {
			'delivery_address': 'Kilometer 2, Shell Location Road, Uvwiamuge, Agbarho.',
			'phone': '08030000000',
			'notes': 'Please handle with care',
		}, secure=True)

		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, reverse('payments:initiate'), fetch_redirect_response=False)

		order = Order.objects.get(user=self.user)
		self.assertEqual(order.status, 'pending')
		self.assertEqual(order.total_amount, Decimal('5000.00'))
		self.assertEqual(order.items.count(), 1)

		self.product.refresh_from_db()
		self.assertEqual(self.product.stock_quantity, 10)
		self.assertEqual(cart.items.count(), 0)

	def test_checkout_post_revalidates_stock_before_creating_order(self):
		cart = Cart.objects.create(user=self.user)
		CartItem.objects.create(cart=cart, product=self.product, quantity=2)
		self.product.stock_quantity = 1
		self.product.save(update_fields=['stock_quantity'])

		self.client.force_login(self.user)
		response = self.client.post(reverse('store:checkout'), {
			'delivery_address': 'Kilometer 2, Shell Location Road, Uvwiamuge, Agbarho.',
			'phone': '08030000000',
			'notes': 'Please handle with care',
		}, secure=True)

		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, reverse('store:cart'), fetch_redirect_response=False)
		self.assertEqual(Order.objects.count(), 0)
		self.assertEqual(cart.items.count(), 1)

	def test_checkout_applies_active_promotion_to_total(self):
		cart = Cart.objects.create(user=self.user)
		CartItem.objects.create(cart=cart, product=self.product, quantity=2)
		Promotion.objects.create(
			title='Egg Promo',
			description='Discount on eggs',
			discount_percent=Decimal('10.00'),
			product=self.product,
			start_date=timezone.now().date(),
			end_date=timezone.now().date(),
			is_active=True,
		)

		self.client.force_login(self.user)
		response = self.client.post(reverse('store:checkout'), {
			'delivery_address': 'Kilometer 2, Shell Location Road, Uvwiamuge, Agbarho.',
			'phone': '08030000000',
			'notes': 'Please handle with care',
		}, secure=True)

		self.assertEqual(response.status_code, 302)
		order = Order.objects.get(user=self.user)
		self.assertEqual(order.total_amount, Decimal('4500.00'))
		self.assertEqual(order.items.get().unit_price, Decimal('2250.00'))

	def test_add_to_cart_blocks_when_requested_quantity_exceeds_stock(self):
		cart = Cart.objects.create(user=self.user)
		CartItem.objects.create(cart=cart, product=self.product, quantity=10)

		self.client.force_login(self.user)
		response = self.client.get(reverse('store:add_to_cart', args=[self.product.pk]), secure=True)

		self.assertEqual(response.status_code, 302)
		cart_item = CartItem.objects.get(cart=cart, product=self.product)
		self.assertEqual(cart_item.quantity, 10)

	def test_add_to_cart_returns_json_and_updates_count_for_ajax_requests(self):
		self.client.force_login(self.user)
		response = self.client.post(
			reverse('store:add_to_cart', args=[self.product.pk]),
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
			HTTP_ACCEPT='application/json',
			secure=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertJSONEqual(
			response.content,
			{'ok': True, 'message': '"Fresh Eggs" added to cart.', 'cart_item_count': 1},
		)
		self.assertEqual(CartItem.objects.get(product=self.product, cart__user=self.user).quantity, 1)

		second_response = self.client.post(
			reverse('store:add_to_cart', args=[self.product.pk]),
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
			HTTP_ACCEPT='application/json',
			secure=True,
		)

		self.assertEqual(second_response.status_code, 200)
		self.assertEqual(second_response.json()['cart_item_count'], 2)
		self.assertEqual(CartItem.objects.get(product=self.product, cart__user=self.user).quantity, 2)

	def test_add_to_cart_requires_login_for_ajax_requests(self):
		response = self.client.post(
			reverse('store:add_to_cart', args=[self.product.pk]),
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
			HTTP_ACCEPT='application/json',
			secure=True,
		)

		self.assertEqual(response.status_code, 401)
		self.assertEqual(response.json()['requires_login'], True)

	def test_update_cart_item_changes_quantity_within_stock(self):
		cart = Cart.objects.create(user=self.user)
		item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)

		self.client.force_login(self.user)
		response = self.client.post(
			reverse('store:update_cart_item', args=[item.pk]),
			{'quantity': 4},
			secure=True,
		)

		self.assertEqual(response.status_code, 302)
		item.refresh_from_db()
		self.assertEqual(item.quantity, 4)

	def test_product_list_filters_by_category_and_sort(self):
		fish_category = LivestockCategory.objects.create(name='Fishery')
		fish_species = LivestockSpecies.objects.create(category=fish_category, name='Catfish')
		Product.objects.create(
			livestock_species=fish_species,
			name='Catfish',
			description='Fresh fish',
			price=Decimal('4000.00'),
			unit='kg',
			stock_quantity=6,
			is_available=True,
		)

		response = self.client.get(
			reverse('store:product_list'),
			{'category': self.category.pk, 'sort': 'price_desc'},
			secure=True,
		)

		self.assertEqual(response.status_code, 200)
		products = list(response.context['products'])
		self.assertEqual(len(products), 1)
		self.assertEqual(products[0].name, 'Fresh Eggs')

	def test_customer_can_cancel_pending_order(self):
		order = Order.objects.create(
			user=self.user,
			status='pending',
			delivery_address='Kilometer 2, Shell Location Road, Uvwiamuge, Agbarho.',
			phone='08030000000',
			total_amount=Decimal('2500.00'),
		)

		self.client.force_login(self.user)
		response = self.client.post(reverse('store:cancel_order', args=[order.pk]), secure=True)

		self.assertEqual(response.status_code, 302)
		order.refresh_from_db()
		self.assertEqual(order.status, 'cancelled')

	def test_customer_cannot_cancel_shipped_order(self):
		order = Order.objects.create(
			user=self.user,
			status='shipped',
			delivery_address='Kilometer 2, Shell Location Road, Uvwiamuge, Agbarho.',
			phone='08030000000',
			total_amount=Decimal('2500.00'),
		)

		self.client.force_login(self.user)
		response = self.client.post(reverse('store:cancel_order', args=[order.pk]), secure=True)

		self.assertEqual(response.status_code, 302)
		order.refresh_from_db()
		self.assertEqual(order.status, 'shipped')

	def test_checkout_rejects_invalid_phone_number(self):
		cart = Cart.objects.create(user=self.user)
		CartItem.objects.create(cart=cart, product=self.product, quantity=1)

		self.client.force_login(self.user)
		response = self.client.post(reverse('store:checkout'), {
			'delivery_address': 'Kilometer 2, Shell Location Road, Uvwiamuge, Agbarho.',
			'phone': 'bad-phone',
			'notes': 'Please handle with care',
		}, secure=True)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(Order.objects.count(), 0)
		self.assertFormError(response.context['form'], 'phone', 'Enter a valid phone number.')

	def test_contact_rejects_too_short_message(self):
		response = self.client.post(reverse('store:contact'), {
			'name': 'Test User',
			'email': 'test@example.com',
			'phone': '08030000000',
			'message': 'short',
		}, secure=True)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(ContactMessage.objects.count(), 0)
