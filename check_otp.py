#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tamipee.settings')
django.setup()

from accounts.models import EmailVerification, CustomUser

user = CustomUser.objects.filter(email='daveed0011@gmail.com').first()
if user:
    ev = EmailVerification.objects.filter(user=user).order_by('-created_at').first()
    if ev:
        print(f'\n{"="*50}')
        print(f'CURRENT OTP FOR: {user.email}')
        print(f'{"="*50}')
        print(f'OTP CODE: {ev.otp_code}')
        print(f'Created: {ev.created_at}')
        print(f'Expires: {ev.expires_at}')
        print(f'Attempts Used: {ev.attempts}/{ev.max_attempts}')
        print(f'Is Locked: {ev.is_locked}')
        print(f'{"="*50}\n')
    else:
        print('No OTP found for this user')
else:
    print('User not found')
