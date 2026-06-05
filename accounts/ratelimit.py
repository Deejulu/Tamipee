"""
Simple rate limiting for registration without external dependencies.
"""
from django.core.cache import cache
from django.http import HttpResponseForbidden
from functools import wraps
from datetime import timedelta


def get_client_ip_simple(request):
    """Get client IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ratelimit_registration(max_attempts=5, window_minutes=60):
    """
    Rate limit decorator for registration view.
    
    Args:
        max_attempts: Maximum registration attempts allowed
        window_minutes: Time window in minutes
    
    Returns:
        Decorated view function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.method != 'POST':
                # Only rate limit POST requests (actual registrations)
                return view_func(request, *args, **kwargs)
            
            ip = get_client_ip_simple(request)
            cache_key = f'register_ratelimit_{ip}'
            
            # Get current attempt count
            attempts = cache.get(cache_key, 0)
            
            if attempts >= max_attempts:
                from django.contrib import messages
                messages.error(
                    request,
                    f'Too many registration attempts from your location. '
                    f'Please try again in {window_minutes} minutes or contact support.'
                )
                from django.shortcuts import render
                from accounts.forms import CustomerRegistrationForm
                return render(request, 'accounts/register.html', {'form': CustomerRegistrationForm()})
            
            # Increment attempt counter
            cache.set(cache_key, attempts + 1, window_minutes * 60)
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


def ratelimit_password_reset(max_attempts=10, window_minutes=60):
    """
    Rate limit decorator for password reset attempts.
    
    Args:
        max_attempts: Maximum password reset attempts allowed
        window_minutes: Time window in minutes
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.method != 'POST':
                return view_func(request, *args, **kwargs)
            
            ip = get_client_ip_simple(request)
            cache_key = f'password_reset_ratelimit_{ip}'
            
            attempts = cache.get(cache_key, 0)
            
            if attempts >= max_attempts:
                from django.contrib import messages
                messages.error(
                    request,
                    f'Too many password reset attempts. Please try again in {window_minutes} minutes.'
                )
                from django.shortcuts import redirect
                return redirect('accounts:login')
            
            cache.set(cache_key, attempts + 1, window_minutes * 60)
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator
