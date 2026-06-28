from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboards
    path('admin/', views.admin_dashboard, name='admin'),
    path('staff/', views.staff_dashboard, name='staff'),
    path('customer/', views.customer_dashboard, name='customer'),

    # Admin: user management
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/add-staff/', views.admin_add_staff, name='admin_add_staff'),
    path('admin/users/add-customer/', views.admin_add_customer, name='admin_add_customer'),
    path('admin/users/<int:pk>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/users/<int:pk>/update-role/', views.admin_update_user_role, name='admin_update_user_role'),
    path('admin/users/<int:pk>/delete/', views.admin_delete_user, name='admin_delete_user'),


    # Admin: orders & payments
    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('admin/payments/', views.admin_payments, name='admin_payments'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),

    # Admin: site & marketing hubs
    path('admin/site/', views.admin_site_management, name='admin_site_management'),
    path('admin/marketing/', views.admin_marketing, name='admin_marketing'),

    # Admin: site content
    path('admin/site/hero/', views.admin_manage_hero, name='admin_manage_hero'),
    path('admin/site/pages/', views.admin_manage_pages, name='admin_manage_pages'),
    path('admin/site/banners/', views.admin_manage_banners, name='admin_manage_banners'),
    path('admin/site/testimonials/', views.admin_manage_testimonials, name='admin_manage_testimonials'),
    path('admin/site/faqs/', views.admin_manage_faqs, name='admin_manage_faqs'),
    path('admin/site/contact/', views.admin_manage_contact_info, name='admin_manage_contact_info'),

    # Admin: products
    path('admin/products/', views.admin_manage_products, name='admin_manage_products'),
    path('admin/products/add/', views.admin_manage_product_form, name='admin_manage_product_form'),
    path('admin/products/edit/<int:pk>/', views.admin_manage_product_form, name='admin_edit_product'),
    path('admin/products/delete/<int:pk>/', views.admin_delete_product, name='admin_delete_product'),

    # Admin: livestock categories & species
    path('admin/livestock/', views.admin_livestock, name='admin_livestock'),
    path('admin/farm-overview/', views.admin_farm_overview, name='admin_farm_overview'),
    path('admin/livestock/categories/', views.admin_manage_categories, name='admin_manage_categories'),
    path('admin/livestock/categories/add/', views.admin_manage_category_form, name='admin_manage_category_form'),
    path('admin/livestock/categories/edit/<int:pk>/', views.admin_manage_category_form, name='admin_edit_category'),
    path('admin/livestock/categories/delete/<int:pk>/', views.admin_delete_category, name='admin_delete_category'),
    path('admin/livestock/species/add/', views.admin_manage_livestock_form, name='admin_manage_livestock_form'),
    path('admin/livestock/species/edit/<int:pk>/', views.admin_manage_livestock_form, name='admin_edit_livestock'),
    path('admin/livestock/species/delete/<int:pk>/', views.admin_delete_livestock, name='admin_delete_livestock'),
    path('admin/livestock/feed/', views.admin_manage_feed_form, name='admin_manage_feed_form'),
    path('admin/livestock/feed/edit/<int:pk>/', views.admin_manage_feed_form, name='admin_edit_feed'),
    path('admin/livestock/boosters/', views.admin_manage_boosters, name='admin_manage_boosters'),
    path('admin/livestock/boosters/delete/<int:pk>/', views.admin_delete_booster, name='admin_delete_booster'),
    path('admin/livestock/seasonal/', views.admin_manage_seasonal, name='admin_manage_seasonal'),
    path('admin/livestock/seasonal/delete/<int:pk>/', views.admin_delete_seasonal, name='admin_delete_seasonal'),
    path('admin/daily-log/', views.admin_daily_log, name='admin_daily_log'),
    path('admin/daily-log/feed/delete/<int:pk>/', views.admin_delete_feed_log, name='admin_delete_feed_log'),
    path('admin/daily-log/production/delete/<int:pk>/', views.admin_delete_production_log, name='admin_delete_production_log'),

    # Admin: marketing
    path('admin/marketing/promotions/', views.admin_manage_promotions, name='admin_manage_promotions'),
    path('admin/marketing/promotions/add/', views.admin_manage_promo_form, name='admin_manage_promo_form'),
    path('admin/marketing/promotions/edit/<int:pk>/', views.admin_manage_promo_form, name='admin_edit_promo'),
    path('admin/marketing/promotions/delete/<int:pk>/', views.admin_delete_promo, name='admin_delete_promo'),
    path('admin/marketing/newsletter/', views.admin_manage_newsletter, name='admin_manage_newsletter'),
    path('admin/marketing/announcements/', views.admin_manage_announcements, name='admin_manage_announcements'),
    path('admin/marketing/announcements/delete/<int:pk>/', views.admin_delete_announcement, name='admin_delete_announcement'),
    path('admin/contact-messages/', views.admin_contact_messages, name='admin_contact_messages'),

    # Admin: site content delete
    path('admin/site/banners/delete/<int:pk>/', views.admin_delete_banner, name='admin_delete_banner'),
    path('admin/site/testimonials/delete/<int:pk>/', views.admin_delete_testimonial, name='admin_delete_testimonial'),
    path('admin/site/faqs/delete/<int:pk>/', views.admin_delete_faq, name='admin_delete_faq'),

    # Admin: sample data tools
    path('admin/sample-data/', views.admin_sample_data_tools, name='admin_sample_data_tools'),
    path('admin/sample-data/populate/', views.admin_populate_sample_data, name='admin_populate_sample_data'),
    path('admin/sample-data/delete/', views.admin_delete_sample_data, name='admin_delete_sample_data'),

    # Staff
    path('staff/livestock/', views.staff_livestock, name='staff_livestock'),
    path('staff/feed/', views.staff_feed, name='staff_feed'),
    path('staff/orders/', views.staff_orders, name='staff_orders'),
    path('orders/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),

    # Customer
    path('customer/orders/', views.customer_orders, name='customer_orders'),
    path('customer/wishlist/', views.customer_wishlist, name='customer_wishlist'),
]

