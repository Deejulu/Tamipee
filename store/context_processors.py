from django.db.models import Sum

from store.models import CartItem, Announcement


def cart_context(request):
    """Injects cart item count and active announcements into every template."""
    ctx = {}

    # Cart count (authenticated users only)
    if request.user.is_authenticated:
        cart_summary = CartItem.objects.filter(cart__user=request.user).aggregate(total_quantity=Sum('quantity'))
        ctx['cart_item_count'] = cart_summary['total_quantity'] or 0
    else:
        ctx['cart_item_count'] = 0

    # Active announcements shown site-wide
    ctx['site_announcements'] = Announcement.objects.filter(is_active=True).order_by('-created_at')[:3]

    return ctx
