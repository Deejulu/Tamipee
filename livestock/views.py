from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import role_required
from .models import LivestockCategory, LivestockSpecies, FeedSchedule, GrowthBooster, SeasonalVariation, LivestockRecord
from .forms import LivestockCategoryForm, LivestockSpeciesForm, FeedScheduleForm, GrowthBoosterForm, SeasonalVariationForm, LivestockRecordForm


@login_required
def livestock_list(request):
    categories = LivestockCategory.objects.prefetch_related('species').all()
    return render(request, 'livestock/list.html', {'categories': categories})


@login_required
def livestock_detail(request, pk):
    species = get_object_or_404(LivestockSpecies, pk=pk)
    return render(request, 'livestock/detail.html', {'species': species})


@login_required
def category_detail(request, pk):
    category = get_object_or_404(LivestockCategory, pk=pk)
    species_list = category.species.all()
    return render(request, 'livestock/category_detail.html', {'category': category, 'species_list': species_list})


@role_required('admin', 'staff')
def add_livestock(request):
    form = LivestockSpeciesForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Livestock species added successfully.')
        return redirect('livestock:list')
    return render(request, 'livestock/form.html', {'form': form, 'title': 'Add Livestock'})


@role_required('admin', 'staff')
def edit_livestock(request, pk):
    species = get_object_or_404(LivestockSpecies, pk=pk)
    form = LivestockSpeciesForm(request.POST or None, request.FILES or None, instance=species)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Livestock species updated.')
        return redirect('livestock:list')
    return render(request, 'livestock/form.html', {'form': form, 'title': 'Edit Livestock'})


@role_required('admin', 'staff')
def delete_livestock(request, pk):
    species = get_object_or_404(LivestockSpecies, pk=pk)
    if request.method == 'POST':
        species.delete()
        messages.success(request, 'Livestock species deleted.')
    return redirect('livestock:list')


@role_required('admin', 'staff')
def feed_log(request, pk):
    species = get_object_or_404(LivestockSpecies, pk=pk)
    schedules = species.feed_schedules.all()
    form = FeedScheduleForm(request.POST or None, initial={'species': species})
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Feed schedule saved.')
        return redirect('livestock:feed_log', pk=pk)
    return render(request, 'livestock/feed_log.html', {'species': species, 'schedules': schedules, 'form': form})


@role_required('admin', 'staff')
def growth_log(request, pk):
    species = get_object_or_404(LivestockSpecies, pk=pk)
    boosters = species.growth_boosters.all()
    form = GrowthBoosterForm(request.POST or None, initial={'species': species})
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Growth booster record saved.')
        return redirect('livestock:growth_log', pk=pk)
    return render(request, 'livestock/growth_log.html', {'species': species, 'boosters': boosters, 'form': form})


@role_required('admin', 'staff')
def seasonal_view(request, pk):
    species = get_object_or_404(LivestockSpecies, pk=pk)
    variations = species.seasonal_variations.all()
    form = SeasonalVariationForm(request.POST or None, initial={'species': species})
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Seasonal variation saved.')
        return redirect('livestock:seasonal', pk=pk)
    return render(request, 'livestock/seasonal.html', {'species': species, 'variations': variations, 'form': form})


