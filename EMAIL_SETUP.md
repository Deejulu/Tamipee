# Email Setup for OTP Delivery

## Overview
OTP codes are now sent to your email inbox in both development and production environments.

## Local Development Setup

### 1. Create a `.env` file
If you don't already have a `.env` file, copy the example:
```bash
cp .env.example .env
```

### 2. Configure Email SMTP Settings
Add these variables to your `.env` file:

#### Option A: Gmail (Quick Setup for Testing)
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Tamipee Farms <your-email@gmail.com>
```

**Important:** For Gmail, you need an **App Password**, not your regular password:
1. Go to your Google Account settings
2. Enable 2-Step Verification
3. Go to Security → App Passwords
4. Create a new app password for "Mail"
5. Use that 16-character password in `EMAIL_HOST_PASSWORD`

#### Option B: SendGrid (Recommended for Production)
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Tamipee Farms <verified@yourdomain.com>
```

**Steps:**
1. Sign up at https://sendgrid.com (free tier: 100 emails/day)
2. Verify a sender email address
3. Create an API key
4. Use `apikey` as username and your API key as password

#### Option C: Brevo (formerly Sendinblue)
```env
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-brevo-smtp-key
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Tamipee Farms <your-email@gmail.com>
```

**Steps:**
1. Sign up at https://www.brevo.com (free tier: 300 emails/day)
2. Go to SMTP & API → SMTP
3. Generate an SMTP key
4. Use your login email as username and the SMTP key as password

### 3. Test OTP Email Delivery
1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Register a new user account at http://127.0.0.1:8000/accounts/register/

3. Check your email inbox for the verification code

4. The OTP will also be displayed on the verification page during development (as a fallback)

## Troubleshooting

### Email not received
- Check your spam/junk folder
- Verify SMTP credentials in `.env` are correct
- Check the Django console for error messages
- Test with a different email provider

### "SMTPAuthenticationError"
- Gmail: Make sure you're using an App Password, not your regular password
- SendGrid/Brevo: Verify your API key is correct and not expired

### "SMTPConnectError"
- Check your firewall or antivirus isn't blocking port 587
- Try using port 465 with `EMAIL_USE_TLS=False` and `EMAIL_USE_SSL=True`

## Production Notes
For production deployment on Render, add the same email environment variables to your Render dashboard under "Environment" settings.
