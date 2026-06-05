# Tamipee Integrated Farms

A comprehensive Django-based farm management and e-commerce platform for livestock, feed, and farm product sales.

## 🌟 Features

### Farm Management
- **Livestock Tracking**: Manage multiple species (layers, pullets, cockerels, turkeys, catfish)
- **Feed Schedules**: Track daily feeding routines and costs
- **Growth Boosters**: Monitor supplements and performance enhancers
- **Seasonal Variations**: Adapt farm operations to dry/rainy seasons
- **Daily Logs**: Record feed consumption and production (eggs, weight gain)

### E-Commerce Store
- **Product Catalog**: Sell live birds, fish, eggs, and farm supplies
- **Shopping Cart**: Full-featured cart with inventory validation
- **Secure Checkout**: Paystack payment integration
- **Order Management**: Track orders from placement to delivery
- **Promotions & Discounts**: Time-limited sales campaigns
- **Wishlist**: Save favorite products

### User Roles & Permissions
- **Admin**: Full system access and configuration
- **Staff**: Farm operations and order processing
- **Customer**: Shopping and order tracking

### Security & Performance
- Role-based access control with custom decorators
- Transaction-safe checkout with race condition protection
- Database indexes on high-traffic queries
- Input validation (phone numbers, addresses, dates)
- CSRF and HTTPS protection in production

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.12+
- Git
- Virtual environment support

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/tamipee-integrated-farms.git
cd tamipee-integrated-farms
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your credentials:
# - DJANGO_SECRET_KEY (generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
# - PAYSTACK_PUBLIC_KEY and PAYSTACK_SECRET_KEY (test keys from dashboard.paystack.com)
# - EMAIL_HOST_USER and EMAIL_HOST_PASSWORD (Gmail app password)
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Load sample data (optional)**
```bash
python manage.py populate_sample
```

8. **Run development server**
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to see your site!

## 📦 Deployment to Render

### Prerequisites
- Render account (https://render.com)
- GitHub repository with your code
- Paystack account for payment processing

### Step-by-Step Deployment

1. **Push code to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/tamipee-integrated-farms.git
git push -u origin main
```

2. **Create Web Service on Render**
   - Go to https://dashboard.render.com/
   - Click **New +** → **Web Service**
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `tamipee-farms` (or your preferred name)
     - **Region**: Choose closest to your users
     - **Branch**: `main`
     - **Runtime**: `Python 3`
     - **Build Command**: `./build.sh`
     - **Start Command**: `gunicorn tamipee.wsgi:application`
     - **Instance Type**: Free (or paid for production)

3. **Add Environment Variables**
   In Render dashboard, go to **Environment** and add:

   ```
   DJANGO_DEBUG=False
   DJANGO_SECRET_KEY=<generate-new-random-key>
   DJANGO_ALLOWED_HOSTS=your-app.onrender.com
   DJANGO_CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com
   
   # Paystack (LIVE keys for production!)
   PAYSTACK_PUBLIC_KEY=pk_live_your_live_public_key
   PAYSTACK_SECRET_KEY=sk_live_your_live_secret_key
   
   # Email (SendGrid)
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=your-sendgrid-api-key
   DEFAULT_FROM_EMAIL=Tamipee Integrated Farms <verified-sender@yourdomain.com>
   
   # Security
   DJANGO_SECURE_SSL_REDIRECT=True
   DJANGO_SESSION_COOKIE_SECURE=True
   DJANGO_CSRF_COOKIE_SECURE=True
   ```

4. **Create PostgreSQL Database**
   - In Render dashboard: **New +** → **PostgreSQL**
   - Name: `tamipee-db`
   - Copy the **Internal Database URL**
   - Add to your web service environment variables:
     ```
     DATABASE_URL=<paste-internal-database-url>
     ```

5. **Deploy**
   - Click **Create Web Service**
   - Render will automatically build and deploy
   - Monitor the logs for any errors
   - Your site will be live at: `https://your-app.onrender.com`

6. **Create Superuser in Production**
   ```bash
   # In Render dashboard, go to Shell and run:
   python manage.py createsuperuser
   ```

7. **Load Sample Data (Optional)**
   ```bash
   # In Render Shell:
   python manage.py populate_sample
   ```

### Post-Deployment Checklist
- ✅ Visit `/admin/` and verify superuser login
- ✅ Test Paystack checkout with test card: `4084 0840 8408 4081` (expires any future date)
- ✅ Verify email notifications are sending
- ✅ Check all pages load without errors
- ✅ Test user registration and login
- ✅ Place a test order and confirm payment flow

## 🗂️ Project Structure

```
tamipee-integrated-farms/
├── accounts/          # User authentication and profiles
├── dashboard/         # Admin, staff, and customer dashboards
├── livestock/         # Farm management (species, feeds, boosters)
├── store/             # E-commerce (products, cart, orders)
├── payments/          # Paystack integration
├── templates/         # HTML templates
├── static/            # CSS, JS, images
├── media/             # User uploads (profile pics, product images)
├── tamipee/           # Project settings
├── manage.py
├── requirements.txt
├── build.sh           # Render build script
├── .env.example       # Environment variables template
└── README.md
```

## 🛠️ Tech Stack

- **Backend**: Django 6.0.5
- **Database**: SQLite (dev), PostgreSQL (production)
- **Frontend**: Bootstrap 5, Crispy Forms
- **Payments**: Paystack
- **Email**: Gmail SMTP
- **Deployment**: Render.com, Gunicorn, WhiteNoise

## 📝 Environment Variables Reference

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DJANGO_DEBUG` | Debug mode (True/False) | `False` | Yes |
| `DJANGO_SECRET_KEY` | Django secret key | `random-50-char-string` | Yes |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts | `yoursite.com,www.yoursite.com` | Yes |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF | `https://yoursite.com` | Yes |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` | Production |
| `PAYSTACK_PUBLIC_KEY` | Paystack public key | `pk_live_...` | Yes |
| `PAYSTACK_SECRET_KEY` | Paystack secret key | `sk_live_...` | Yes |
| `EMAIL_HOST_USER` | Gmail address | `farm@gmail.com` | Yes |
| `EMAIL_HOST_PASSWORD` | Gmail app password | `16-char-password` | Yes |

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

Run specific test modules:
```bash
python manage.py test store.tests
python manage.py test dashboard.tests
```

## 📚 Management Commands

### Sample Data
```bash
# Populate database with realistic sample data
python manage.py populate_sample

# Delete all sample data
python manage.py delete_sample
```

### Standard Django Commands
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Create admin user
python manage.py createsuperuser
```

## 🔐 Security Notes

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use LIVE Paystack keys in production** - Test keys only for development
3. **Generate new SECRET_KEY for production** - Don't reuse development key
4. **Enable HTTPS in production** - Automatically handled by Render
5. **Use Gmail App Passwords** - Not your regular Gmail password

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software for Tamipee Integrated Farms.

## 📞 Support

For issues and questions:
- **Email**: support@tamipeefarms.com
- **Issues**: https://github.com/yourusername/tamipee-integrated-farms/issues

## 🎯 Roadmap

- [ ] Guest checkout system
- [ ] SMS notifications via Twilio
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Multi-currency support
- [ ] Automated inventory forecasting
- [ ] WhatsApp Business integration

---

Built with ❤️ by Tamipee Integrated Farms Team
