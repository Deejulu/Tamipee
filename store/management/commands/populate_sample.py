from django.core.management.base import BaseCommand
from datetime import date, timedelta
import random

# -----------------------------------------------------------------------
# CLIENT DATA — Tamipee Integrated Farms
# All species, feeds and tasks come directly from the farm owner.
# -----------------------------------------------------------------------


class Command(BaseCommand):
    help = 'Populate the database with realistic sample data for Tamipee Integrated Farms'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Populating Tamipee Integrated Farms sample data...'))
        self._create_livestock()
        self._create_products()
        self._create_site_content()
        self._create_sample_orders()
        self.stdout.write(self.style.SUCCESS('\n✓ All sample data populated successfully!'))
        self.stdout.write('  Run: python manage.py delete_sample   — to remove all this data\n')

    # ------------------------------------------------------------------ #
    #  LIVESTOCK                                                           #
    # ------------------------------------------------------------------ #
    def _create_livestock(self):
        from livestock.models import (
            LivestockCategory, LivestockSpecies,
            FeedSchedule, GrowthBooster, SeasonalVariation,
        )

        # --- Categories (client's actual farm) ---
        poultry, _ = LivestockCategory.objects.get_or_create(
            name='Poultry',
            defaults={'description': 'Chickens, turkeys and other domestic birds raised for meat and eggs at Tamipee Integrated Farms.'},
        )
        fish, _ = LivestockCategory.objects.get_or_create(
            name='Fish',
            defaults={'description': 'Freshwater fish species including catfish farmed in our ponds.'},
        )

        # --- Species (from client's daily activity list) ---
        layer, _ = LivestockSpecies.objects.get_or_create(
            name='Layer Hen',
            category=poultry,
            defaults={
                'breed': 'Lohmann Brown',
                'description': (
                    'High-producing egg layer hens. Morning routine includes pen cleaning and feeding. '
                    'Eggs are collected and feed troughs topped up in the afternoon.'
                ),
                'current_stock': 350,
            },
        )
        pullet, _ = LivestockSpecies.objects.get_or_create(
            name='Pullet',
            category=poultry,
            defaults={
                'breed': 'Lohmann Brown (Pre-lay)',
                'description': (
                    'Young female chickens (8–18 weeks) being raised to become laying hens. '
                    'Fed twice daily — morning and evening — to ensure healthy development before the laying stage.'
                ),
                'current_stock': 200,
            },
        )
        cockerel, _ = LivestockSpecies.objects.get_or_create(
            name='Cockerel',
            category=poultry,
            defaults={
                'breed': 'Mixed Breed',
                'description': (
                    'Young male chickens raised for meat production. '
                    'Fed daily with high-protein ration for good weight gain.'
                ),
                'current_stock': 150,
            },
        )
        turkey, _ = LivestockSpecies.objects.get_or_create(
            name='Turkey',
            category=poultry,
            defaults={
                'breed': 'Broad-Breasted White',
                'description': (
                    'Commercially farmed turkeys for festive and year-round meat supply. '
                    'Known for their large body size and excellent meat quality.'
                ),
                'current_stock': 80,
            },
        )
        catfish, _ = LivestockSpecies.objects.get_or_create(
            name='Catfish',
            category=fish,
            defaults={
                'breed': 'Clarias gariepinus',
                'description': (
                    'African catfish farmed in our earthen ponds. '
                    'Fed every morning for optimal growth and feed conversion.'
                ),
                'current_stock': 2000,
            },
        )

        # --- Feed Schedules (from client's actual daily farm activities) ---
        feed_schedules = [
            # LAYERS — morning clean + feed, afternoon egg collection + top-up
            dict(
                species=layer, feed_type='Layer Mash',
                defaults=dict(
                    daily_quantity_kg=20, cost_per_kg=420,
                    feeding_times='Morning (7am) — feed & clean pen. Afternoon (2pm) — collect eggs & top up feed.',
                    season='all',
                    notes=(
                        'Morning: Clean layer pen (remove droppings). Feed layers. '
                        'Afternoon: Pick up all eggs. Rub/top up feed troughs for evening intake. '
                        'Ensure consistent schedule for steady egg production.'
                    ),
                ),
            ),
            # CATFISH — morning feeding only
            dict(
                species=catfish, feed_type='Catfish Floating Pellets',
                defaults=dict(
                    daily_quantity_kg=15, cost_per_kg=750,
                    feeding_times='Morning (7am)',
                    season='all',
                    notes=(
                        'Feed fish every morning. Broadcast pellets evenly across pond surface. '
                        'Remove any uneaten feed after 30 minutes to maintain water quality. '
                        'Feed quantity = 3% of total fish body weight.'
                    ),
                ),
            ),
            # PULLETS — morning and evening
            dict(
                species=pullet, feed_type='Pullet Grower Feed',
                defaults=dict(
                    daily_quantity_kg=10, cost_per_kg=400,
                    feeding_times='Morning (7am) and Evening (5pm)',
                    season='all',
                    notes=(
                        'Feed pullets twice daily — morning and evening. '
                        'Use grower feed with 16–18% protein to support healthy development. '
                        'Monitor body weight weekly to confirm on-target growth.'
                    ),
                ),
            ),
            # COCKERELS — daily feeding
            dict(
                species=cockerel, feed_type='Cockerel Grower Mash',
                defaults=dict(
                    daily_quantity_kg=8, cost_per_kg=390,
                    feeding_times='Morning (7am)',
                    season='all',
                    notes=(
                        'Feed cockerels once in the morning with a high-protein grower mash. '
                        'Ensure adequate feeder space to prevent competition and uneven growth.'
                    ),
                ),
            ),
            # TURKEYS — daily feeding
            dict(
                species=turkey, feed_type='Turkey Grower Pellets',
                defaults=dict(
                    daily_quantity_kg=12, cost_per_kg=500,
                    feeding_times='Morning (7am)',
                    season='all',
                    notes=(
                        'Feed turkeys in the morning. Turkeys require higher protein than chickens — '
                        'use a 22–24% protein turkey grower pellet. '
                        'Provide grit and clean water at all times.'
                    ),
                ),
            ),
        ]
        for kwargs in feed_schedules:
            FeedSchedule.objects.get_or_create(**kwargs)

        # --- Growth Boosters (client species) ---
        boosters = [
            dict(
                species=layer, name='Calcium & Phosphorus Supplement',
                defaults=dict(
                    booster_type='Mineral',
                    dosage='2 g per bird per day mixed into morning feed',
                    frequency='Daily',
                    expected_impact='Stronger eggshells. Reduces soft-shell egg complaints. 8% improvement in hatchability.',
                    cost_per_unit=800,
                ),
            ),
            dict(
                species=layer, name='Vitamin C & Electrolyte Supplement',
                defaults=dict(
                    booster_type='Vitamin',
                    dosage='5 ml per litre of drinking water',
                    frequency='Every 3 days (daily during dry season)',
                    expected_impact='Reduces heat stress, maintains egg production during hot months. 10% reduction in mortality.',
                    cost_per_unit=2000,
                ),
            ),
            dict(
                species=catfish, name='Aqua Boost Growth Enhancer',
                defaults=dict(
                    booster_type='Growth Enhancer',
                    dosage='2 ml per kg of feed',
                    frequency='Every 2 weeks',
                    expected_impact='20% faster growth rate. Improved immune response and disease resistance in pond conditions.',
                    cost_per_unit=3500,
                ),
            ),
            dict(
                species=pullet, name='Pullet Vitamin Premix',
                defaults=dict(
                    booster_type='Vitamin Premix',
                    dosage='1 g per litre of drinking water',
                    frequency='Weekly',
                    expected_impact='Better feathering, uniform growth, and earlier onset of laying. Reduces mortality during grow-out.',
                    cost_per_unit=1200,
                ),
            ),
            dict(
                species=turkey, name='Turkey Amino Acid Supplement',
                defaults=dict(
                    booster_type='Amino Acid',
                    dosage='5 g per kg of feed',
                    frequency='Daily in morning feed',
                    expected_impact='Improved breast muscle development. Turkeys reach market weight 10–12 days earlier.',
                    cost_per_unit=2500,
                ),
            ),
        ]
        for kwargs in boosters:
            GrowthBooster.objects.get_or_create(**kwargs)

        # --- Seasonal Variations (client species) ---
        variations = [
            dict(
                species=layer, season='Dry',
                defaults=dict(
                    production_impact='Egg production drops 15–20% due to heat stress. Thin or soft eggshells more common.',
                    recommended_action='Increase water intake. Add shade nets over pens. Supplement with Vitamin C and electrolytes daily. Feed during cooler morning hours only.',
                    expected_yield_change_percent=-18,
                ),
            ),
            dict(
                species=layer, season='Rainy',
                defaults=dict(
                    production_impact='Cool temperatures help maintain production. However wet litter increases respiratory disease risk.',
                    recommended_action='Improve drainage around pens. Increase litter changing frequency. Monitor for Newcastle and coccidiosis.',
                    expected_yield_change_percent=8,
                ),
            ),
            dict(
                species=catfish, season='Rainy',
                defaults=dict(
                    production_impact='Flooding risk may damage pond embankments and allow fish to escape. Water quality can deteriorate rapidly.',
                    recommended_action='Reinforce pond embankments before rainy season. Monitor water pH and oxygen levels. Reduce feeding rate during heavy rainfall.',
                    expected_yield_change_percent=-5,
                ),
            ),
            dict(
                species=pullet, season='Dry',
                defaults=dict(
                    production_impact='Heat stress during grow-out phase can delay onset of laying and reduce eventual egg production.',
                    recommended_action='Provide adequate ventilation and shade. Ensure fresh cool water is available at all times especially at the evening feed.',
                    expected_yield_change_percent=-10,
                ),
            ),
            dict(
                species=turkey, season='Dry',
                defaults=dict(
                    production_impact='Turkeys are particularly sensitive to heat. High temperatures can cause significant weight loss and mortality.',
                    recommended_action='Provide large shaded areas and wallowing spots if possible. Feed only in the early morning. Increase water supply.',
                    expected_yield_change_percent=-15,
                ),
            ),
        ]
        for kwargs in variations:
            SeasonalVariation.objects.get_or_create(**kwargs)

        self.stdout.write('  ✓ Livestock categories, species, feed schedules, boosters, seasonal variations')

    # ------------------------------------------------------------------ #
    #  PRODUCTS, BANNERS, TESTIMONIALS, FAQS, PROMOTIONS, ANNOUNCEMENTS  #
    # ------------------------------------------------------------------ #
    def _create_products(self):
        from livestock.models import LivestockSpecies
        from store.models import Product, Banner, Testimonial, FAQ, Promotion, Announcement

        layer   = LivestockSpecies.objects.filter(name='Layer Hen').first()
        pullet  = LivestockSpecies.objects.filter(name='Pullet').first()
        cockerel= LivestockSpecies.objects.filter(name='Cockerel').first()
        turkey  = LivestockSpecies.objects.filter(name='Turkey').first()
        catfish = LivestockSpecies.objects.filter(name='Catfish').first()

        products = [
            # Feeds for sale
            dict(name='Layer Mash (50kg bag)', defaults=dict(
                description='Complete layer mash for egg-laying hens. Rich in calcium and phosphorus for strong eggshells and consistent high egg production. Fed every morning at Tamipee Integrated Farms.',
                price=18000, unit='piece', stock_quantity=50,
                is_featured=True, is_available=True, livestock_species=layer,
            )),
            dict(name='Pullet Grower Feed (25kg bag)', defaults=dict(
                description='Balanced grower feed for pullets aged 8–18 weeks. 17% protein content supports steady growth and on-time onset of laying. Fed morning and evening.',
                price=9500, unit='piece', stock_quantity=40,
                is_featured=False, is_available=True, livestock_species=pullet,
            )),
            dict(name='Cockerel Grower Mash (25kg bag)', defaults=dict(
                description='High-protein grower mash for cockerels. Promotes rapid weight gain and good muscle development for market-ready birds.',
                price=9000, unit='piece', stock_quantity=35,
                is_featured=False, is_available=True, livestock_species=cockerel,
            )),
            dict(name='Turkey Grower Pellets (25kg bag)', defaults=dict(
                description='Specially formulated 22% protein pellets for growing turkeys. Supports the fast muscle growth needed for market-weight turkeys.',
                price=12000, unit='piece', stock_quantity=25,
                is_featured=False, is_available=True, livestock_species=turkey,
            )),
            dict(name='Catfish Floating Pellets (15kg bag)', defaults=dict(
                description='High-protein floating pellets for pond catfish farming. Fed every morning at our fish ponds. Promotes rapid growth and good feed conversion.',
                price=11000, unit='piece', stock_quantity=60,
                is_featured=True, is_available=True, livestock_species=catfish,
            )),
            # Live animals & produce
            dict(name='Fresh Eggs (Crate of 30)', defaults=dict(
                description='Farm-fresh eggs from our well-managed layer hens. Collected daily every afternoon and carefully sorted for size and quality. No preservatives.',
                price=3500, unit='piece', stock_quantity=100,
                is_featured=True, is_available=True, livestock_species=layer,
            )),
            dict(name='Live Layer Hen', defaults=dict(
                description='Healthy spent or active layer hens from our flock. Well-fed on quality layer mash. Available for home consumption or small-scale farming.',
                price=4500, unit='piece', stock_quantity=80,
                is_featured=False, is_available=True, livestock_species=layer,
            )),
            dict(name='Live Cockerel (Market Ready)', defaults=dict(
                description='Well-grown market-ready cockerels averaging 2–2.5 kg live weight. Fed on grower mash with no hormones. Ideal for celebrations and daily use.',
                price=5500, unit='piece', stock_quantity=60,
                is_featured=True, is_available=True, livestock_species=cockerel,
            )),
            dict(name='Live Turkey', defaults=dict(
                description='Farm-raised Broad-Breasted White turkeys. Large, meaty birds ideal for special occasions, weddings and celebrations. Average live weight 8–12 kg.',
                price=35000, unit='piece', stock_quantity=30,
                is_featured=True, is_available=True, livestock_species=turkey,
            )),
            dict(name='Fresh Catfish (Live, per kg)', defaults=dict(
                description='Live pond-fresh catfish sold per kilogram. Farmed without antibiotics in clean freshwater ponds. Available for pickup daily after morning harvest.',
                price=2800, unit='kg', stock_quantity=80,
                is_featured=True, is_available=True, livestock_species=catfish,
            )),
            # Supplements
            dict(name='Calcium & Phosphorus Supplement (Layers)', defaults=dict(
                description='Mineral supplement mixed into layer feed daily to prevent soft-shell eggs and maintain bone strength in laying hens.',
                price=800, unit='piece', stock_quantity=70,
                is_featured=False, is_available=True, livestock_species=layer,
            )),
            dict(name='Vitamin C & Electrolyte Supplement', defaults=dict(
                description='Concentrated vitamin C and electrolyte blend. Reduces heat stress in all poultry species. Particularly important during dry season mornings.',
                price=2000, unit='piece', stock_quantity=60,
                is_featured=False, is_available=True, livestock_species=layer,
            )),
        ]
        for kwargs in products:
            Product.objects.get_or_create(**kwargs)

        # Banners
        Banner.objects.get_or_create(
            title='Fresh Eggs. Live Birds. Quality Feed.',
            defaults=dict(
                subtitle='Layer hens, catfish, cockerels, pullets and turkeys — raised with care at Tamipee Integrated Farms.',
                is_active=True, order=1,
            ),
        )
        Banner.objects.get_or_create(
            title='Farm Fresh. Every Day.',
            defaults=dict(
                subtitle='Our eggs are collected fresh every afternoon. Our catfish are harvested daily from our ponds. Order now for same-day pickup.',
                is_active=True, order=2,
            ),
        )

        # Testimonials
        testimonials = [
            dict(customer_name='Emeka Okonkwo', rating=5, defaults=dict(
                message="I've been buying broiler chicks from Tamipee Farms for over a year. Quality is consistently excellent and mortality rate is very low compared to other suppliers.",
                is_active=True,
            )),
            dict(customer_name='Fatimah Bello', rating=5, defaults=dict(
                message='The catfish feed I purchased gave amazing results. My fish reached market size two weeks earlier than expected. Very impressed!',
                is_active=True,
            )),
            dict(customer_name='Chidi Eze', rating=4, defaults=dict(
                message='Professional service and fast delivery. The starter mash quality is top notch. My broilers have been performing very well on it.',
                is_active=True,
            )),
            dict(customer_name='Ngozi Adeyemi', rating=5, defaults=dict(
                message='Tamipee Farms is the only place I trust for my poultry feed. Honest pricing, quality products and very helpful staff. Highly recommended!',
                is_active=True,
            )),
        ]
        for t in testimonials:
            defaults = t.pop('defaults')
            defaults['rating'] = t.pop('rating')
            Testimonial.objects.get_or_create(**t, defaults=defaults)

        # FAQs
        faqs = [
            ('How do I place an order for live birds or fish?',
             'Simply browse our shop, add your desired products to the cart, and proceed to checkout. We accept payment via Paystack. For large bulk orders, please contact us directly for special pricing.', 1),
            ('Do you deliver to my location?',
             'Yes, we offer delivery across the state. Delivery fees are calculated based on your location and order size. Enter your address at checkout and we will confirm the delivery timeline.', 2),
            ('What is the minimum order quantity for day-old chicks?',
             'The minimum order for day-old broiler chicks is 50 pieces. This ensures the chicks maintain body heat during transportation. Contact us for orders above 1,000 pieces for a special farm delivery arrangement.', 3),
            ('Are your feeds tested and certified?',
             'All our feeds are sourced from certified manufacturers and meet NAFDAC standards. We regularly test feed samples to ensure quality and nutritional accuracy before making them available for sale.', 4),
            ('Can I visit the farm before purchasing?',
             'Yes! We encourage farm visits. Please call ahead to schedule an appointment so we can give you a proper tour and expert consultation. Walk-in visits may be limited during busy periods.', 5),
        ]
        for question, answer, order in faqs:
            FAQ.objects.get_or_create(
                question=question,
                defaults=dict(answer=answer, order=order, is_active=True),
            )

        # Promotions (based on client products)
        today = date.today()
        layer_mash = Product.objects.filter(name='Layer Mash (50kg bag)').first()
        catfish_pellets = Product.objects.filter(name='Catfish Floating Pellets (15kg bag)').first()
        if layer_mash:
            Promotion.objects.get_or_create(
                title='June Layer Feed Discount',
                defaults=dict(
                    description='Get 10% off Layer Mash this month. Stock up before prices change!',
                    discount_percent=10,
                    product=layer_mash,
                    start_date=today,
                    end_date=today + timedelta(days=30),
                    is_active=True,
                ),
            )
        if catfish_pellets:
            Promotion.objects.get_or_create(
                title='Fish Farmer Promo',
                defaults=dict(
                    description='15% off Catfish Floating Pellets for the next two weeks. Grow your fish faster for less!',
                    discount_percent=15,
                    product=catfish_pellets,
                    start_date=today,
                    end_date=today + timedelta(days=14),
                    is_active=True,
                ),
            )

        # Announcements
        Announcement.objects.get_or_create(
            title='Fresh Eggs Available — Collected Daily',
            defaults=dict(
                body='Our layer hens are producing at full capacity. Fresh eggs are collected every afternoon and available for sale the same day. Order a crate now before they run out!',
                is_active=True,
            ),
        )
        Announcement.objects.get_or_create(
            title='Market-Ready Turkeys Available Now',
            defaults=dict(
                body='We have a fresh batch of well-grown Broad-Breasted White turkeys ready for sale. Perfect for celebrations, events and special occasions. Call to reserve yours today.',
                is_active=True,
            ),
        )

        self.stdout.write('  ✓ Products, banners, testimonials, FAQs, promotions, announcements')

    # ------------------------------------------------------------------ #
    #  SITE CONTENT                                                        #
    # ------------------------------------------------------------------ #
    def _create_site_content(self):
        from store.models import SiteContent
        contents = [
            ('hero_title', 'Fresh Farm Products, Delivered With Care'),
            ('hero_subtitle', 'Premium poultry, fish and livestock products from Tamipee Integrated Farms — raised naturally, delivered fresh to your door.'),
            ('about_intro', 'Tamipee Integrated Farms is a premier integrated farming enterprise dedicated to producing high-quality livestock, poultry and fish products. With years of experience in sustainable farming, we combine traditional values with modern agricultural practices to deliver the best to our customers and communities.'),
        ]
        for key, value in contents:
            SiteContent.objects.get_or_create(key=key, defaults={'value': value})
        self.stdout.write('  ✓ Site content')

    # ------------------------------------------------------------------ #
    #  SAMPLE CUSTOMERS & ORDERS (for dashboard analytics)                #
    # ------------------------------------------------------------------ #
    def _create_sample_orders(self):
        from django.contrib.auth import get_user_model
        from store.models import Product, Order, OrderItem

        User = get_user_model()

        sample_customers = [
            dict(username='sample_emeka',   email='emeka.okonkwo@example.com',   first_name='Emeka',   last_name='Okonkwo'),
            dict(username='sample_fatimah', email='fatimah.bello@example.com',   first_name='Fatimah', last_name='Bello'),
            dict(username='sample_chidi',   email='chidi.eze@example.com',       first_name='Chidi',   last_name='Eze'),
            dict(username='sample_ngozi',   email='ngozi.adeyemi@example.com',   first_name='Ngozi',   last_name='Adeyemi'),
        ]

        customers = []
        for cdata in sample_customers:
            user, created = User.objects.get_or_create(
                username=cdata['username'],
                defaults={**cdata, 'role': 'customer'},
            )
            if created:
                user.set_password('SamplePass123!')
                user.save()
            customers.append(user)

        products = list(Product.objects.filter(is_available=True))
        if not products:
            return

        statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'delivered']
        addresses = [
            '12 Adeola Odeku Street, Victoria Island, Lagos',
            '45 Gimbiya Street, Area 11, Abuja',
            '8 Rumuola Road, Port Harcourt, Rivers State',
            '23 Ring Road, Ibadan, Oyo State',
            '67 Awolowo Road, Ikoyi, Lagos',
        ]
        phones = ['08031234567', '08029876543', '07065432109', '09011223344']

        order_count = 0
        for i, customer in enumerate(customers):
            for j in range(3):  # 3 orders per customer = 12 sample orders total
                selected = random.sample(products, min(random.randint(1, 3), len(products)))
                items_data = [
                    {'product': p, 'quantity': random.randint(1, 5), 'unit_price': p.price}
                    for p in selected
                ]
                total = sum(d['quantity'] * d['unit_price'] for d in items_data)
                order, created = Order.objects.get_or_create(
                    user=customer,
                    phone=phones[i % len(phones)],
                    total_amount=total,
                    defaults=dict(
                        status=statuses[(i + j) % len(statuses)],
                        delivery_address=addresses[i % len(addresses)],
                        notes='',
                    ),
                )
                if created:
                    for d in items_data:
                        OrderItem.objects.create(order=order, **d)
                    order_count += 1

        self.stdout.write(f'  ✓ {len(customers)} sample customers, {order_count} sample orders (for analytics)')
