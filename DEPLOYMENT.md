# Deployment Guide - Render.com

This guide walks you through deploying Tamipee Integrated Farms to Render.com step-by-step.

## Prerequisites

Before you begin, make sure you have:

1. ✅ GitHub account
2. ✅ Render.com account (sign up at https://render.com)
3. ✅ Paystack account with LIVE API keys (https://paystack.com)
4. ✅ Gmail account with App Password generated
5. ✅ Your code pushed to a GitHub repository

## Part 1: Push to GitHub

### 1.1 Initialize Git Repository (if not already done)

```bash
# Navigate to your project folder
cd "c:\Users\user\Documents\web proj\Tamipee Integrated Farms"

# Initialize git
git init

# Add all files
git add .

# Make first commit
git commit -m "Initial commit - Tamipee Integrated Farms"
```

### 1.2 Create GitHub Repository

1. Go to https://github.com
2. Click the **+** icon → **New repository**
3. Name: `tamipee-integrated-farms` (or your preferred name)
4. Description: "Farm management and e-commerce platform"
5. **Keep it Private** if this is a production business application
6. Do NOT initialize with README (you already have one)
7. Click **Create repository**

### 1.3 Push Your Code

```bash
# Add GitHub as remote origin (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/tamipee-integrated-farms.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**IMPORTANT**: Before pushing, verify `.env` is in `.gitignore` and NOT being tracked:
```bash
git status
# .env should NOT appear in the list
# If it does, run: git rm --cached .env
```

## Part 2: Set Up Database (Choose ONE Option)

### Option A: Render PostgreSQL (Recommended for Simplicity)

#### 2A.1 Create Database

1. Go to https://dashboard.render.com
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `tamipee-farms-db`
   - **Database**: `tamipee_db` (auto-generated)
   - **User**: `tamipee_user` (auto-generated)
   - **Region**: Choose closest to your target audience
   - **Plan**: Free (or paid for production)
4. Click **Create Database**
5. Wait for "Available" status (may take 1-2 minutes)

#### 2A.2 Copy Database URL

1. In your database dashboard, find **Internal Database URL**
2. It looks like: `postgresql://user:password@host/database`
3. **Copy this entire URL** - you'll use it as-is in Part 3

### Option B: Supabase PostgreSQL

#### 2B.1 Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click **New project**
3. Configure:
   - **Name**: `tamipee-farms`
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your target audience
   - **Plan**: Free tier available
4. Click **Create new project**
5. Wait for project setup to complete

#### 2B.2 Get Connection String (IMPORTANT: Use Direct Connection)

1. In Supabase dashboard, go to **Project Settings** → **Database**
2. Scroll to **Connection string** section
3. Select **URI** tab
4. **IMPORTANT**: Use the **Direct Connection** string, NOT the Pooler
5. Copy the connection string that looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
6. Replace `[YOUR-PASSWORD]` with your actual database password
7. If password has special characters (`@`, `:`, `/`, `%`, `#`), URL-encode them:
   - `@` → `%40`
   - `:` → `%3A`
   - `/` → `%2F`
   - `%` → `%25`
   - `#` → `%23`

**Example with special chars**:
- Password: `MyP@ss:123`
- Encoded: `MyP%40ss%3A123`
- Full URL: `postgresql://postgres:MyP%40ss%3A123@db.abc123xyz.supabase.co:5432/postgres`

**⚠️ Common Mistakes to Avoid**:
- ❌ Don't use the Pooler connection (it has compatibility issues with Django)
- ❌ Don't forget to replace `[YOUR-PASSWORD]` with actual password
- ❌ Don't add quotes around the URL in Render
- ✅ Use Direct Connection format shown above

## Part 3: Deploy Web Service

### 3.1 Create Web Service

1. In Render dashboard, click **New +** → **Web Service**
2. Connect your GitHub account if not already connected
3. Find and select your `tamipee-integrated-farms` repository
4. Click **Connect**

### 3.2 Configure Service

Fill in the following:

- **Name**: `tamipee-farms` (this becomes your URL subdomain)
- **Region**: Same as your database region
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn tamipee.wsgi:application`
- **Plan**: Free (or paid tier for production traffic)

### 3.3 Add Environment Variables

Click **Advanced** → **Add Environment Variable** and add these one by one:

#### Required Variables

```env
# Django Core
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<GENERATE_NEW_KEY_SEE_BELOW>
DJANGO_ALLOWED_HOSTS=tamipee-farms.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://tamipee-farms.onrender.com

# Database (paste the connection URL from Part 2)
# For Render PostgreSQL: Use Internal Database URL from step 2A.2
# For Supabase: Use Direct Connection URL from step 2B.2
# Example Render: postgresql://tamipee_user:password@host/tamipee_db
# Example Supabase: postgresql://postgres:password@db.projectref.supabase.co:5432/postgres
DATABASE_URL=<PASTE_YOUR_DATABASE_URL_HERE>

# Paystack (LIVE KEYS - get from dashboard.paystack.com)
PAYSTACK_PUBLIC_KEY=pk_live_your_actual_live_key_here
PAYSTACK_SECRET_KEY=sk_live_your_actual_live_key_here

# Email (Gmail)
EMAIL_HOST_USER=your-farm-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=Tamipee Integrated Farms <your-farm-email@gmail.com>
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Security Settings
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
```

#### How to Generate DJANGO_SECRET_KEY

On your local machine, run:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and use it as your `DJANGO_SECRET_KEY`.

**CRITICAL**: Use a NEW key for production, different from your local `.env` file!

#### How to Get Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. You must have 2-Factor Authentication enabled
3. Select **Mail** and your device
4. Click **Generate**
5. Copy the 16-character password (no spaces)
6. Use it as `EMAIL_HOST_PASSWORD`

### 3.4 Deploy

1. Click **Create Web Service**
2. Render will start building your application
3. Monitor the logs - you should see:
   - Installing dependencies
   - Running migrations
   - Collecting static files
   - Build completed successfully

First deploy may take 5-10 minutes.

## Part 4: Post-Deployment Setup

### 4.1 Create Superuser

Once deployment succeeds:

1. In Render dashboard, go to your web service
2. Click **Shell** tab (top right)
3. Run:
```bash
python manage.py createsuperuser
```
4. Follow prompts to create admin account

### 4.2 Test Your Site

Visit: `https://tamipee-farms.onrender.com` (replace with your actual name)

✅ **Verify**:
- Homepage loads
- Products page displays
- Login/Register works
- Admin panel accessible at `/admin/`

### 4.3 Test Payments (Optional Test Mode First)

Before using LIVE keys, test with Paystack test mode:

1. Temporarily change environment variables:
   ```
   PAYSTACK_PUBLIC_KEY=pk_test_...
   PAYSTACK_SECRET_KEY=sk_test_...
   ```
2. Redeploy (Render auto-deploys on env variable changes)
3. Add product to cart
4. Go to checkout
5. Use test card: `4084 0840 8408 4081` (any future expiry, any CVV)
6. Verify order completes
7. **Switch back to LIVE keys when ready for production**

### 4.4 Populate Sample Data (Optional)

To add demo content:

1. In Render Shell:
```bash
python manage.py populate_sample
```

2. Or use the admin dashboard:
   - Login at `/admin/`
   - Navigate to `/dashboard/admin/sample-data/`
   - Click **Populate Sample Data**

To remove sample data later:
```bash
python manage.py delete_sample
```

## Part 5: Troubleshooting Common Deployment Issues

### Issue: "tenant/user postgres.XXXXX not found" (Supabase)

**Error message**:
```
django.db.utils.OperationalError: connection failed: FATAL: (ENOTFOUND) tenant/user postgres.lzsimijosxbarnstgkyb not found
```

**Cause**: You're using the Supabase **Pooler** connection string instead of the **Direct** connection string, or the connection format is incorrect.

**Fix**:
1. Go to Supabase Dashboard → Project Settings → Database
2. Under "Connection string", select **URI** tab
3. **Copy the Direct Connection string** (NOT Pooler):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
4. Replace `[YOUR-PASSWORD]` with your actual database password
5. If password contains special characters, URL-encode them:
   - `@` → `%40`, `:` → `%3A`, `/` → `%2F`, `%` → `%25`, `#` → `%23`
6. In Render Dashboard:
   - Go to your web service → Environment
   - Update `DATABASE_URL` with the corrected string
   - Click **Save Changes**
7. Render will auto-deploy; monitor logs for validation success

**Verification**: After redeployment, you should see in logs:
```
✓ DATABASE_URL validation passed
  Host: db.[PROJECT-REF].supabase.co
  Port: 5432
  User: postgres
```

### Issue: "DATABASE_URL is not set"

**Cause**: Environment variable missing or empty.

**Fix**:
1. Render Dashboard → Your web service → Environment
2. Add environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Your database connection string (no quotes)
3. Save and redeploy

### Issue: Static files (CSS/JS) not loading

**Cause**: `collectstatic` failed or `STATIC_ROOT` misconfigured.

**Fix**:
1. Check logs for `collectstatic` errors
2. Verify `render.yaml` has:
   ```yaml
   buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput --clear
   ```
3. Ensure `DJANGO_SETTINGS_MODULE=tamipee.settings` in environment variables
4. Trigger manual deploy

### Issue: Admin can't log in after deployment

**Cause**: Superuser not created or database is empty.

**Fix** (requires paid Render plan for shell access):
```bash
python manage.py createsuperuser
```

**Alternative** (via environment variable):
Add these to Render environment variables:
```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@tamipeefarms.com
DJANGO_SUPERUSER_PASSWORD=your_secure_password
```

Then add to `start.sh` after migrations:
```bash
python manage.py createsuperuser --noinput || true
```

### Issue: "DisallowedHost" error

**Cause**: Your domain not in `ALLOWED_HOSTS`.

**Fix**:
Update environment variable:
```
DJANGO_ALLOWED_HOSTS=yourapp.onrender.com,www.yourdomain.com,yourdomain.com
```

### Getting Help

If errors persist:
1. Check Render logs: Dashboard → Your service → Logs
2. Look for the specific error message
3. Verify all environment variables are set correctly
4. Ensure `DATABASE_URL` passes validation (check logs for ✓ mark)

## Part 6: Custom Domain (Optional)

### 5.1 Add Custom Domain in Render

1. In your web service settings
2. Go to **Custom Domains**
3. Click **Add Custom Domain**
4. Enter: `www.tamipeefarms.com` (your actual domain)

### 5.2 Update DNS Records

In your domain registrar (Namecheap, GoDaddy, etc.):

1. Add CNAME record:
   - **Name**: `www`
   - **Value**: `tamipee-farms.onrender.com` (your Render URL)
   - **TTL**: Automatic or 3600

2. For root domain (`tamipeefarms.com`), add:
   - **A Record** pointing to Render's IP (shown in Render dashboard)
   - Or **CNAME** from `@` to `www.tamipeefarms.com`

3. Wait for DNS propagation (5 minutes to 48 hours)

### 5.3 Update Environment Variables

Add your custom domain to:
```env
DJANGO_ALLOWED_HOSTS=www.tamipeefarms.com,tamipeefarms.com,tamipee-farms.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://www.tamipeefarms.com,https://tamipeefarms.com
```

## Part 6: Monitoring & Maintenance

### 6.1 View Logs

- Render Dashboard → Your Service → **Logs** tab
- Real-time logs of all requests and errors

### 6.2 Monitor Database Usage

- Render Dashboard → PostgreSQL Database → **Metrics**
- Free tier: 1 GB storage limit
- Consider upgrading when approaching limit

### 6.3 Automatic Deploys

Render auto-deploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Update feature X"
git push origin main

# Render automatically rebuilds and deploys
```

### 6.4 Manual Deploy

In Render dashboard:
- Your Service → **Manual Deploy** → **Deploy latest commit**

## Troubleshooting

### Build Fails

**Check**:
1. `build.sh` has Unix line endings (not Windows CRLF)
   ```bash
   # Convert line endings (run locally before pushing)
   dos2unix build.sh
   ```
2. All packages in `requirements.txt` are available

### Database Connection Error

**Check**:
1. `DATABASE_URL` is set correctly
2. Database is in "Available" status
3. Web service and database are in same region

### Static Files Not Loading

**Check**:
1. WhiteNoise is installed: `pip freeze | grep whitenoise`
2. `STATIC_ROOT` is set in settings.py
3. `python manage.py collectstatic` ran in build.sh

### Paystack Payment Fails

**Check**:
1. Using LIVE keys (not test keys) in production
2. Paystack account is activated and verified
3. CSRF_TRUSTED_ORIGINS includes your domain with `https://`

### Email Not Sending

**Check**:
1. Gmail App Password is correct (not regular password)
2. 2FA is enabled on Gmail account
3. "Less secure app access" is NOT needed (app passwords bypass this)

### 500 Server Error

**Check Render logs**:
1. Render Dashboard → Logs
2. Look for Python tracebacks
3. Common issues:
   - Missing environment variable
   - Database migration not run
   - Import error from missing package

## Security Checklist

Before going live with real customer data:

- [ ] `DJANGO_DEBUG=False` in production
- [ ] New random `DJANGO_SECRET_KEY` (not from development)
- [ ] Using Paystack **LIVE** keys (pk_live_... and sk_live_...)
- [ ] HTTPS is enforced (automatic on Render)
- [ ] `.env` file is NOT in git repository
- [ ] Database backups enabled (Render paid plan)
- [ ] Gmail App Password (not regular password)
- [ ] All `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` updated

## Cost Estimate

### Render Free Tier (Development/Testing)
- Web Service: Free
- PostgreSQL: Free (1GB)
- **Limitations**:
  - Sleeps after 15 min inactivity (wakes on request)
  - 750 hours/month
  - Best for testing

### Render Paid (Production)
- Starter Web Service: $7/month (always on)
- Starter PostgreSQL: $7/month (25GB)
- **Total**: ~$14/month
- No sleep, faster performance, backups

## Support

If you encounter issues:

1. Check Render logs first
2. Review this guide's Troubleshooting section
3. Render Docs: https://render.com/docs
4. Django Docs: https://docs.djangoproject.com

---

**Congratulations!** Your Tamipee Integrated Farms application is now live! 🎉

Remember to:
- Monitor logs regularly
- Keep dependencies updated
- Back up database (Render paid plan)
- Test payment flow before announcing to customers
