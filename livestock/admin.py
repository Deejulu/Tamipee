from django.contrib import admin
from .models import LivestockCategory, LivestockSpecies, FeedSchedule, GrowthBooster, SeasonalVariation, LivestockRecord


@admin.register(LivestockCategory)
class LivestockCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(LivestockSpecies)
class LivestockSpeciesAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'breed', 'current_stock', 'created_at']
    list_filter = ['category']
    search_fields = ['name', 'breed']


@admin.register(FeedSchedule)
class FeedScheduleAdmin(admin.ModelAdmin):
    list_display = ['species', 'feed_type', 'daily_quantity_kg', 'cost_per_kg', 'season']
    list_filter = ['season', 'species__category']
    search_fields = ['feed_type', 'species__name']


@admin.register(GrowthBooster)
class GrowthBoosterAdmin(admin.ModelAdmin):
    list_display = ['name', 'species', 'booster_type', 'frequency', 'cost_per_unit']
    list_filter = ['species__category']
    search_fields = ['name', 'booster_type']


@admin.register(SeasonalVariation)
class SeasonalVariationAdmin(admin.ModelAdmin):
    list_display = ['species', 'season', 'expected_yield_change_percent']
    list_filter = ['season']


@admin.register(LivestockRecord)
class LivestockRecordAdmin(admin.ModelAdmin):
    list_display = ['species', 'date', 'quantity_added', 'quantity_removed', 'reason', 'recorded_by']
    list_filter = ['species__category', 'date']
    search_fields = ['species__name', 'reason']

