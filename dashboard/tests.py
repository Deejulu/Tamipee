from datetime import date

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings

from livestock.models import DailyFeedLog, DailyProductionLog, LivestockCategory, LivestockSpecies
from store.models import Order, OrderItem, Product


class DashboardAccessAndRoleTests(TestCase):
	def setUp(self):
		self.User = get_user_model()
		self.admin_user = self.User.objects.create_user(
			username='admin1',
			email='admin1@example.com',
			password='StrongPass123!',
			role='admin',
			is_staff=True,
		)
		self.customer_user = self.User.objects.create_user(
			username='customer1',
			email='customer1@example.com',
			password='StrongPass123!',
			role='customer',
		)

	def test_admin_users_forbidden_for_customer(self):
		self.client.force_login(self.customer_user)
		response = self.client.get(reverse('dashboard:admin_users'), secure=True)
		self.assertEqual(response.status_code, 403)

	def test_admin_can_update_user_role_and_staff_flag(self):
		target = self.User.objects.create_user(
			username='target1',
			email='target1@example.com',
			password='StrongPass123!',
			role='customer',
			is_staff=False,
		)

		self.client.force_login(self.admin_user)
		response = self.client.post(
			reverse('dashboard:admin_update_user_role', args=[target.pk]),
			{'role': 'staff'},
			secure=True,
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		target.refresh_from_db()
		self.assertEqual(target.role, 'staff')
		self.assertTrue(target.is_staff)

	def test_superuser_role_cannot_be_changed_to_non_admin(self):
		super_user = self.User.objects.create_superuser(
			username='rootsafe',
			email='rootsafe@example.com',
			password='StrongPass123!',
		)

		self.client.force_login(self.admin_user)
		self.client.post(
			reverse('dashboard:admin_update_user_role', args=[super_user.pk]),
			{'role': 'customer'},
			secure=True,
			follow=True,
		)

		super_user.refresh_from_db()
		self.assertTrue(super_user.is_superuser)
		self.assertEqual(super_user.role, 'admin')


class DashboardDailyLogTemplateRegressionTests(TestCase):
	def setUp(self):
		self.User = get_user_model()
		self.admin_user = self.User.objects.create_user(
			username='adminlog',
			email='adminlog@example.com',
			password='StrongPass123!',
			role='admin',
			is_staff=True,
		)
		category = LivestockCategory.objects.create(name='Poultry')
		self.species = LivestockSpecies.objects.create(category=category, name='Layer')

	def test_daily_log_page_renders_with_null_recorded_by(self):
		DailyFeedLog.objects.create(
			date=date.today(),
			species=self.species,
			feed_type='Layer Mash',
			bags_consumed=2,
			recorded_by=None,
		)
		DailyProductionLog.objects.create(
			date=date.today(),
			species=self.species,
			product='Eggs',
			quantity=3,
			unit='crates',
			recorded_by=None,
		)

		self.client.force_login(self.admin_user)
		response = self.client.get(reverse('dashboard:admin_daily_log'), secure=True)
		self.assertEqual(response.status_code, 200)

	def test_admin_can_log_egg_production_with_damage_counts(self):
		self.client.force_login(self.admin_user)
		response = self.client.post(
			reverse('dashboard:admin_daily_log'),
			{
				'form_type': 'production',
				'date': date.today(),
				'species': self.species.pk,
				'product': 'Eggs',
				'quantity': '4',
				'unit': 'crate',
				'egg_count': '120',
				'damaged_count': '6',
				'notes': 'Morning collection',
			},
			secure=True,
		)

		self.assertEqual(response.status_code, 302)
		entry = DailyProductionLog.objects.get(product='Eggs')
		self.assertEqual(entry.egg_count, 120)
		self.assertEqual(entry.damaged_count, 6)
		self.assertEqual(entry.saleable_quantity, 114)


class DashboardEggReportsTests(TestCase):
	def setUp(self):
		self.User = get_user_model()
		self.admin_user = self.User.objects.create_user(
			username='eggadmin',
			email='eggadmin@example.com',
			password='StrongPass123!',
			role='admin',
			is_staff=True,
		)
		self.customer_user = self.User.objects.create_user(
			username='eggbuyer',
			email='eggbuyer@example.com',
			password='StrongPass123!',
			role='customer',
		)
		category = LivestockCategory.objects.create(name='Poultry')
		self.species = LivestockSpecies.objects.create(category=category, name='Layer')
		self.egg_product = Product.objects.create(
			livestock_species=self.species,
			name='Fresh Eggs',
			description='Clean table eggs',
			price=5500,
			unit='crate',
			stock_quantity=18,
		)

	def test_reports_include_egg_production_and_sales_metrics(self):
		DailyProductionLog.objects.create(
			date=date.today(),
			species=self.species,
			product='Eggs',
			quantity=4,
			unit='crate',
			egg_count=120,
			damaged_count=6,
		)
		order = Order.objects.create(
			user=self.customer_user,
			status='delivered',
			delivery_address='Farm Road 12',
			phone='08030000000',
			total_amount=11000,
		)
		OrderItem.objects.create(order=order, product=self.egg_product, quantity=2, unit_price=5500)

		self.client.force_login(self.admin_user)
		response = self.client.get(reverse('dashboard:admin_reports'), secure=True)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['egg_metrics']['collected'], 120)
		self.assertEqual(response.context['egg_metrics']['saleable'], 114)
		self.assertEqual(response.context['egg_metrics']['damaged'], 6)
		self.assertEqual(response.context['egg_sales_revenue'], 11000)
		self.assertEqual(response.context['egg_units_sold'], 2)
		self.assertEqual(response.context['egg_stock_units'], 18)
		self.assertContains(response, 'Egg Production And Sales')


class DashboardOrderInventoryTests(TestCase):
	def setUp(self):
		self.User = get_user_model()
		self.admin_user = self.User.objects.create_user(
			username='inventoryadmin',
			email='inventoryadmin@example.com',
			password='StrongPass123!',
			role='admin',
			is_staff=True,
		)
		self.customer_user = self.User.objects.create_user(
			username='inventorycustomer',
			email='inventorycustomer@example.com',
			password='StrongPass123!',
			role='customer',
		)
		category = LivestockCategory.objects.create(name='Poultry')
		species = LivestockSpecies.objects.create(category=category, name='Layer')
		self.product = Product.objects.create(
			livestock_species=species,
			name='Fresh Eggs',
			description='Farm eggs',
			price=5500,
			unit='crate',
			stock_quantity=20,
		)
		self.order = Order.objects.create(
			user=self.customer_user,
			status='confirmed',
			delivery_address='Farm Road 12',
			phone='08030000000',
			total_amount=11000,
			inventory_applied=True,
		)
		OrderItem.objects.create(order=self.order, product=self.product, quantity=2, unit_price=5500)
		self.product.stock_quantity = 18
		self.product.save(update_fields=['stock_quantity'])

	def test_admin_cancelling_confirmed_order_restocks_inventory(self):
		self.client.force_login(self.admin_user)
		response = self.client.post(
			reverse('dashboard:update_order_status', args=[self.order.pk]),
			{'status': 'cancelled'},
			secure=True,
		)

		self.assertEqual(response.status_code, 302)
		self.order.refresh_from_db()
		self.product.refresh_from_db()
		self.assertEqual(self.order.status, 'cancelled')
		self.assertFalse(self.order.inventory_applied)
		self.assertEqual(self.product.stock_quantity, 20)

	@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
	def test_admin_status_update_sends_customer_email_and_warns_on_low_stock(self):
		self.order.inventory_applied = False
		self.order.status = 'pending'
		self.order.save(update_fields=['inventory_applied', 'status', 'updated_at'])
		self.product.stock_quantity = 5
		self.product.save(update_fields=['stock_quantity'])

		self.client.force_login(self.admin_user)
		response = self.client.post(
			reverse('dashboard:update_order_status', args=[self.order.pk]),
			{'status': 'confirmed'},
			secure=True,
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.order.refresh_from_db()
		self.product.refresh_from_db()
		self.assertEqual(self.order.status, 'confirmed')
		self.assertTrue(self.order.inventory_applied)
		self.assertEqual(self.product.stock_quantity, 3)
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn('Order #', mail.outbox[0].subject)
		messages = list(response.context['messages'])
		self.assertTrue(any('Low stock alert' in str(message) for message in messages))
