from django.core.management.base import BaseCommand


SAMPLE_PRODUCT_NAMES = [
    'Layer Mash (50kg bag)',
    'Pullet Grower Feed (25kg bag)',
    'Cockerel Grower Mash (25kg bag)',
    'Turkey Grower Pellets (25kg bag)',
    'Catfish Floating Pellets (15kg bag)',
    'Fresh Eggs (Crate of 30)',
    'Live Layer Hen',
    'Live Cockerel (Market Ready)',
    'Live Turkey',
    'Fresh Catfish (Live, per kg)',
    'Calcium & Phosphorus Supplement (Layers)',
    'Vitamin C & Electrolyte Supplement',
]

SAMPLE_CATEGORY_NAMES = ['Poultry', 'Fish']

SAMPLE_BANNER_TITLES = [
    'Fresh Eggs. Live Birds. Quality Feed.',
    'Farm Fresh. Every Day.',
]

SAMPLE_TESTIMONIAL_NAMES = [
    'Emeka Okonkwo', 'Fatimah Bello', 'Chidi Eze', 'Ngozi Adeyemi',
]

SAMPLE_FAQ_QUESTIONS = [
    'How do I place an order for live birds or fish?',
    'Do you deliver to my location?',
    'What is the minimum order quantity for day-old chicks?',
    'Are your feeds tested and certified?',
    'Can I visit the farm before purchasing?',
]

SAMPLE_PROMOTION_TITLES = [
    'June Layer Feed Discount',
    'Fish Farmer Promo',
]

SAMPLE_ANNOUNCEMENT_TITLES = [
    'Fresh Eggs Available — Collected Daily',
    'Market-Ready Turkeys Available Now',
]

SAMPLE_SITE_CONTENT_KEYS = ['hero_title', 'hero_subtitle', 'about_intro']

SAMPLE_USERNAMES = [
    'sample_emeka', 'sample_fatimah', 'sample_chidi', 'sample_ngozi',
]


class Command(BaseCommand):
    help = 'Delete all sample data created by populate_sample'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Deleting Tamipee Integrated Farms sample data...'))

        self._delete_orders()
        self._delete_customers()
        self._delete_store_content()
        self._delete_livestock()

        self.stdout.write(self.style.SUCCESS('\n✓ All sample data deleted successfully!\n'))

    def _delete_orders(self):
        from django.contrib.auth import get_user_model
        from store.models import Order

        User = get_user_model()
        sample_users = User.objects.filter(username__in=SAMPLE_USERNAMES)
        count, _ = Order.objects.filter(user__in=sample_users).delete()
        self.stdout.write(f'  ✓ Deleted {count} sample orders')

    def _delete_customers(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        count, _ = User.objects.filter(username__in=SAMPLE_USERNAMES).delete()
        self.stdout.write(f'  ✓ Deleted {count} sample customer accounts')

    def _delete_store_content(self):
        from store.models import (
            Product, Banner, Testimonial, FAQ,
            Promotion, Announcement, SiteContent,
        )

        p, _ = Product.objects.filter(name__in=SAMPLE_PRODUCT_NAMES).delete()
        b, _ = Banner.objects.filter(title__in=SAMPLE_BANNER_TITLES).delete()
        t, _ = Testimonial.objects.filter(customer_name__in=SAMPLE_TESTIMONIAL_NAMES).delete()
        f, _ = FAQ.objects.filter(question__in=SAMPLE_FAQ_QUESTIONS).delete()
        pr, _ = Promotion.objects.filter(title__in=SAMPLE_PROMOTION_TITLES).delete()
        an, _ = Announcement.objects.filter(title__in=SAMPLE_ANNOUNCEMENT_TITLES).delete()
        sc, _ = SiteContent.objects.filter(key__in=SAMPLE_SITE_CONTENT_KEYS).delete()

        self.stdout.write(
            f'  ✓ Deleted: {p} products, {b} banners, {t} testimonials, '
            f'{f} FAQs, {pr} promotions, {an} announcements, {sc} site content entries'
        )

    def _delete_livestock(self):
        from livestock.models import LivestockCategory

        # Deleting categories cascades to species → feed schedules, boosters, seasonal variations
        count, _ = LivestockCategory.objects.filter(name__in=SAMPLE_CATEGORY_NAMES).delete()
        self.stdout.write(f'  ✓ Deleted livestock categories (+ all linked species, feeds, boosters, variations)')
