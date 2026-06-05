# Tamipee Integrated Farms — Feature Checklist
_Last updated: June 2026 | Django 6.0.5 | SQLite_

---

## Public Site (No Login Required)

### Pages
- [x] Homepage — hero, stats bar, promotional banners (admin-managed), featured products, testimonials (admin-managed), Why Choose Us, CTA
- [x] Shop / Product list — browse all available products
- [x] Product detail page — image, price, unit, stock status, Add to Cart, Wishlist toggle
- [x] About page — mission, livestock categories, location map, FAQs (admin-managed)
- [x] Contact page — contact form (name, email, phone, message)

### Navigation & UX
- [x] Sticky top navbar with brand logo
- [x] Cart icon with live item-count badge (logged-in users)
- [x] User dropdown showing name, email, role badge
- [x] Site-wide announcement bar (admin-managed, dismissible per visit)
- [x] Flash messages (auto-dismiss after 5 s)
- [x] Scroll-to-top button
- [x] Responsive / mobile-stack tables
- [x] Footer with quick links, product links, hard-coded contact info

### Product Discovery
- [x] Search by name, description, species, category
- [x] Filter by livestock category
- [x] Filter by species
- [x] Filter by stock status (in stock only)
- [x] Sort by newest / price asc / price desc / name A-Z
- [x] Out-of-Stock badge + disabled Add-to-Cart button
- [x] Breadcrumb navigation on product detail

### Marketing / Newsletter
- [x] Newsletter subscription form (duplicate email prevented)
- [x] Newsletter subscriber list (admin-visible)
- [ ] Newsletter sending / bulk email (not implemented — collection only)

---

## Customer Features (Login Required)

### Account Management
- [x] Register (username, email, optional phone/address, password)
- [x] Login / logout (session-based)
- [x] Profile update — first/last name, email, phone, address, profile picture
- [x] Password reset via email link (enter email → confirm new password)

### Cart
- [x] Add product to cart (with stock validation & max-quantity enforcement)
- [x] View cart with subtotals and running total
- [x] Update item quantity in cart
- [x] Remove item from cart
- [ ] Guest / session cart (login required to access cart)

### Checkout & Orders
- [x] Checkout form — delivery address, phone, optional notes
- [x] Promotions applied automatically (% discount, date-range controlled)
- [x] Stock re-validation at checkout submission
- [x] Order confirmation email sent to customer after checkout
- [x] Full order history with status badges
- [x] Order detail page — items, quantities, unit prices, subtotals, total, delivery info, notes
- [ ] No tax / delivery fee calculation
- [ ] No order-change or cancellation by customer

### Wishlist
- [x] Toggle add/remove wishlist from product detail page
- [x] Dedicated wishlist dashboard page — product cards with Add to Cart and Remove
- [x] Unique constraint (same product cannot be added twice)

### Customer Dashboard
- [x] Overview — total orders count, recent-orders table (last 5), wishlist link
- [x] Quick-action buttons (Shop, Cart, All Orders, Edit Profile)
- [x] Full orders list (`/dashboard/customer/orders/`)

### Payments
- [x] Paystack payment initiation (unique reference per order)
- [x] Paystack inline popup (card, bank transfer, USSD)
- [x] Server-side payment verification after callback
- [x] Payment success / failed pages
- [x] Automatic order confirmation on successful webhook
- [ ] Refunds / payment reversal
- [ ] Order-level payment retry if failed

---

## Staff Dashboard (Role: Staff)

- [x] Staff dashboard overview — livestock category count, pending orders count
- [x] View livestock categories and species
- [x] View feed schedules
- [x] View all orders (staff orders view)
- [x] Update order status (Pending → Confirmed → Processing → Shipped → Delivered / Cancelled)
- [x] Automatic inventory deduction when order confirmed; release when cancelled
- [x] Add / edit livestock species (`/dashboard/admin/livestock/species/`)
- [x] Add / edit feed schedules
- [x] Add / edit growth boosters
- [x] Add / edit seasonal variations
- [x] Daily feed log — record date, species, feed type, bags consumed, notes
- [x] Daily production log — date, species, product name, quantity, unit; egg-specific: egg_count, damaged_count
- [x] Delete feed log entries
- [x] Delete production log entries

---

## Admin Dashboard (Role: Admin / Superuser)

### Overview & Navigation
- [x] Summary stats — total users, orders, products, livestock species, pending orders
- [x] Recent-orders table with quick status dropdown
- [x] Pending-orders count badge
- [x] Quick-action shortcuts (Add Product, Add Livestock, Add Feed Schedule, Add Growth Booster, Add Staff, Post Announcement)

### User Management
- [x] View all users ordered by join date
- [x] Add staff accounts (username, name, email, phone, password)
- [x] Change user roles (Admin / Staff / Customer)
- [x] Superuser role locked to Admin (cannot be downgraded)

### Order & Payment Management
- [x] View all orders — customer, amount, date, status
- [x] Change order status inline
- [x] View all payment records — reference, amount, status, Paystack response JSON

### Reporting & Analytics
- [x] Revenue dashboard — total revenue (successful payments), total orders, total customers
- [x] Egg production metrics (30-day) — collected, damaged, saleable, estimated trays
- [x] Egg sales analytics — revenue from egg products, units sold, order count, current stock
- [x] 7-day egg production trend chart (Chart.js)
- [x] Orders vs. customers summary chart

### Livestock & Farm Management
- [x] Livestock categories — create, edit, delete (with images)
- [x] Livestock species — create, edit, delete (name, breed, description, image, current stock)
- [x] Feed schedules — feed type, daily qty (kg), feeding times, cost/kg, season, notes
- [x] Growth boosters — supplement name/type, dosage, frequency, expected impact, cost/unit
- [x] Seasonal variations — season, production impact, recommended actions, expected yield % change
- [x] Daily feed log — same as Staff (above)
- [x] Daily production log — same as Staff (above)

### Product Management
- [x] Create products — name, description, price, unit, stock, image, availability, featured flag
- [x] Link product to livestock species
- [x] Edit products
- [x] Delete products (hard delete — no soft delete / undo)
- [x] Toggle `is_featured` flag to control homepage display

### Promotions
- [x] Create promotions — title, description, % discount, linked product, start/end date, active toggle
- [x] Edit promotions
- [x] Delete promotions
- [ ] Bulk promotion tools
- [ ] Promotion preview before publishing

### Site & Marketing Management
- [x] Hero section text editor (SiteContent `hero_text`)
- [x] Site content key/value manager (raw key-value store)
- [x] Banners — upload image, set title, subtitle, CTA link, order, visibility
- [x] Testimonials — add customer name, message, rating (1–5★), image, visibility
- [x] FAQs — question, answer, display order, visibility
- [x] Contact info fields (viewed via Manage Pages, stored in SiteContent)
- [x] Announcements — title, body, visibility (shown site-wide as dismissible bar)
- [x] Newsletter subscriber list (view only, active subscribers)
- [x] Contact messages inbox — list all received messages, auto-mark as read on view
- [ ] Contact info edit form (currently read-only preview; edit via raw Manage Pages)
- [ ] Newsletter broadcast / send emails to subscribers

---

## Content Visibility Matrix

| Content Type | Admin Can Manage | Shows on Public Site |
|---|---|---|
| Announcements | ✅ Create / delete | ✅ Site-wide top bar (all pages) |
| Banners | ✅ Create / delete | ✅ Homepage carousel |
| Testimonials | ✅ Create / delete | ✅ Homepage section |
| Featured Products | ✅ `is_featured` flag | ✅ Homepage product grid |
| FAQs | ✅ Create / delete | ✅ About page accordion |
| Hero text (`hero_text`) | ✅ Edit via Manage Pages | ⚠️ Stored in DB, not yet rendered in homepage hero |
| Contact info (`contact_phone` etc.) | ⚠️ Edit via raw Manage Pages | ⚠️ Footer / Contact page use hard-coded values |

---

## Known Gaps & Future Work

### Missing Features
- [ ] Guest/session cart (no login needed to browse + checkout)
- [ ] Customer-initiated order cancellation
- [ ] Refund / payment reversal workflow
- [ ] Customer notifications (email or on-site) when order status changes
- [ ] Low-stock alerts for staff/admin
- [ ] Customer product reviews / ratings
- [ ] Livestock stock record UI (`LivestockRecord` model exists but has no routes/forms)
- [ ] Live-animal sales UX (currently treated same as packaged products)
- [ ] Order tracking page with status timeline for customers
- [ ] Shipping fee / tax calculation
- [ ] Pagination on admin livestock, feed logs, and production logs
- [ ] Soft delete / audit trail for products, categories, species

### Security / Access Control
- [ ] `livestock/add`, `livestock/edit`, `livestock/delete` routes accessible to ANY logged-in user (should be Staff/Admin only)
- [ ] Contact info edit form is not functional (read-only display; editor redirects to raw key-value page)

### Performance
- [ ] N+1 query on cart context processor (1 query per page for every authenticated user)
- [ ] N+1 queries on admin livestock template (nested loops without `prefetch_related`)
- [ ] Checkout runs promotion query twice per cart item
- [ ] No database indices on `Order.status`, `Product.is_available`, date fields
- [ ] No caching strategy (Redis / Memcached not configured)
- [ ] Payment confirmation UX: verify page redirects to success after a 3-second delay regardless of actual webhook outcome

### Production Readiness
- [ ] SQLite → PostgreSQL migration needed before production use
- [ ] Paystack keys must be set via environment variables (currently fall back to placeholder strings)
- [ ] Email credentials must be environment variables (currently checked from env but no `.env` file provided)
- [ ] `DEBUG=True` default — must be overridden in production via `DJANGO_DEBUG=False`
- [ ] Static file serving via `collectstatic` + whitenoise / nginx required for production

---

## Quick URL Reference

| URL | Who | What |
|---|---|---|
| `/` | Public | Homepage |
| `/products/` | Public | Product catalogue |
| `/products/<pk>/` | Public | Product detail |
| `/about/` | Public | About + FAQ |
| `/contact/` | Public | Contact form |
| `/accounts/register/` | Public | Register |
| `/accounts/login/` | Public | Login |
| `/cart/` | Customer | Cart |
| `/checkout/` | Customer | Checkout |
| `/orders/` | Customer | Order history |
| `/orders/<pk>/` | Customer | Order detail |
| `/payments/initiate/` | Customer | Start Paystack payment |
| `/payments/callback/` | System | Paystack webhook |
| `/accounts/profile/` | Customer | Edit profile |
| `/dashboard/customer/` | Customer | Customer dashboard |
| `/dashboard/customer/wishlist/` | Customer | Wishlist |
| `/dashboard/staff/` | Staff | Staff dashboard |
| `/dashboard/admin/` | Admin | Admin overview |
| `/dashboard/admin/orders/` | Admin | All orders |
| `/dashboard/admin/payments/` | Admin | Payment records |
| `/dashboard/admin/reports/` | Admin | Analytics & reports |
| `/dashboard/admin/livestock/` | Admin/Staff | Livestock management |
| `/dashboard/admin/daily-log/` | Admin/Staff | Daily feed & production logs |
| `/dashboard/admin/site/` | Admin | Site content hub |
| `/dashboard/admin/marketing/` | Admin | Marketing hub |
| `/dashboard/admin/users/` | Admin | User management |
| `/admin/` | Superuser | Django built-in admin |
