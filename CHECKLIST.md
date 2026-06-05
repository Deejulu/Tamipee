# Pre-Deployment Checklist

Complete this checklist before pushing to GitHub and deploying to Render.

## ✅ Local Development Setup

- [ ] Virtual environment created and activated
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file created from `.env.example`
- [ ] `.env` file contains your actual credentials (Paystack test keys, Gmail)
- [ ] Database migrations run: `python manage.py migrate`
- [ ] Superuser created: `python manage.py createsuperuser`
- [ ] Local server runs without errors: `python manage.py runserver`
- [ ] Admin dashboard accessible at http://127.0.0.1:8000/admin/

## ✅ Security Check

- [ ] `.env` file is listed in `.gitignore`
- [ ] `.env` file is NOT tracked by git (run `git status` to verify)
- [ ] Database file `db.sqlite3` is in `.gitignore`
- [ ] `media/` folder is in `.gitignore`
- [ ] `staticfiles/` folder is in `.gitignore`
- [ ] No sensitive credentials in any `.py` files
- [ ] `DJANGO_SECRET_KEY` in `.env` is different from production (you'll generate new one for Render)

## ✅ GitHub Preparation

- [ ] GitHub account created
- [ ] Git initialized in project folder: `git init`
- [ ] All files staged: `git add .`
- [ ] Initial commit made: `git commit -m "Initial commit"`
- [ ] GitHub repository created (public or private)
- [ ] Remote origin added: `git remote add origin https://github.com/USERNAME/REPO.git`
- [ ] Code pushed to GitHub: `git push -u origin main`

## ✅ Render Account Setup

- [ ] Render account created at https://render.com
- [ ] GitHub account connected to Render
- [ ] Payment method added (even for free tier, may be required)

## ✅ Production Credentials Ready

### Paystack (LIVE Keys)
- [ ] Paystack account fully activated
- [ ] Business verification completed
- [ ] LIVE API keys obtained from dashboard.paystack.com/#/settings/developer
- [ ] Test transaction completed successfully
- [ ] `pk_live_...` public key ready
- [ ] `sk_live_...` secret key ready

### Gmail (App Password)
- [ ] Gmail account to use for farm emails identified
- [ ] 2-Factor Authentication enabled on Gmail account
- [ ] App Password generated at https://myaccount.google.com/apppasswords
- [ ] 16-character app password copied and saved securely

### Django Secret Key
- [ ] New production secret key generated (different from `.env`):
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

## ✅ Deployment Files Ready

- [ ] `requirements.txt` includes all production dependencies
- [ ] `build.sh` exists and is executable
- [ ] `runtime.txt` specifies Python version
- [ ] `.env.example` is up-to-date
- [ ] `README.md` has clear instructions
- [ ] `DEPLOYMENT.md` reviewed

## ✅ Database Setup on Render

- [ ] PostgreSQL database created on Render
- [ ] Database name noted
- [ ] Internal Database URL copied
- [ ] Database is in "Available" status

## ✅ Web Service Configuration on Render

- [ ] Web service created and connected to GitHub repo
- [ ] Build command set to: `./build.sh`
- [ ] Start command set to: `gunicorn tamipee.wsgi:application`
- [ ] Python 3 runtime selected
- [ ] Region matches database region

## ✅ Environment Variables Set on Render

- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_SECRET_KEY=<new-production-key>`
- [ ] `DJANGO_ALLOWED_HOSTS=your-app.onrender.com`
- [ ] `DJANGO_CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com`
- [ ] `DATABASE_URL=<postgres-internal-url>`
- [ ] `PAYSTACK_PUBLIC_KEY=pk_live_...`
- [ ] `PAYSTACK_SECRET_KEY=sk_live_...`
- [ ] `EMAIL_HOST_USER=<your-gmail>`
- [ ] `EMAIL_HOST_PASSWORD=<app-password>`
- [ ] `DEFAULT_FROM_EMAIL=Tamipee Integrated Farms <your-gmail>`
- [ ] All security variables set (SSL_REDIRECT, COOKIE_SECURE, etc.)

## ✅ Post-Deployment Verification

- [ ] Build completed successfully (check Render logs)
- [ ] No errors in deployment logs
- [ ] Site accessible at https://your-app.onrender.com
- [ ] Homepage loads correctly
- [ ] Static files (CSS/JS) loading
- [ ] Admin panel accessible at `/admin/`
- [ ] Superuser created via Render shell
- [ ] Can login to admin panel
- [ ] Sample data populated (optional)

## ✅ Functionality Testing

- [ ] User registration works
- [ ] User login/logout works
- [ ] Products page displays correctly
- [ ] Add to cart functionality works
- [ ] Checkout page loads
- [ ] Paystack payment integration works (test mode first!)
- [ ] Order confirmation received
- [ ] Email notifications sending
- [ ] Admin dashboard accessible
- [ ] Staff functions work correctly

## ✅ Payment Testing (CRITICAL!)

### Test Mode First
- [ ] Set Paystack TEST keys temporarily
- [ ] Place test order
- [ ] Use test card: 4084 0840 8408 4081
- [ ] Verify payment completes
- [ ] Check order in admin panel
- [ ] Verify customer receives confirmation email

### Live Mode
- [ ] Switch to Paystack LIVE keys
- [ ] Redeploy with live keys
- [ ] Place small real transaction to verify
- [ ] Verify funds arrive in Paystack dashboard
- [ ] Test refund process if needed

## ✅ Performance & Security

- [ ] HTTPS enforced (automatic on Render)
- [ ] All external links use HTTPS
- [ ] No mixed content warnings
- [ ] Page load times acceptable (< 3 seconds)
- [ ] Mobile responsive design works
- [ ] Forms have CSRF protection
- [ ] SQL injection protection (Django ORM handles this)
- [ ] XSS protection enabled

## ✅ Documentation

- [ ] README.md updated with correct URLs
- [ ] DEPLOYMENT.md reviewed and accurate
- [ ] Team members know how to access admin panel
- [ ] Backup procedures documented
- [ ] Support contact information updated

## ✅ Monitoring Setup

- [ ] Render email notifications enabled
- [ ] Critical error alerts configured
- [ ] Uptime monitoring set up (optional: UptimeRobot)
- [ ] Database usage monitored
- [ ] Payment transaction logs reviewed regularly

## 🎯 Ready to Launch!

When all checkboxes above are complete:

1. Announce to team
2. Share URLs with stakeholders
3. Monitor logs for first 24 hours
4. Be ready to respond to customer inquiries
5. Celebrate your successful deployment! 🎉

---

## Quick Reference Links

- **Your Site**: https://your-app.onrender.com
- **Admin Panel**: https://your-app.onrender.com/admin/
- **Render Dashboard**: https://dashboard.render.com
- **Paystack Dashboard**: https://dashboard.paystack.com
- **GitHub Repo**: https://github.com/USERNAME/REPO

## Need Help?

Refer to:
- `README.md` - General overview and setup
- `DEPLOYMENT.md` - Detailed step-by-step deployment guide
- Render Docs: https://render.com/docs
- Django Docs: https://docs.djangoproject.com
- Paystack Docs: https://paystack.com/docs
