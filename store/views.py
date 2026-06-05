from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction, ProgrammingError
from django.db.models import Q
from livestock.models import LivestockCategory, LivestockSpecies
from .models import Product, Cart, CartItem, Order, OrderItem, Testimonial, FAQ, Banner, Announcement, WishlistItem, Promotion, ContactMessage
from .forms import CheckoutForm, NewsletterForm, ContactForm


def _active_promotions_by_product(today, products):
    product_ids = [product.pk for product in products]
    if not product_ids:
        return {}

    promotions = (
        Promotion.objects.filter(
            product_id__in=product_ids,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today,
        )
        .select_related('product')
        .order_by('product_id', '-discount_percent', '-start_date')
    )

    promo_map = {}
    for promotion in promotions:
        promo_map.setdefault(promotion.product_id, promotion)
    return promo_map


def home(request):
    featured_products = Product.objects.filter(is_available=True, is_featured=True)[:6]
    banners = Banner.objects.filter(is_active=True)
    testimonials = Testimonial.objects.filter(is_active=True)[:4]
    try:
        announcements = Announcement.objects.filter(is_active=True)[:3]
    except ProgrammingError:
        announcements = Announcement.objects.none()
    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'banners': banners,
        'testimonials': testimonials,
        'announcements': announcements,
    })


def product_list(request):
    products = Product.objects.filter(is_available=True).select_related('livestock_species', 'livestock_species__category')
    categories = LivestockCategory.objects.order_by('name')
    species_list = LivestockSpecies.objects.select_related('category').order_by('name')
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    species_id = request.GET.get('species')
    stock_filter = request.GET.get('stock')
    sort = request.GET.get('sort', 'newest')

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(livestock_species__name__icontains=query) |
            Q(livestock_species__category__name__icontains=query)
        )
    if category_id:
        products = products.filter(livestock_species__category_id=category_id)
        species_list = species_list.filter(category_id=category_id)
    if species_id:
        products = products.filter(livestock_species_id=species_id)
    if stock_filter == 'in_stock':
        products = products.filter(stock_quantity__gt=0)

    sort_options = {
        'newest': '-created_at',
        'price_asc': 'price',
        'price_desc': '-price',
        'name_asc': 'name',
    }
    products = products.order_by(sort_options.get(sort, '-created_at'))

    return render(request, 'store/product_list.html', {
        'products': products,
        'query': query,
        'categories': categories,
        'species_list': species_list,
        'selected_category': category_id or '',
        'selected_species': species_id or '',
        'selected_stock': stock_filter or '',
        'selected_sort': sort,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    return render(request, 'store/product_detail.html', {'product': product})


def about(request):
    faqs = FAQ.objects.filter(is_active=True)
    return render(request, 'store/about.html', {'faqs': faqs})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            message = form.cleaned_data['message']
            ContactMessage.objects.create(name=name, email=email, phone=phone, message=message)
            # Notify admin by email
            try:
                send_mail(
                    subject=f'New Contact Message from {name}',
                    message=f'Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=True,
                )
            except Exception:
                pass
            messages.success(request, 'Your message has been sent. We will get back to you shortly.')
        else:
            messages.error(request, 'Please correct the highlighted contact details and try again.')
        return redirect('store:contact')
    return render(request, 'store/contact.html', {'form': form})


def newsletter_subscribe(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You have subscribed to our newsletter!')
        else:
            messages.error(request, 'This email is already subscribed.')
    return redirect(request.META.get('HTTP_REFERER', 'store:home'))


@login_required
def cart(request):
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart.html', {'cart': cart_obj})


def add_to_cart(request, pk):
    wants_json = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if request.method not in ['GET', 'POST']:
        if wants_json:
            return JsonResponse({'ok': False, 'message': 'Unsupported request method.'}, status=405)
        return redirect('store:product_list')

    if not request.user.is_authenticated:
        login_url = f"{settings.LOGIN_URL}?next={request.META.get('HTTP_REFERER', request.path)}"
        if wants_json:
            return JsonResponse({'ok': False, 'requires_login': True, 'login_url': login_url}, status=401)
        return redirect(login_url)

    product = get_object_or_404(Product, pk=pk, is_available=True)
    referer = request.META.get('HTTP_REFERER') or request.build_absolute_uri('/')

    if product.stock_quantity < 1:
        message = f'"{product.name}" is currently out of stock.'
        if wants_json:
            return JsonResponse({'ok': False, 'message': message}, status=400)
        messages.error(request, message)
        return redirect(referer)

    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart_obj, product=product)
    current_quantity = item.quantity if not created else 0

    if current_quantity >= product.stock_quantity:
        message = f'Only {product.stock_quantity} unit(s) of "{product.name}" are available.'
        if wants_json:
            return JsonResponse({'ok': False, 'message': message, 'cart_item_count': cart_obj.item_count}, status=400)
        messages.error(request, message)
        return redirect(referer)

    if not created:
        item.quantity += 1
        item.save(update_fields=['quantity'])

    message = f'"{product.name}" added to cart.'
    if wants_json:
        return JsonResponse({'ok': True, 'message': message, 'cart_item_count': cart_obj.item_count})

    messages.success(request, message)
    return redirect(referer)


@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    item.delete()
    messages.info(request, 'Item removed from cart.')
    return redirect('store:cart')


@login_required
def update_cart_item(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    if request.method != 'POST':
        return redirect('store:cart')

    try:
        quantity = int(request.POST.get('quantity', item.quantity))
    except (TypeError, ValueError):
        messages.error(request, 'Enter a valid quantity.')
        return redirect('store:cart')

    if quantity <= 0:
        item.delete()
        messages.info(request, 'Item removed from cart.')
        return redirect('store:cart')

    if quantity > item.product.stock_quantity:
        messages.error(request, f'Only {item.product.stock_quantity} unit(s) of "{item.product.name}" are available.')
        return redirect('store:cart')

    item.quantity = quantity
    item.save(update_fields=['quantity'])
    messages.success(request, 'Cart quantity updated.')
    return redirect('store:cart')


@login_required
def checkout(request):
    cart_obj, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = list(cart_obj.items.select_related('product'))
    if not cart_obj.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:cart')

    # Stock validation before showing form or processing
    out_of_stock = []
    for item in cart_items:
        if item.product.stock_quantity < item.quantity:
            out_of_stock.append(item.product.name)
    if out_of_stock:
        messages.error(request, f'Sorry, insufficient stock for: {", ".join(out_of_stock)}. Please update your cart.')
        return redirect('store:cart')

    form = CheckoutForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        today = timezone.now().date()
        with transaction.atomic():
            locked_items = list(
                cart_obj.items.select_related('product').select_for_update()
            )
            if not locked_items:
                messages.warning(request, 'Your cart is empty.')
                return redirect('store:cart')

            out_of_stock = []
            locked_products = []
            for item in locked_items:
                locked_product = Product.objects.select_for_update().get(pk=item.product_id)
                locked_products.append(locked_product)
                if locked_product.stock_quantity < item.quantity:
                    out_of_stock.append(locked_product.name)

            if out_of_stock:
                messages.error(request, f'Sorry, insufficient stock for: {", ".join(out_of_stock)}. Please update your cart.')
                return redirect('store:cart')

            promo_map = _active_promotions_by_product(today, locked_products)
            order = form.save(commit=False)
            order.user = request.user

            total = 0
            order_items = []
            product_map = {product.pk: product for product in locked_products}
            for item in locked_items:
                product = product_map[item.product_id]
                unit_price = product.price
                promo = promo_map.get(product.pk)
                if promo and promo.discount_percent > 0:
                    discount = unit_price * (promo.discount_percent / 100)
                    unit_price = unit_price - discount

                total += unit_price * item.quantity
                order_items.append(OrderItem(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    unit_price=unit_price,
                ))

            order.total_amount = total
            order.save()
            for order_item in order_items:
                order_item.order = order
            OrderItem.objects.bulk_create(order_items)
            cart_obj.items.all().delete()

        # Send order confirmation email to customer
        try:
            item_lines = '\n'.join(
                [f'  - {oi.product.name} x{oi.quantity} @ ₦{oi.unit_price}' for oi in order.items.all()]
            )
            send_mail(
                subject=f'Order #{order.pk} Confirmed – Tamipee Integrated Farms',
                message=(
                    f'Hi {request.user.first_name or request.user.username},\n\n'
                    f'Thank you for your order! Here is your summary:\n\n'
                    f'Order #: {order.pk}\n'
                    f'Items:\n{item_lines}\n\n'
                    f'Total: ₦{order.total_amount}\n\n'
                    f'Delivery Address: {order.delivery_address}\n\n'
                    f'We will process your order shortly.\n\n'
                    f'– Tamipee Integrated Farms'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=True,
            )
        except Exception:
            pass

        return redirect('payments:initiate')
    return render(request, 'store/checkout.html', {'cart': cart_obj, 'form': form})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method != 'POST':
        return redirect('store:order_detail', pk=pk)

    cancellable_statuses = {'pending', 'confirmed'}
    if order.status not in cancellable_statuses:
        messages.error(request, 'This order can no longer be cancelled online.')
        return redirect('store:order_detail', pk=pk)

    if order.inventory_applied:
        order.release_inventory()

    order.status = 'cancelled'
    order.save(update_fields=['status', 'updated_at'])
    messages.success(request, f'Order #{order.pk} has been cancelled.')
    return redirect('store:order_detail', pk=pk)


@login_required
def toggle_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        messages.info(request, f'"{product.name}" removed from wishlist.')
    else:
        messages.success(request, f'"{product.name}" added to wishlist.')
    return redirect(request.META.get('HTTP_REFERER', 'store:product_list'))


