"""
Session timeout middleware for automatic logout after inactivity.
"""
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime


class SessionIdleTimeoutMiddleware:
    """
    Log out users after 30 minutes of inactivity.
    
    This middleware tracks the last activity timestamp in the session
    and automatically logs out users who have been idle for too long.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.idle_timeout = 1800  # 30 minutes in seconds
    
    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            now = timezone.now()
            
            if last_activity:
                # Parse ISO format timestamp
                try:
                    if isinstance(last_activity, str):
                        last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    else:
                        last_activity_dt = last_activity
                    
                    # Make timezone-aware if needed
                    if timezone.is_naive(last_activity_dt):
                        last_activity_dt = timezone.make_aware(last_activity_dt)
                    
                    # Calculate idle time
                    idle_time = (now - last_activity_dt).total_seconds()
                    
                    if idle_time > self.idle_timeout:
                        # Log out due to inactivity
                        logout(request)
                        messages.warning(
                            request,
                            f'You have been logged out due to {int(idle_time/60)} minutes of inactivity. '
                            'Please log in again.'
                        )
                        # Don't redirect here - let the view handle it
                        # The user will see the warning on next page load
                except (ValueError, TypeError):
                    # Invalid timestamp, just update it
                    pass
            
            # Update last activity timestamp
            request.session['last_activity'] = now.isoformat()
        
        response = self.get_response(request)
        return response
