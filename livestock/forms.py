from django import forms
from .models import LivestockCategory, LivestockSpecies, FeedSchedule, GrowthBooster, SeasonalVariation, LivestockRecord, DailyFeedLog, DailyProductionLog

_SELECT_ATTRS = {'class': 'form-select'}
_INPUT_ATTRS  = {'class': 'form-control'}
_TEXTAREA_ATTRS = {'class': 'form-control', 'rows': 3}


class LivestockCategoryForm(forms.ModelForm):
    class Meta:
        model = LivestockCategory
        fields = ['name', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={**_INPUT_ATTRS, 'placeholder': 'e.g. Poultry, Fish, Piggery'}),
            'description': forms.Textarea(attrs={**_TEXTAREA_ATTRS, 'placeholder': 'Brief description of this livestock category'}),
        }


class LivestockSpeciesForm(forms.ModelForm):
    class Meta:
        model = LivestockSpecies
        fields = ['category', 'name', 'breed', 'description', 'image', 'current_stock']
        widgets = {
            'category': forms.Select(attrs=_SELECT_ATTRS),
            'name': forms.TextInput(attrs={**_INPUT_ATTRS, 'placeholder': 'e.g. Layer Hen, Catfish, Duroc Pig'}),
            'breed': forms.TextInput(attrs={**_INPUT_ATTRS, 'placeholder': 'e.g. ISA Brown, Clarias (optional)'}),
            'description': forms.Textarea(attrs={**_TEXTAREA_ATTRS, 'placeholder': 'Any notes about this species'}),
            'current_stock': forms.NumberInput(attrs={**_INPUT_ATTRS, 'placeholder': '0', 'min': '0'}),
        }


class FeedScheduleForm(forms.ModelForm):
    class Meta:
        model = FeedSchedule
        fields = ['species', 'feed_type', 'daily_quantity_kg', 'feeding_times', 'cost_per_kg', 'season', 'notes']
        widgets = {
            'species': forms.Select(attrs=_SELECT_ATTRS),
            'feed_type': forms.TextInput(attrs={**_INPUT_ATTRS, 'placeholder': 'e.g. Layer Mash, Starter Mash, Floating Pellets'}),
            'daily_quantity_kg': forms.NumberInput(attrs={**_INPUT_ATTRS, 'placeholder': '0.00', 'min': '0', 'step': '0.5', 'id': 'id_daily_quantity_kg'}),
            'feeding_times': forms.TextInput(attrs={
                **_INPUT_ATTRS,
                'placeholder': 'e.g. 7:00 AM, 12:00 PM, 5:00 PM',
                'id': 'id_feeding_times',
                'autocomplete': 'off',
            }),
            'cost_per_kg': forms.NumberInput(attrs={**_INPUT_ATTRS, 'placeholder': '0.00', 'min': '0', 'step': '0.01', 'id': 'id_cost_per_kg'}),
            'season': forms.Select(attrs=_SELECT_ATTRS),
            'notes': forms.Textarea(attrs={**_TEXTAREA_ATTRS, 'placeholder': 'Any extra notes about this feed schedule'}),
        }
        help_texts = {
            'daily_quantity_kg': 'Total kg of this feed type consumed per day by this species.',
            'cost_per_kg': 'What you pay per kg of this feed. Used to auto-calculate your daily feed cost.',
            'season': 'Set different schedules for dry vs rainy season if feeding amounts change.',
        }


class GrowthBoosterForm(forms.ModelForm):
    class Meta:
        model = GrowthBooster
        fields = ['species', 'name', 'booster_type', 'dosage', 'frequency', 'expected_impact', 'cost_per_unit']
        widgets = {
            'species': forms.Select(attrs=_SELECT_ATTRS),
            'name': forms.TextInput(attrs={**_INPUT_ATTRS, 'placeholder': 'e.g. VitaFarm Boost, AminoGrow'}),
            'booster_type': forms.TextInput(attrs={**_INPUT_ATTRS, 'placeholder': 'e.g. Vitamin supplement, Probiotic, Antibiotic'}),
            'dosage': forms.TextInput(attrs={**_INPUT_ATTRS, 'placeholder': 'e.g. 5ml per litre of water'}),
            'frequency': forms.TextInput(attrs={**_INPUT_ATTRS, 'placeholder': 'e.g. Daily, Every Monday, Weekly'}),
            'expected_impact': forms.Textarea(attrs={**_TEXTAREA_ATTRS, 'placeholder': 'e.g. Boosts egg production by ~10%, reduces mortality rate'}),
            'cost_per_unit': forms.NumberInput(attrs={**_INPUT_ATTRS, 'placeholder': '0.00', 'min': '0', 'step': '0.01'}),
        }


class SeasonalVariationForm(forms.ModelForm):
    class Meta:
        model = SeasonalVariation
        fields = ['species', 'season', 'production_impact', 'recommended_action', 'expected_yield_change_percent']
        widgets = {
            'species': forms.Select(attrs=_SELECT_ATTRS),
            'season': forms.TextInput(attrs={**_INPUT_ATTRS, 'placeholder': 'e.g. Harmattan, Rainy Season, Hot Dry Season'}),
            'production_impact': forms.Textarea(attrs={**_TEXTAREA_ATTRS, 'placeholder': 'e.g. Egg production drops by 15% due to heat stress in the pen'}),
            'recommended_action': forms.Textarea(attrs={**_TEXTAREA_ATTRS, 'placeholder': 'e.g. Increase water intake, reduce flock density, add electrolytes to water'}),
            'expected_yield_change_percent': forms.NumberInput(attrs={**_INPUT_ATTRS, 'placeholder': 'e.g. -15 or +8', 'step': '0.1'}),
        }
        help_texts = {
            'expected_yield_change_percent': 'Use negative numbers for drops (e.g. -15) and positive for gains (e.g. +8).',
        }


class LivestockRecordForm(forms.ModelForm):
    class Meta:
        model = LivestockRecord
        fields = ['species', 'date', 'quantity_added', 'quantity_removed', 'reason', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class DailyFeedLogForm(forms.ModelForm):
    class Meta:
        model = DailyFeedLog
        fields = ['date', 'species', 'feed_type', 'bags_consumed', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class DailyProductionLogForm(forms.ModelForm):
    class Meta:
        model = DailyProductionLog
        fields = ['date', 'species', 'product', 'quantity', 'unit', 'egg_count', 'damaged_count', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].help_text = 'Use Eggs for layer production so egg analytics and sales reporting stay accurate.'
        self.fields['egg_count'].help_text = 'Optional for eggs. If left blank, tray/crate or pieces quantity will be used to estimate it.'

    def clean(self):
        cleaned_data = super().clean()
        product = (cleaned_data.get('product') or '').strip().lower()
        quantity = cleaned_data.get('quantity')
        unit = cleaned_data.get('unit')
        egg_count = cleaned_data.get('egg_count')
        damaged_count = cleaned_data.get('damaged_count') or 0

        if 'egg' in product and egg_count is None and quantity is not None:
            if unit == 'pieces':
                egg_count = int(quantity)
            elif unit in ['crates', 'crate', 'tray']:
                egg_count = int(quantity * 30)
            cleaned_data['egg_count'] = egg_count

        if 'egg' in product and egg_count is None:
            self.add_error('egg_count', 'Enter the egg count or use pieces/tray/crate quantity for egg production.')

        if egg_count is not None and damaged_count > egg_count:
            self.add_error('damaged_count', 'Damaged eggs cannot exceed the total eggs collected.')

        return cleaned_data
