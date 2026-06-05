from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initiate/', views.initiate_payment, name='initiate'),
    path('verify/', views.verify_payment, name='verify'),
    path('callback/', views.payment_callback, name='callback'),
    path('success/', views.payment_success, name='success'),
    path('failed/', views.payment_failed, name='failed'),
]

