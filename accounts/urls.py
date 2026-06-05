from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),

    # Email verification (legacy - may not be used)
    path('verify-email/<int:user_id>/', views.verify_email, name='verify_email'),
    path('resend-otp/<int:user_id>/', views.resend_otp, name='resend_otp'),

    # New password reset with security questions
    path('forgot-password/', views.forgot_password_search, name='forgot_password_search'),
    path('forgot-password/verify/', views.forgot_password_verify, name='forgot_password_verify'),
    path('forgot-password/reset/', views.forgot_password_reset, name='forgot_password_reset'),
    
    # Recovery code regeneration
    path('regenerate-recovery-code/', views.regenerate_recovery_code_confirm, name='regenerate_recovery_code_confirm'),
    path('regenerate-recovery-code/process/', views.regenerate_recovery_code, name='regenerate_recovery_code'),
    
    # Credential downloads (PDF, PNG)
    path('download-credentials-pdf/<int:user_id>/', views.download_credentials_pdf, name='download_credentials_pdf'),
    path('download-credentials-image/<int:user_id>/', views.download_credentials_image, name='download_credentials_image'),
    
    # Legacy password reset URLs (redirect to new flow)
    path('password-reset/', views.direct_password_reset, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password-reset-complete/',
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]
