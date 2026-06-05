from django.urls import path
from . import views

app_name = 'livestock'

urlpatterns = [
    path('', views.livestock_list, name='list'),
    path('category/<int:pk>/', views.category_detail, name='category_detail'),
    path('species/<int:pk>/', views.livestock_detail, name='detail'),
    path('add/', views.add_livestock, name='add'),
    path('edit/<int:pk>/', views.edit_livestock, name='edit'),
    path('delete/<int:pk>/', views.delete_livestock, name='delete'),
    path('species/<int:pk>/feed/', views.feed_log, name='feed_log'),
    path('species/<int:pk>/growth/', views.growth_log, name='growth_log'),
    path('species/<int:pk>/seasonal/', views.seasonal_view, name='seasonal'),
]

