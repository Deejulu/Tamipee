from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import timedelta

from .forms import CustomerRegistrationForm, ProfileUpdateForm
from .models import EmailVerification


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountsFlowTests(TestCase):
	def setUp(self):
		self.User = get_user_model()

	def test_register_creates_customer_user_and_redirects_to_email_verification(self):
		"""Test that registration creates an active customer user and redirects to login"""
		response = self.client.post(reverse('accounts:register'), {
			'first_name': 'John',
			'last_name': 'Doe',
			'password1': 'StrongPass123!',
			'password2': 'StrongPass123!',
		})

		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, reverse('accounts:login'))
		# Find the created user by checking for john_doe in username
		user = self.User.objects.filter(first_name='John', last_name='Doe').first()
		self.assertIsNotNone(user)
		self.assertEqual(user.role, 'customer')
		self.assertTrue(user.is_active)  # Now active immediately
		self.assertTrue(user.username.startswith('john_doe'))  # Username generated from name
		self.assertEqual(len(mail.outbox), 0)  # No emails sent
		self.assertIsNone(self.client.session.get('_auth_user_id'))  # Not logged in yet

	def test_verify_email_with_correct_otp_activates_user(self):
		user = self.User.objects.create_user(
			username='otp_user',
			email='otp_user@example.com',
			password='StrongPass123!',
			is_active=False,
			email_verified=False,
		)
		verification, plain_otp = EmailVerification.create_for_user(user)

		response = self.client.post(
			reverse('accounts:verify_email', args=[user.pk]),
			{'otp_code': plain_otp},
			follow=True,
		)

		user.refresh_from_db()
		verification.refresh_from_db()
		self.assertRedirects(response, reverse('accounts:login'))
		self.assertTrue(user.is_active)
		self.assertTrue(user.email_verified)
		self.assertTrue(verification.is_used)

	def test_verify_email_locks_after_five_invalid_attempts(self):
		user = self.User.objects.create_user(
			username='locked_user',
			email='locked_user@example.com',
			password='StrongPass123!',
			is_active=False,
			email_verified=False,
		)
		verification, _ = EmailVerification.create_for_user(user)

		for _ in range(5):
			response = self.client.post(
				reverse('accounts:verify_email', args=[user.pk]),
				{'otp_code': '000000'},
			)

		verification.refresh_from_db()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(verification.attempts, 5)
		self.assertIsNotNone(verification.locked_until)
		self.assertGreater(verification.locked_until, timezone.now())

	def test_resend_otp_is_rate_limited_during_cooldown(self):
		user = self.User.objects.create_user(
			username='resend_user',
			email='resend_user@example.com',
			password='StrongPass123!',
			is_active=False,
			email_verified=False,
		)
		EmailVerification.create_for_user(user)

		response = self.client.get(reverse('accounts:resend_otp', args=[user.pk]), follow=True)

		self.assertRedirects(response, reverse('accounts:verify_email', args=[user.pk]))
		messages = [message.message for message in response.context['messages']]
		self.assertTrue(any('Please wait 2 minutes' in message for message in messages))
		self.assertEqual(EmailVerification.objects.filter(user=user).count(), 1)
		self.assertEqual(len(mail.outbox), 0)

	def test_resend_otp_sends_new_code_after_cooldown(self):
		user = self.User.objects.create_user(
			username='resend_ready_user',
			email='resend_ready@example.com',
			password='StrongPass123!',
			is_active=False,
			email_verified=False,
		)
		verification, _ = EmailVerification.create_for_user(user)
		verification.created_at = timezone.now() - timedelta(minutes=3)
		verification.save(update_fields=['created_at'])

		response = self.client.get(reverse('accounts:resend_otp', args=[user.pk]), follow=True)

		self.assertRedirects(response, reverse('accounts:verify_email', args=[user.pk]))
		self.assertEqual(EmailVerification.objects.filter(user=user).count(), 2)
		self.assertEqual(EmailVerification.objects.filter(user=user, is_used=False).count(), 1)
		self.assertEqual(len(mail.outbox), 1)

	def test_login_invalid_credentials_shows_error(self):
		self.User.objects.create_user(
			username='validuser',
			email='valid@example.com',
			password='StrongPass123!',
		)

		response = self.client.post(reverse('accounts:login'), {
			'username': 'validuser',
			'password': 'wrong-password',
		}, follow=True)

		self.assertEqual(response.status_code, 200)
		messages = [m.message for m in response.context['messages']]
		self.assertIn('Invalid username or password.', messages)

	def test_login_accepts_email_address(self):
		"""Test that login works with username (no longer email-based)"""
		user = self.User.objects.create_user(
			username='testuser123',
			email='email-login@example.com',
			password='StrongPass123!',
			role='customer',
		)

		response = self.client.post(reverse('accounts:login'), {
			'username': 'testuser123',  # Login with username, not email
			'password': 'StrongPass123!',
		}, follow=True)

		self.assertRedirects(response, reverse('dashboard:customer'))
		self.assertEqual(self.client.session.get('_auth_user_id'), str(user.pk))

	def test_password_reset_redirects_existing_user_to_confirm_page(self):
		"""Test that password reset now shows admin contact message"""
		self.User.objects.create_user(
			username='reset_user',
			email='reset@example.com',
			password='StrongPass123!',
		)

		response = self.client.get(reverse('accounts:password_reset'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'administrator')
		self.assertEqual(len(mail.outbox), 0)

	def test_password_reset_shows_error_for_unknown_user(self):
		"""Test that password reset shows admin contact message"""
		response = self.client.get(reverse('accounts:password_reset'), follow=True)

		self.assertEqual(response.status_code, 200)
		messages = [message.message for message in response.context['messages']]
		self.assertIn('Password reset is handled by administrators. Please contact support to reset your password.', messages)
		self.assertEqual(len(mail.outbox), 0)

	def test_dashboard_redirects_by_user_role(self):
		admin_user = self.User.objects.create_user(
			username='admin_u',
			email='admin_u@example.com',
			password='StrongPass123!',
			role='admin',
		)
		staff_user = self.User.objects.create_user(
			username='staff_u',
			email='staff_u@example.com',
			password='StrongPass123!',
			role='staff',
		)
		customer_user = self.User.objects.create_user(
			username='cust_u',
			email='cust_u@example.com',
			password='StrongPass123!',
			role='customer',
		)
		super_user = self.User.objects.create_superuser(
			username='root_u',
			email='root_u@example.com',
			password='StrongPass123!',
		)

		self.client.force_login(admin_user)
		self.assertRedirects(self.client.get(reverse('accounts:dashboard')), reverse('dashboard:admin'))

		self.client.force_login(staff_user)
		self.assertRedirects(self.client.get(reverse('accounts:dashboard')), reverse('dashboard:staff'))

		self.client.force_login(customer_user)
		self.assertRedirects(self.client.get(reverse('accounts:dashboard')), reverse('dashboard:customer'))

		self.client.force_login(super_user)
		self.assertRedirects(self.client.get(reverse('accounts:dashboard')), reverse('dashboard:admin'))

	def test_customer_registration_form_rejects_existing_email_case_insensitive(self):
		"""Test that customer registration form validates first_name and last_name"""
		# Since email is no longer used for customer registration, test name validation
		form = CustomerRegistrationForm(data={
			'first_name': 'John',
			'last_name': 'Doe',
			'password1': 'StrongPass123!',
			'password2': 'StrongPass123!',
		})

		self.assertTrue(form.is_valid())
		# Test missing fields
		form_invalid = CustomerRegistrationForm(data={
			'password1': 'StrongPass123!',
			'password2': 'StrongPass123!',
		})
		self.assertFalse(form_invalid.is_valid())
		self.assertIn('first_name', form_invalid.errors)
		self.assertIn('last_name', form_invalid.errors)

	def test_profile_update_form_rejects_email_used_by_another_user(self):
		owner = self.User.objects.create_user(
			username='owner',
			email='owner@example.com',
			password='StrongPass123!',
		)
		other = self.User.objects.create_user(
			username='other',
			email='other@example.com',
			password='StrongPass123!',
		)

		form = ProfileUpdateForm(instance=owner, data={
			'username': owner.username,
			'first_name': owner.first_name,
			'last_name': owner.last_name,
			'email': 'Other@Example.com',
			'phone': owner.phone,
			'address': owner.address,
		})

		self.assertFalse(form.is_valid())
		self.assertIn('email', form.errors)
