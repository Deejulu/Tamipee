import hashlib
import hmac
import json
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from store.models import Order, OrderItem, Product
from .models import Payment


class PaymentsFlowTests(TestCase):
	def setUp(self):
		self.User = get_user_model()
		self.user = self.User.objects.create_user(
			username='payer1',
			email='payer1@example.com',
			password='StrongPass123!',
			role='customer',
		)
		self.product = Product.objects.create(
			name='Fresh Eggs',
			description='Test product',
			price=Decimal('2500.00'),
			unit='dozen',
			stock_quantity=10,
			is_available=True,
		)

	def test_initiate_payment_creates_payment_for_pending_order(self):
		order = Order.objects.create(
			user=self.user,
			delivery_address='Test Address',
			phone='08031111111',
			total_amount=Decimal('12000.00'),
			status='pending',
		)

		self.client.force_login(self.user)
		response = self.client.get(reverse('payments:initiate'), secure=True)

		self.assertEqual(response.status_code, 200)
		payment = Payment.objects.get(order=order)
		self.assertEqual(payment.user, self.user)
		self.assertEqual(payment.amount, Decimal('12000.00'))
		self.assertEqual(payment.status, 'pending')

	def test_payment_callback_rejects_invalid_signature(self):
		payload = {'event': 'charge.success', 'data': {'reference': 'INVALID-REF'}}
		response = self.client.post(
			reverse('payments:callback'),
			data=json.dumps(payload),
			content_type='application/json',
			HTTP_X_PAYSTACK_SIGNATURE='invalid-signature',
			secure=True,
		)
		self.assertEqual(response.status_code, 400)

	def test_payment_callback_marks_payment_success_and_confirms_order(self):
		order = Order.objects.create(
			user=self.user,
			delivery_address='Test Address',
			phone='08032222222',
			total_amount=Decimal('7500.00'),
			status='pending',
		)
		payment = Payment.objects.create(
			user=self.user,
			order=order,
			reference='TIF-TEST-123',
			amount=Decimal('7500.00'),
			status='pending',
		)
		OrderItem.objects.create(order=order, product=self.product, quantity=2, unit_price=Decimal('2500.00'))

		payload = {
			'event': 'charge.success',
			'data': {
				'reference': payment.reference,
				'status': 'success',
			},
		}
		body = json.dumps(payload).encode('utf-8')
		signature = hmac.new(
			settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
			body,
			hashlib.sha512,
		).hexdigest()

		response = self.client.post(
			reverse('payments:callback'),
			data=body,
			content_type='application/json',
			HTTP_X_PAYSTACK_SIGNATURE=signature,
			secure=True,
		)

		self.assertEqual(response.status_code, 200)

		payment.refresh_from_db()
		order.refresh_from_db()
		self.product.refresh_from_db()
		self.assertEqual(payment.status, 'success')
		self.assertEqual(order.status, 'confirmed')
		self.assertTrue(order.inventory_applied)
		self.assertEqual(self.product.stock_quantity, 8)

	def test_payment_callback_does_not_deduct_stock_twice_for_confirmed_payment(self):
		order = Order.objects.create(
			user=self.user,
			delivery_address='Test Address',
			phone='08032222222',
			total_amount=Decimal('5000.00'),
			status='confirmed',
		)
		payment = Payment.objects.create(
			user=self.user,
			order=order,
			reference='TIF-TEST-456',
			amount=Decimal('5000.00'),
			status='success',
		)
		OrderItem.objects.create(order=order, product=self.product, quantity=2, unit_price=Decimal('2500.00'))
		self.product.stock_quantity = 8
		self.product.save(update_fields=['stock_quantity'])

		payload = {
			'event': 'charge.success',
			'data': {
				'reference': payment.reference,
				'status': 'success',
			},
		}
		body = json.dumps(payload).encode('utf-8')
		signature = hmac.new(
			settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
			body,
			hashlib.sha512,
		).hexdigest()

		response = self.client.post(
			reverse('payments:callback'),
			data=body,
			content_type='application/json',
			HTTP_X_PAYSTACK_SIGNATURE=signature,
			secure=True,
		)

		self.assertEqual(response.status_code, 200)
		self.product.refresh_from_db()
		self.assertEqual(self.product.stock_quantity, 8)
