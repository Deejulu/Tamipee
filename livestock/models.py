from decimal import Decimal

from django.db import models


class LivestockCategory(models.Model):
    name = models.CharField(max_length=100)  # e.g. Poultry, Fish, Piggery
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='livestock/categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Livestock Categories'

    def __str__(self):
        return self.name


class LivestockSpecies(models.Model):
    category = models.ForeignKey(LivestockCategory, on_delete=models.CASCADE, related_name='species')
    name = models.CharField(max_length=100)  # e.g. Broiler, Catfish, Duroc Pig
    breed = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='livestock/species/', blank=True, null=True)
    current_stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Livestock Species'

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class FeedSchedule(models.Model):
    SEASON_CHOICES = [
        ('all', 'All Seasons'),
        ('dry', 'Dry Season'),
        ('rainy', 'Rainy Season'),
    ]
    species = models.ForeignKey(LivestockSpecies, on_delete=models.CASCADE, related_name='feed_schedules')
    feed_type = models.CharField(max_length=150)
    daily_quantity_kg = models.DecimalField(max_digits=8, decimal_places=2)
    feeding_times = models.CharField(max_length=200, help_text='e.g. 7am, 12pm, 5pm')
    cost_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    season = models.CharField(max_length=10, choices=SEASON_CHOICES, default='all')
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.species.name} - {self.feed_type}"

    @property
    def daily_cost(self):
        return self.daily_quantity_kg * self.cost_per_kg


class GrowthBooster(models.Model):
    species = models.ForeignKey(LivestockSpecies, on_delete=models.CASCADE, related_name='growth_boosters')
    name = models.CharField(max_length=150)
    booster_type = models.CharField(max_length=100, help_text='e.g. Vitamin supplement, Probiotic')
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100, help_text='e.g. Daily, Weekly')
    expected_impact = models.TextField(help_text='Describe how this impacts production/growth')
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} for {self.species.name}"


class SeasonalVariation(models.Model):
    species = models.ForeignKey(LivestockSpecies, on_delete=models.CASCADE, related_name='seasonal_variations')
    season = models.CharField(max_length=50)
    production_impact = models.TextField()
    recommended_action = models.TextField()
    expected_yield_change_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.species.name} - {self.season}"


class LivestockRecord(models.Model):
    species = models.ForeignKey(LivestockSpecies, on_delete=models.CASCADE, related_name='records')
    date = models.DateField()
    quantity_added = models.PositiveIntegerField(default=0)
    quantity_removed = models.PositiveIntegerField(default=0)
    reason = models.CharField(max_length=200, blank=True, help_text='e.g. Sale, Death, Transfer')
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, related_name='livestock_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.species.name} record - {self.date}"


class DailyFeedLog(models.Model):
    """Actual feed consumed on a given day (in bags), entered by staff/admin."""
    date = models.DateField()
    species = models.ForeignKey(LivestockSpecies, on_delete=models.CASCADE, related_name='feed_logs')
    feed_type = models.CharField(max_length=150, help_text='e.g. Layer Mash')
    bags_consumed = models.DecimalField(max_digits=6, decimal_places=1, help_text='Number of bags used today')
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='feed_logs_entered',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} | {self.species.name} — {self.bags_consumed} bag(s) of {self.feed_type}"


class DailyProductionLog(models.Model):
    """Daily output record — eggs collected, fish harvested, etc."""
    UNIT_CHOICES = [
        ('crates', 'Crates'),
        ('tray', 'Tray'),
        ('crate', 'Crate'),
        ('kg', 'kg'),
        ('pieces', 'Pieces'),
        ('litres', 'Litres'),
    ]
    date = models.DateField()
    species = models.ForeignKey(LivestockSpecies, on_delete=models.CASCADE, related_name='production_logs')
    product = models.CharField(max_length=100, help_text='e.g. Eggs, Catfish Harvest')
    quantity = models.DecimalField(max_digits=8, decimal_places=1)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='crates')
    egg_count = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='Optional for layer production: total eggs collected before sorting.',
    )
    damaged_count = models.PositiveIntegerField(
        default=0,
        help_text='Cracked, dirty, or otherwise unsellable eggs from the batch.',
    )
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='production_logs_entered',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    @property
    def saleable_quantity(self):
        if self.egg_count is None:
            return self.quantity
        return max(self.egg_count - self.damaged_count, 0)

    @property
    def estimated_trays(self):
        if self.egg_count is None:
            return None
        return Decimal(self.saleable_quantity) / Decimal('30')

    def __str__(self):
        return f"{self.date} | {self.species.name} — {self.quantity} {self.unit} of {self.product}"

