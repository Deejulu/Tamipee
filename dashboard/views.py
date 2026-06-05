from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from accounts.models import CustomUser
from accounts.forms import StaffRegistrationForm
from accounts.decorators import role_required
from livestock.models import LivestockCategory, LivestockSpecies, FeedSchedule, GrowthBooster, SeasonalVariation, DailyFeedLog, DailyProductionLog
from livestock.forms import LivestockCategoryForm, LivestockSpeciesForm, FeedScheduleForm, GrowthBoosterForm, SeasonalVariationForm, DailyFeedLogForm, DailyProductionLogForm
from store.models import Product, Order, OrderItem, Newsletter, Banner, Testimonial, FAQ, Promotion, Announcement, SiteContent, ContactMessage
from store.forms import ProductForm, BannerForm, TestimonialForm, FAQForm, PromotionForm, AnnouncementForm, SiteContentForm


def _egg_product_filter(prefix=''):
    return (
        Q(**{f'{prefix}name__icontains': 'egg'}) |
        Q(**{f'{prefix}unit__in': ['dozen', 'tray', 'crate']}) |
        Q(**{f'{prefix}livestock_species__name__icontains': 'layer'})
    )


def _egg_log_filter():
    return Q(product__icontains='egg') | Q(egg_count__isnull=False) | Q(species__name__icontains='layer')


def _build_egg_metrics(logs):
    collected = 0
    damaged = 0
    saleable = 0
    for log in logs:
        if log.egg_count is None:
            continue
        collected += log.egg_count
        damaged += log.damaged_count
        saleable += log.saleable_quantity
    return {
        'collected': collected,
        'damaged': damaged,
        'saleable': saleable,
        'trays': round(saleable / 30, 1) if saleable else 0,
    }


def _paginate_queryset(request, queryset, per_page=12):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def _send_order_status_email(order):
    if not order.user.email:
        return

    send_mail(
        subject=f'Order #{order.pk} status updated - Tamipee Integrated Farms',
        message=(
            f'Hi {order.user.first_name or order.user.username},\n\n'
            f'Your order #{order.pk} is now marked as "{order.get_status_display()}".\n\n'
            f'Total: ₦{order.total_amount}\n'
            f'Delivery Address: {order.delivery_address}\n\n'
            f'Thank you for shopping with Tamipee Integrated Farms.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )


# role_required moved to accounts.decorators for reusability


# ── Main Dashboards ──────────────────────────────────────────────────────────

@role_required('admin')
def admin_dashboard(request):
    from payments.models import Payment as PaymentModel
    today = timezone.localdate()
    total_revenue = sum(p.amount for p in PaymentModel.objects.filter(status='success'))
    context = {
        'total_users': CustomUser.objects.count(),
        'total_orders': Order.objects.count(),
        'total_products': Product.objects.count(),
        'total_livestock': LivestockSpecies.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'recent_orders': Order.objects.select_related('user').order_by('-created_at')[:6],
        'total_revenue': total_revenue,
        'total_customers': CustomUser.objects.filter(role='customer').count(),
        'new_users_today': CustomUser.objects.filter(date_joined__date=today).count(),
        'orders_today': Order.objects.filter(created_at__date=today).count(),
        'delivered_orders': Order.objects.filter(status='delivered').count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
    }
    return render(request, 'dashboard/admin.html', context)


@role_required('staff')
def staff_dashboard(request):
    context = {
        'livestock_categories': LivestockCategory.objects.all(),
        'recent_orders': Order.objects.filter(status='pending').order_by('-created_at')[:10],
    }
    return render(request, 'dashboard/staff.html', context)


@login_required
def customer_dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'dashboard/customer.html', {'orders': orders})


# ── Admin: User Management ────────────────────────────────────────────────────

@role_required('admin')
def admin_users(request):
    qs = CustomUser.objects.all().order_by('-date_joined')
    search = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    if search:
        qs = qs.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search)
        )
    if role_filter == 'superuser':
        qs = qs.filter(is_superuser=True)
    elif role_filter:
        qs = qs.filter(role=role_filter)
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    users = _paginate_queryset(request, qs, per_page=15)
    role_choices = [choice[0] for choice in CustomUser.ROLE_CHOICES]
    context = {
        'users': users,
        'role_choices': role_choices,
        'search': search,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'total_users': CustomUser.objects.count(),
        'total_admins': CustomUser.objects.filter(role='admin').count(),
        'total_staff': CustomUser.objects.filter(role='staff').count(),
        'total_customers': CustomUser.objects.filter(role='customer').count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
    }
    return render(request, 'dashboard/admin_users.html', context)


@role_required('admin')
def admin_user_detail(request, pk):
    from payments.models import Payment as PaymentModel
    target_user = get_object_or_404(CustomUser, pk=pk)
    user_orders = Order.objects.filter(user=target_user).order_by('-created_at')[:10]
    user_payments = PaymentModel.objects.filter(user=target_user).order_by('-created_at')[:10]
    total_orders = Order.objects.filter(user=target_user).count()
    total_spent = sum(p.amount for p in PaymentModel.objects.filter(user=target_user, status='success'))
    role_choices = [choice[0] for choice in CustomUser.ROLE_CHOICES]
    context = {
        'target_user': target_user,
        'user_orders': user_orders,
        'user_payments': user_payments,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'role_choices': role_choices,
    }
    return render(request, 'dashboard/admin_user_detail.html', context)


@role_required('admin')
def admin_update_user_role(request, pk):
    user_to_update = get_object_or_404(CustomUser, pk=pk)

    if request.method != 'POST':
        return redirect('dashboard:admin_users')

    new_role = request.POST.get('role')
    valid_roles = [choice[0] for choice in CustomUser.ROLE_CHOICES]

    if new_role not in valid_roles:
        messages.error(request, 'Invalid role selected.')
        return redirect('dashboard:admin_users')

    # Keep role data consistent with Django permissions for superusers.
    if user_to_update.is_superuser and new_role != 'admin':
        if user_to_update.role != 'admin':
            user_to_update.role = 'admin'
            user_to_update.is_staff = True
            user_to_update.save(update_fields=['role', 'is_staff'])
        messages.error(request, 'Superusers must have the Admin role.')
        return redirect('dashboard:admin_users')

    user_to_update.role = new_role
    # Keep Django staff-level access in sync with the app role hierarchy.
    user_to_update.is_staff = new_role in ['admin', 'staff']
    user_to_update.save(update_fields=['role', 'is_staff'])
    messages.success(request, f'Role for {user_to_update.username} updated to {user_to_update.get_role_display()}.')
    return redirect('dashboard:admin_users')


@role_required('admin')
def admin_add_staff(request):
    form = StaffRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Staff account created successfully.')
        return redirect('dashboard:admin_users')
    return render(request, 'dashboard/admin_add_staff.html', {'form': form})


# ── Admin: Order Management ───────────────────────────────────────────────────

@role_required('admin')
def admin_orders(request):
    qs = Order.objects.select_related('user').order_by('-created_at')
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    if search:
        qs = qs.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(phone__icontains=search) |
            Q(delivery_address__icontains=search)
        )
        # Allow searching by order ID if the query is numeric
        if search.lstrip('#').isdigit():
            qs = qs | Order.objects.filter(pk=int(search.lstrip('#'))).select_related('user')
            qs = qs.distinct()
    if status_filter:
        qs = qs.filter(status=status_filter)

    orders = _paginate_queryset(request, qs, per_page=15)
    context = {
        'orders': orders,
        'search': search,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
        'pending_count': Order.objects.filter(status='pending').count(),
        'processing_count': Order.objects.filter(status__in=['confirmed', 'processing']).count(),
        'shipped_count': Order.objects.filter(status='shipped').count(),
        'delivered_count': Order.objects.filter(status='delivered').count(),
        'cancelled_count': Order.objects.filter(status='cancelled').count(),
    }
    return render(request, 'dashboard/admin_orders.html', context)


@role_required('admin', 'staff')
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
        if new_status in valid_statuses:
            previous_status = order.status
            low_stock_products = []
            if new_status == 'cancelled' and previous_status != 'cancelled':
                order.release_inventory()
            elif new_status in ['confirmed', 'processing', 'shipped', 'delivered'] and not order.inventory_applied:
                try:
                    order.apply_inventory()
                    low_stock_products = [
                        item.product.name
                        for item in order.items.select_related('product')
                        if item.product.stock_quantity <= 5
                    ]
                except ValueError as exc:
                    messages.error(request, str(exc))
                    return redirect(request.META.get('HTTP_REFERER', 'dashboard:admin_orders'))

            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])
            if previous_status != new_status:
                _send_order_status_email(order)
            messages.success(request, f'Order #{order.pk} updated to "{order.get_status_display()}".')
            if low_stock_products:
                messages.warning(
                    request,
                    f'Low stock alert: {", ".join(low_stock_products)} now has 5 or fewer units remaining.'
                )
        else:
            messages.error(request, 'Invalid status.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:admin_orders'))


# ── Admin: Payment Management ─────────────────────────────────────────────────

@role_required('admin')
def admin_payments(request):
    from payments.models import Payment as PaymentModel
    qs = PaymentModel.objects.select_related('user', 'order').order_by('-created_at')
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    if search:
        qs = qs.filter(
            Q(reference__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )
    if status_filter:
        qs = qs.filter(status=status_filter)

    payments = _paginate_queryset(request, qs, per_page=15)
    all_pay = PaymentModel.objects.all()
    total_revenue = sum(p.amount for p in all_pay.filter(status='success'))
    total_pending_amount = sum(p.amount for p in all_pay.filter(status='pending'))
    context = {
        'payments': payments,
        'search': search,
        'status_filter': status_filter,
        'total_revenue': total_revenue,
        'total_pending_amount': total_pending_amount,
        'success_count': all_pay.filter(status='success').count(),
        'pending_count': all_pay.filter(status='pending').count(),
        'failed_count': all_pay.filter(status='failed').count(),
    }
    return render(request, 'dashboard/admin_payments.html', context)


# ── Admin: Reports ────────────────────────────────────────────────────────────

@role_required('admin')
def admin_reports(request):
    from payments.models import Payment as PaymentModel
    today = timezone.localdate()
    egg_window_start = today - timedelta(days=29)
    total_revenue = sum(p.amount for p in PaymentModel.objects.filter(status='success'))

    egg_logs = list(
        DailyProductionLog.objects.filter(_egg_log_filter(), date__gte=egg_window_start)
        .select_related('species')
        .order_by('date', 'created_at')
    )
    egg_metrics = _build_egg_metrics(egg_logs)

    egg_sales_items = list(
        OrderItem.objects.filter(_egg_product_filter('product__'))
        .select_related('product', 'order')
    )
    fulfilled_egg_sales = [item for item in egg_sales_items if item.order.status != 'cancelled']
    egg_sales_revenue = sum(item.subtotal for item in fulfilled_egg_sales)
    egg_units_sold = sum(item.quantity for item in fulfilled_egg_sales)
    egg_order_count = len({item.order_id for item in fulfilled_egg_sales})
    egg_stock_units = sum(Product.objects.filter(_egg_product_filter(), is_available=True).values_list('stock_quantity', flat=True))

    trend_map = {}
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        trend_map[day] = 0
    for log in egg_logs:
        if log.date in trend_map and log.egg_count is not None:
            trend_map[log.date] += log.saleable_quantity

    context = {
        'total_revenue': total_revenue,
        'total_orders': Order.objects.count(),
        'total_customers': CustomUser.objects.filter(role='customer').count(),
        'egg_metrics': egg_metrics,
        'egg_sales_revenue': egg_sales_revenue,
        'egg_units_sold': egg_units_sold,
        'egg_order_count': egg_order_count,
        'egg_stock_units': egg_stock_units,
        'egg_production_labels': [day.strftime('%d %b') for day in trend_map.keys()],
        'egg_production_values': list(trend_map.values()),
    }
    return render(request, 'dashboard/admin_reports.html', context)


# ── Admin: Site Management Hub ───────────────────────────────────────────────

@role_required('admin')
def admin_site_management(request):
    return render(request, 'dashboard/admin_site_management.html')


# ── Admin: Marketing Hub ─────────────────────────────────────────────────────

@role_required('admin')
def admin_marketing(request):
    return render(request, 'dashboard/admin_marketing.html')


# ── Admin: Hero / Pages / Banners / Testimonials / FAQs / Contact ────────────

@role_required('admin')
def admin_manage_hero(request):
    hero_content, _ = SiteContent.objects.get_or_create(key='hero_text', defaults={'value': ''})
    form = SiteContentForm(request.POST or None, instance=hero_content)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Hero section updated.')
        return redirect('dashboard:admin_manage_hero')
    return render(request, 'dashboard/admin_manage_hero.html', {'form': form})


@role_required('admin')
def admin_manage_pages(request):
    contents = SiteContent.objects.all()
    return render(request, 'dashboard/admin_manage_pages.html', {'contents': contents})


@role_required('admin')
def admin_manage_banners(request):
    banners = Banner.objects.all()
    form = BannerForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Banner added.')
        return redirect('dashboard:admin_manage_banners')
    return render(request, 'dashboard/admin_manage_banners.html', {'banners': banners, 'form': form})


@role_required('admin')
def admin_manage_testimonials(request):
    testimonials = Testimonial.objects.all()
    form = TestimonialForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Testimonial added.')
        return redirect('dashboard:admin_manage_testimonials')
    return render(request, 'dashboard/admin_manage_testimonials.html', {'testimonials': testimonials, 'form': form})


@role_required('admin')
def admin_manage_faqs(request):
    faqs = FAQ.objects.all()
    form = FAQForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'FAQ added.')
        return redirect('dashboard:admin_manage_faqs')
    return render(request, 'dashboard/admin_manage_faqs.html', {'faqs': faqs, 'form': form})


@role_required('admin')
def admin_manage_contact_info(request):
    fields = ['contact_phone', 'contact_email', 'contact_address']
    contents = {c.key: c for c in SiteContent.objects.filter(key__in=fields)}
    return render(request, 'dashboard/admin_manage_contact_info.html', {'contents': contents})


# ── Admin: Product Management ─────────────────────────────────────────────────

@role_required('admin')
def admin_manage_products(request):
    products = _paginate_queryset(request, Product.objects.order_by('-created_at'), per_page=12)
    return render(request, 'dashboard/admin_manage_products.html', {'products': products})


@role_required('admin')
def admin_manage_product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product saved.')
        return redirect('dashboard:admin_manage_products')
    return render(request, 'dashboard/admin_manage_product_form.html', {'form': form, 'product': product})


@role_required('admin')
def admin_manage_categories(request):
    categories = LivestockCategory.objects.all()
    form = LivestockCategoryForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category added.')
        return redirect('dashboard:admin_manage_categories')
    return render(request, 'dashboard/admin_manage_categories.html', {'categories': categories, 'form': form})


@role_required('admin')
def admin_manage_category_form(request, pk=None):
    category = get_object_or_404(LivestockCategory, pk=pk) if pk else None
    form = LivestockCategoryForm(request.POST or None, request.FILES or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category saved.')
        return redirect('dashboard:admin_manage_categories')
    return render(request, 'dashboard/admin_manage_category_form.html', {'form': form})


@role_required('admin', 'staff')
def admin_manage_livestock_form(request, pk=None):
    species = get_object_or_404(LivestockSpecies, pk=pk) if pk else None
    form = LivestockSpeciesForm(request.POST or None, request.FILES or None, instance=species)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Livestock record saved.')
        return redirect('dashboard:admin_livestock')
    return render(request, 'dashboard/admin_manage_livestock_form.html', {'form': form, 'species': species})


@role_required('admin', 'staff')
def admin_livestock(request):
    categories = LivestockCategory.objects.prefetch_related(
        'species__feed_schedules', 'species__growth_boosters', 'species__seasonal_variations'
    ).all()

    # Compute totals for the analytics strip
    total_species = sum(c.species.count() for c in categories)
    total_stock   = sum(
        s.current_stock for c in categories for s in c.species.all()
    )
    total_schedules = sum(
        s.feed_schedules.count() for c in categories for s in c.species.all()
    )
    total_boosters = sum(
        s.growth_boosters.count() for c in categories for s in c.species.all()
    )

    return render(request, 'dashboard/admin_livestock.html', {
        'categories': categories,
        'total_species': total_species,
        'total_stock': total_stock,
        'total_schedules': total_schedules,
        'total_boosters': total_boosters,
    })


@role_required('admin', 'staff')
def admin_manage_feed_form(request, pk=None):
    schedule = get_object_or_404(FeedSchedule, pk=pk) if pk else None
    form = FeedScheduleForm(request.POST or None, instance=schedule)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Feed schedule saved.')
        return redirect('dashboard:admin_livestock')
    time_choices = [
        ('6:00 AM', '6:00 AM'), ('7:00 AM', '7:00 AM'), ('8:00 AM', '8:00 AM'),
        ('9:00 AM', '9:00 AM'), ('10:00 AM', '10:00 AM'), ('11:00 AM', '11:00 AM'),
        ('12:00 PM', '12:00 PM'), ('1:00 PM', '1:00 PM'), ('2:00 PM', '2:00 PM'),
        ('3:00 PM', '3:00 PM'), ('4:00 PM', '4:00 PM'), ('5:00 PM', '5:00 PM'),
        ('6:00 PM', '6:00 PM'), ('7:00 PM', '7:00 PM'),
    ]
    return render(request, 'dashboard/admin_manage_feed_form.html', {
        'form': form,
        'time_choices': time_choices,
    })


@role_required('admin', 'staff')
def admin_manage_boosters(request):
    boosters = GrowthBooster.objects.select_related('species').all()
    form = GrowthBoosterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Growth booster saved.')
        return redirect('dashboard:admin_manage_boosters')
    return render(request, 'dashboard/admin_manage_boosters.html', {'boosters': boosters, 'form': form})


@role_required('admin', 'staff')
def admin_manage_seasonal(request):
    variations = SeasonalVariation.objects.select_related('species').all()
    form = SeasonalVariationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Seasonal variation saved.')
        return redirect('dashboard:admin_manage_seasonal')
    return render(request, 'dashboard/admin_manage_seasonal.html', {'variations': variations, 'form': form})


# ── Admin: Daily Farm Log ────────────────────────────────────────────────────

@role_required('admin', 'staff')
def admin_daily_log(request):
    today = timezone.localdate()
    egg_window_start = today - timedelta(days=29)

    feed_form = DailyFeedLogForm(request.POST if request.POST.get('form_type') == 'feed' else None,
                                 initial={'date': today})
    production_form = DailyProductionLogForm(request.POST if request.POST.get('form_type') == 'production' else None,
                                             initial={'date': today})

    if request.method == 'POST':
        if request.POST.get('form_type') == 'feed' and feed_form.is_valid():
            entry = feed_form.save(commit=False)
            entry.recorded_by = request.user
            entry.save()
            messages.success(request, 'Feed consumption logged.')
            return redirect('dashboard:admin_daily_log')
        elif request.POST.get('form_type') == 'production' and production_form.is_valid():
            entry = production_form.save(commit=False)
            entry.recorded_by = request.user
            entry.save()
            messages.success(request, 'Production record logged.')
            return redirect('dashboard:admin_daily_log')

    feed_logs = DailyFeedLog.objects.select_related('species', 'recorded_by').order_by('-date', '-created_at')[:60]
    production_logs = DailyProductionLog.objects.select_related('species', 'recorded_by').order_by('-date', '-created_at')[:60]
    egg_metrics = _build_egg_metrics(
        DailyProductionLog.objects.filter(_egg_log_filter(), date__gte=egg_window_start)
        .select_related('species')
    )

    return render(request, 'dashboard/admin_daily_log.html', {
        'feed_form': feed_form,
        'production_form': production_form,
        'feed_logs': feed_logs,
        'production_logs': production_logs,
        'egg_metrics': egg_metrics,
        'today': today,
    })


@role_required('admin', 'staff')
def admin_delete_feed_log(request, pk):
    from django.shortcuts import get_object_or_404
    entry = get_object_or_404(DailyFeedLog, pk=pk)
    entry.delete()
    messages.success(request, 'Feed log entry deleted.')
    return redirect('dashboard:admin_daily_log')


@role_required('admin', 'staff')
def admin_delete_production_log(request, pk):
    from django.shortcuts import get_object_or_404
    entry = get_object_or_404(DailyProductionLog, pk=pk)
    entry.delete()
    messages.success(request, 'Production log entry deleted.')
    return redirect('dashboard:admin_daily_log')


# ── Admin: Farm Overview (Unified Management Page) ───────────────────────────

@role_required('admin', 'staff')
def admin_farm_overview(request):
    """Comprehensive farm management overview - all records in one place."""
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)
    egg_window_start = today - timedelta(days=29)

    # Initialize all forms
    feed_form = DailyFeedLogForm(
        request.POST if request.POST.get('form_type') == 'feed' else None,
        initial={'date': today}
    )
    production_form = DailyProductionLogForm(
        request.POST if request.POST.get('form_type') == 'production' else None,
        initial={'date': today}
    )
    feed_schedule_form = FeedScheduleForm(
        request.POST if request.POST.get('form_type') == 'schedule' else None
    )
    booster_form = GrowthBoosterForm(
        request.POST if request.POST.get('form_type') == 'booster' else None
    )
    seasonal_form = SeasonalVariationForm(
        request.POST if request.POST.get('form_type') == 'seasonal' else None
    )

    # Handle form submissions
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'feed' and feed_form.is_valid():
            entry = feed_form.save(commit=False)
            entry.recorded_by = request.user
            entry.save()
            messages.success(request, '✓ Feed consumption logged.')
            return redirect('dashboard:admin_farm_overview')
            
        elif form_type == 'production' and production_form.is_valid():
            entry = production_form.save(commit=False)
            entry.recorded_by = request.user
            entry.save()
            messages.success(request, '✓ Production record logged.')
            return redirect('dashboard:admin_farm_overview')
            
        elif form_type == 'schedule' and feed_schedule_form.is_valid():
            feed_schedule_form.save()
            messages.success(request, '✓ Feed schedule created.')
            return redirect('dashboard:admin_farm_overview')
            
        elif form_type == 'booster' and booster_form.is_valid():
            booster_form.save()
            messages.success(request, '✓ Growth booster added.')
            return redirect('dashboard:admin_farm_overview')
            
        elif form_type == 'seasonal' and seasonal_form.is_valid():
            seasonal_form.save()
            messages.success(request, '✓ Seasonal variation saved.')
            return redirect('dashboard:admin_farm_overview')

    # Gather all data
    categories = LivestockCategory.objects.prefetch_related(
        'species__feed_schedules', 'species__growth_boosters', 'species__seasonal_variations'
    ).all()

    # Overview metrics
    total_species = sum(c.species.count() for c in categories)
    total_stock = sum(s.current_stock for c in categories for s in c.species.all())
    total_schedules = sum(s.feed_schedules.count() for c in categories for s in c.species.all())
    total_boosters = sum(s.growth_boosters.count() for c in categories for s in c.species.all())
    total_variations = sum(s.seasonal_variations.count() for c in categories for s in c.species.all())

    # Recent logs
    recent_feed_logs = DailyFeedLog.objects.select_related('species', 'recorded_by').filter(
        date__gte=week_ago
    ).order_by('-date', '-created_at')[:20]
    
    recent_production_logs = DailyProductionLog.objects.select_related('species', 'recorded_by').filter(
        date__gte=week_ago
    ).order_by('-date', '-created_at')[:20]

    # All schedules, boosters, variations
    all_schedules = FeedSchedule.objects.select_related('species__category').order_by('species__name', 'feed_type')
    all_boosters = GrowthBooster.objects.select_related('species__category').order_by('species__name', 'name')
    all_variations = SeasonalVariation.objects.select_related('species__category').order_by('species__name', 'season')

    # Egg metrics
    egg_metrics = _build_egg_metrics(
        DailyProductionLog.objects.filter(_egg_log_filter(), date__gte=egg_window_start).select_related('species')
    )

    # Time choices for feed schedule form
    time_choices = [
        ('5am', '5:00 AM'), ('6am', '6:00 AM'), ('7am', '7:00 AM'), ('8am', '8:00 AM'),
        ('9am', '9:00 AM'), ('10am', '10:00 AM'), ('11am', '11:00 AM'), ('12pm', '12:00 PM'),
        ('1pm', '1:00 PM'), ('2pm', '2:00 PM'), ('3pm', '3:00 PM'), ('4pm', '4:00 PM'),
        ('5pm', '5:00 PM'), ('6pm', '6:00 PM'), ('7pm', '7:00 PM'), ('8pm', '8:00 PM'),
    ]

    return render(request, 'dashboard/admin_farm_overview.html', {
        # Forms
        'feed_form': feed_form,
        'production_form': production_form,
        'feed_schedule_form': feed_schedule_form,
        'booster_form': booster_form,
        'seasonal_form': seasonal_form,
        # Data
        'categories': categories,
        'total_species': total_species,
        'total_stock': total_stock,
        'total_schedules': total_schedules,
        'total_boosters': total_boosters,
        'total_variations': total_variations,
        'recent_feed_logs': recent_feed_logs,
        'recent_production_logs': recent_production_logs,
        'all_schedules': all_schedules,
        'all_boosters': all_boosters,
        'all_variations': all_variations,
        'egg_metrics': egg_metrics,
        'time_choices': time_choices,
        'today': today,
    })


# ── Admin: Marketing Management ───────────────────────────────────────────────

@role_required('admin')
def admin_manage_promotions(request):
    promotions = Promotion.objects.all()
    return render(request, 'dashboard/admin_manage_promotions.html', {'promotions': promotions})


@role_required('admin')
def admin_manage_promo_form(request, pk=None):
    promo = get_object_or_404(Promotion, pk=pk) if pk else None
    form = PromotionForm(request.POST or None, instance=promo)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Promotion saved.')
        return redirect('dashboard:admin_manage_promotions')
    return render(request, 'dashboard/admin_manage_promo_form.html', {'form': form})


@role_required('admin')
def admin_delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, 'Product deleted.')
    return redirect('dashboard:admin_manage_products')


@role_required('admin')
def admin_delete_category(request, pk):
    category = get_object_or_404(LivestockCategory, pk=pk)
    category.delete()
    messages.success(request, 'Category deleted.')
    return redirect('dashboard:admin_manage_categories')


@role_required('admin')
def admin_delete_banner(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    banner.delete()
    messages.success(request, 'Banner deleted.')
    return redirect('dashboard:admin_manage_banners')


@role_required('admin')
def admin_delete_testimonial(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    testimonial.delete()
    messages.success(request, 'Testimonial deleted.')
    return redirect('dashboard:admin_manage_testimonials')


@role_required('admin')
def admin_delete_faq(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    faq.delete()
    messages.success(request, 'FAQ deleted.')
    return redirect('dashboard:admin_manage_faqs')


@role_required('admin')
def admin_delete_promo(request, pk):
    promo = get_object_or_404(Promotion, pk=pk)
    promo.delete()
    messages.success(request, 'Promotion deleted.')
    return redirect('dashboard:admin_manage_promotions')


@role_required('admin')
def admin_delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.delete()
    messages.success(request, 'Announcement deleted.')
    return redirect('dashboard:admin_manage_announcements')


@role_required('admin', 'staff')
def admin_delete_booster(request, pk):
    booster = get_object_or_404(GrowthBooster, pk=pk)
    booster.delete()
    messages.success(request, 'Growth booster deleted.')
    return redirect('dashboard:admin_manage_boosters')


@role_required('admin', 'staff')
def admin_delete_seasonal(request, pk):
    variation = get_object_or_404(SeasonalVariation, pk=pk)
    variation.delete()
    messages.success(request, 'Seasonal variation deleted.')
    return redirect('dashboard:admin_manage_seasonal')


@role_required('admin', 'staff')
def admin_delete_livestock(request, pk):
    species = get_object_or_404(LivestockSpecies, pk=pk)
    species.delete()
    messages.success(request, 'Livestock species deleted.')
    return redirect('dashboard:admin_livestock')


@role_required('admin')
def admin_manage_newsletter(request):
    subscribers = Newsletter.objects.filter(is_active=True).order_by('-subscribed_at')
    return render(request, 'dashboard/admin_manage_newsletter.html', {'subscribers': subscribers})


@role_required('admin')
def admin_contact_messages(request):
    contact_messages = ContactMessage.objects.order_by('-submitted_at')
    # Mark all as read when admin views them
    contact_messages.filter(is_read=False).update(is_read=True)
    contact_messages = _paginate_queryset(request, contact_messages, per_page=15)
    return render(request, 'dashboard/admin_contact_messages.html', {'contact_messages': contact_messages})


@role_required('admin')
def admin_manage_announcements(request):
    announcements = Announcement.objects.all()
    form = AnnouncementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Announcement posted.')
        return redirect('dashboard:admin_manage_announcements')
    return render(request, 'dashboard/admin_manage_announcements.html', {'announcements': announcements, 'form': form})


# ── Staff Views ───────────────────────────────────────────────────────────────

@role_required('staff', 'admin')
def staff_livestock(request):
    categories = LivestockCategory.objects.prefetch_related('species').all()
    return render(request, 'dashboard/staff_livestock.html', {'categories': categories})


@role_required('staff', 'admin')
def staff_feed(request):
    schedules = FeedSchedule.objects.select_related('species').all()
    return render(request, 'dashboard/staff_feed.html', {'schedules': schedules})


@role_required('staff', 'admin')
def staff_orders(request):
    orders = Order.objects.order_by('-created_at')
    return render(request, 'dashboard/staff_orders.html', {'orders': orders})


# ── Customer Views ────────────────────────────────────────────────────────────

@login_required
def customer_orders(request):
    orders = _paginate_queryset(
        request,
        Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at'),
        per_page=10,
    )
    return render(request, 'dashboard/customer_orders.html', {'orders': orders})


@login_required
def customer_wishlist(request):
    from store.models import WishlistItem
    items = WishlistItem.objects.filter(user=request.user).select_related('product')
    return render(request, 'dashboard/customer_wishlist.html', {'wishlist_items': items})


# ── Admin: Sample Data Management ────────────────────────────────────────────

@role_required('admin')
def admin_sample_data_tools(request):
    """Admin interface to populate or delete sample data."""
    return render(request, 'dashboard/admin_sample_data_tools.html')


@role_required('admin')
def admin_populate_sample_data(request):
    """Run the populate_sample management command."""
    if request.method != 'POST':
        return redirect('dashboard:admin_sample_data_tools')

    from django.core.management import call_command
    from io import StringIO

    try:
        output = StringIO()
        call_command('populate_sample', stdout=output)
        messages.success(request, 'Sample data populated successfully!')
    except Exception as e:
        messages.error(request, f'Error populating sample data: {str(e)}')

    return redirect('dashboard:admin_sample_data_tools')


@role_required('admin')
def admin_delete_sample_data(request):
    """Run the delete_sample management command."""
    if request.method != 'POST':
        return redirect('dashboard:admin_sample_data_tools')

    from django.core.management import call_command
    from io import StringIO

    try:
        output = StringIO()
        call_command('delete_sample', stdout=output)
        messages.success(request, 'Sample data deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting sample data: {str(e)}')

    return redirect('dashboard:admin_sample_data_tools')


