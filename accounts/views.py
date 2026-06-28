from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.contrib.sessions.models import Session
from datetime import timedelta
from .forms import CustomerRegistrationForm, UserLoginForm, ProfileUpdateForm
from .models import EmailVerification, UserSecurityAnswer, PasswordResetAttempt
from .ratelimit import ratelimit_registration, ratelimit_password_reset


def register_view(request):
    # Allow authenticated admins/superusers to open the customer registration page.
    # We only block if the currently logged-in user is already a customer.
    if request.user.is_authenticated and getattr(request.user, 'role', None) == 'customer':
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Get data from user object (set in form.save())
            recovery_codes = getattr(user, 'plain_recovery_codes', [])
            plain_password = getattr(user, 'plain_password', '')
            security_qa_pairs = getattr(user, 'security_qa_pairs', [])  # List of (question, answer) tuples
            
            # Generate OTP for email verification
            verification, plain_otp = EmailVerification.create_for_user(user)
            
            # Format recovery codes for email
            codes_text = '\n'.join([f"{i+1}. {code}" for i, code in enumerate(recovery_codes)])
            
            # Send verification email
            try:
                send_mail(
                    subject='Email Verification - Tamipee Integrated Farms',
                    message=f'''Hello {user.first_name},

Welcome to Tamipee Integrated Farms!

Your account has been created successfully. Please verify your email address to activate your account.

Your 6-digit verification code is: {plain_otp}

This code will expire in 15 minutes.

Your account details:
Username: {user.username}

Your 7 Recovery Codes (save these securely):
{codes_text}

IMPORTANT: Save your recovery codes in a safe place. Each code can only be used ONCE if you forget your password.

If you didn't create this account, please ignore this email.

Best regards,
Tamipee Integrated Farms Team
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                    timeout=10,  # 10 second timeout to prevent worker hangs
                )
            except Exception as e:
                # Log email-sending problems but continue registration flow
                import logging
                logger = logging.getLogger(__name__)
                logger.exception('Failed to send verification code email: %s', e)
                
                # Show warning but don't block registration
                messages.warning(
                    request, 
                    'Account created successfully, but verification email could not be sent. '
                    'Your OTP code is displayed below.'
                )

            
            # Store OTP in session for DEBUG mode (local testing only)
            if settings.DEBUG:
                request.session[f'debug_otp_{user.pk}'] = plain_otp
                request.session.set_expiry(900)  # 15 minutes
            
            # Store credentials in session for download (temporary - expires after 1 hour)
            request.session[f'credentials_{user.pk}'] = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'password': plain_password,
                'recovery_codes': recovery_codes,
                'security_qa_pairs': security_qa_pairs,  # Store Q&A pairs
                'email': user.email,
                'created_at': timezone.now().isoformat(),
            }
            request.session.set_expiry(3600)  # Expire session data after 1 hour
            
            # Show success page with all user information
            return render(request, 'accounts/register_success.html', {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'password': plain_password,
                'recovery_codes': recovery_codes,
                'security_qa_pairs': security_qa_pairs,  # Pass Q&A pairs to template
                'user_email': user.email,
                'user_id': user.pk,
            })
        else:
            # Form has validation errors - add a general error message
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    from .models import LoginHistory
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        username_or_email = request.POST.get('username', '')
        
        # Try to get user for lockout check (before authentication)
        # Support both username and email
        User = get_user_model()
        user = None
        try:
            # Check if input looks like an email
            if '@' in username_or_email:
                user = User.objects.get(email__iexact=username_or_email)
            else:
                user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            user = None
        
        # Check if account is locked (before attempting authentication)
        if user and user.is_locked():
            minutes_remaining = int((user.locked_until - timezone.now()).total_seconds() / 60)
            messages.error(
                request,
                f'Account locked due to too many failed login attempts. '
                f'Try again in {minutes_remaining} minutes or contact admin.'
            )
            return render(request, 'accounts/login.html', {'form': form})
        
        # Check if email is not verified (account inactive)
        if user and not user.is_active:
            messages.error(
                request,
                'Your email is not verified. Please check your email for the verification code.'
            )
            # Provide link to resend verification
            messages.info(
                request,
                f'<a href="/accounts/verify-email/{user.pk}/" class="alert-link">Click here to verify your email</a>',
                extra_tags='safe'
            )
            return render(request, 'accounts/login.html', {'form': form})
        
        if form.is_valid():
            user = form.get_user()
            
            # Check for suspicious login (new IP address)
            ip = get_client_ip(request)
            is_suspicious, reason = LoginHistory.check_suspicious_login(user, ip)
            
            if is_suspicious:
                # Record suspicious login
                LoginHistory.record_login(user, request, is_successful=True)
                messages.warning(
                    request,
                    f'Security Alert: {reason}. If this wasn\'t you, change your password immediately.'
                )
            else:
                # Record successful login
                LoginHistory.record_login(user, request, is_successful=True)
            
            # Reset failed login counter
            user.reset_failed_logins()
            
            # Login user
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('accounts:dashboard')
        else:
            # Failed login
            if user:
                user.record_failed_login()
                LoginHistory.record_login(
                    user, request, 
                    is_successful=False, 
                    failure_reason='Invalid password'
                )
                
                # Show specific lockout message if this failure caused a lock
                if user.is_locked():
                    minutes = int((user.locked_until - timezone.now()).total_seconds() / 60)
                    messages.error(
                        request,
                        f'Too many failed attempts. Account locked for {minutes} minutes.'
                    )
                else:
                    remaining_attempts = 3 - user.failed_login_attempts
                    if remaining_attempts > 0:
                        messages.error(
                            request,
                            f'Invalid username or password. {remaining_attempts} attempts remaining before lockout.'
                        )
                    else:
                        messages.error(request, 'Invalid username or password.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def dashboard_redirect(request):
    # Superusers always go to admin dashboard regardless of role field
    if request.user.is_superuser:
        return redirect('dashboard:admin')
    role = request.user.role
    if role == 'admin':
        return redirect('dashboard:admin')
    elif role == 'staff':
        return redirect('dashboard:staff')
    else:
        return redirect('dashboard:customer')


def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def invalidate_all_user_sessions(user):
    """
    Invalidate all sessions for a specific user (logout from all devices).
    Call this after password reset for security.
    """
    # Get all active sessions
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    
    for session in sessions:
        session_data = session.get_decoded()
        # Check if this session belongs to the user
        if session_data.get('_auth_user_id') == str(user.id):
            session.delete()


@ratelimit_password_reset(max_attempts=10, window_minutes=60)
def forgot_password_search(request):
    """Step 1: Identify account by first name, last name, and recovery code (prevents username enumeration and duplicate name issues)."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        recovery_code = request.POST.get('recovery_code', '').strip()
        
        if not first_name or not last_name or not recovery_code:
            messages.error(request, 'Please provide your first name, last name, and recovery code.')
            return render(request, 'accounts/forgot_password_search.html')
        
        # Find user by name AND recovery code (solves duplicate name issue)
        User = get_user_model()
        users_with_name = User.objects.filter(
            first_name__iexact=first_name,
            last_name__iexact=last_name,
            role='customer'
        )
        
        # Find the one with matching recovery code
        user = None
        for potential_user in users_with_name:
            if potential_user.check_recovery_code(recovery_code):
                user = potential_user
                break
        
        if not user:
            # Generic error (don't reveal if name exists but code is wrong)
            messages.error(
                request,
                'Account not found or recovery code incorrect. '
                'Please check your information or contact admin.'
            )
            return render(request, 'accounts/forgot_password_search.html')
        
        # Store user ID (not name) in session for next step
        request.session['password_reset_user_id'] = user.id
        messages.info(request, 'Account verified. Please answer your security questions.')
        return redirect('accounts:forgot_password_verify')
    
    return render(request, 'accounts/forgot_password_search.html')


def forgot_password_verify(request):
    """Step 2: Verify security questions and recovery code."""
    # Get user identification from session
    first_name = request.session.get('reset_first_name')
    last_name = request.session.get('reset_last_name')
    
    if not first_name or not last_name:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('accounts:forgot_password_search')
    
    User = get_user_model()
    
    # Try to find user (don't reveal if not found)
    try:
        user = User.objects.get(
            first_name__iexact=first_name,
            last_name__iexact=last_name,
            role='customer'
        )
    except User.DoesNotExist:
        user = None
    except User.MultipleObjectsReturned:
        # Multiple users with same name - need more specific identification
        messages.error(
            request,
            'Multiple accounts found with this name. Please contact admin for assistance.'
        )
        return redirect('accounts:login')
    
    # Check rate limiting regardless of whether user exists
    ip_address = get_client_ip(request)
    if user:
        can_attempt, reason = PasswordResetAttempt.can_attempt_reset(user, ip_address)
        if not can_attempt:
            messages.error(request, reason)
            return redirect('accounts:login')
    
    # Get security questions (or generic ones if user doesn't exist)
    if user:
        security_answers = UserSecurityAnswer.objects.filter(user=user).select_related('question')
        if security_answers.count() < 3:
            messages.error(
                request,
                'Account recovery not available. Please contact admin for assistance.'
            )
            return redirect('accounts:login')
    else:
        # Show generic questions to prevent user enumeration
        from .models import SecurityQuestion
        security_answers = SecurityQuestion.objects.filter(is_active=True)[:3]
    
    if request.method == 'POST':
        recovery_code = request.POST.get('recovery_code', '').strip()
        
        # Always verify, even if user doesn't exist (timing attack prevention)
        verification_passed = False
        
        if user:
            # Create password reset attempt record
            attempt = PasswordResetAttempt.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                questions_answered=3
            )
            
            # Verify recovery code first
            if not user.check_recovery_code(recovery_code):
                attempt.correct_answers = 0
                attempt.mark_failed()
                messages.error(
                    request,
                    'Verification failed. Recovery code or security answers incorrect.'
                )
                return redirect('accounts:login')
            
            # Verify answers
            correct_count = 0
            for i, security_answer in enumerate(security_answers, 1):
                user_answer = request.POST.get(f'answer_{i}', '').strip()
                if security_answer.check_answer(user_answer):
                    correct_count += 1
            
            attempt.correct_answers = correct_count
            attempt.save()
            
            # Check if user got at least 2 out of 3 correct
            if correct_count >= 2:
                attempt.mark_success()
                verification_passed = True
            else:
                attempt.mark_failed()
                
                # Check if user has too many failed attempts
                recent_failed = PasswordResetAttempt.objects.filter(
                    user=user,
                    status__in=['failed', 'locked'],
                    created_at__gte=timezone.now() - timedelta(hours=1)
                ).count()
                
                if recent_failed >= 3:
                    attempt.lock_account(minutes=30)
                    attempt.require_admin_review()
        else:
            # User doesn't exist - simulate processing time (timing attack prevention)
            import time
            time.sleep(0.5)
        
        if verification_passed:
            # Store verified user in session
            request.session['password_reset_user_id'] = user.id
            request.session['password_reset_verified'] = True
            messages.success(
                request,
                'Verification successful! You can now reset your password.'
            )
            return redirect('accounts:forgot_password_reset')
        else:
            messages.error(
                request,
                'Verification failed. Please check your recovery code and security answers.'
            )
            return redirect('accounts:login')
    
    # Display verification form
    context = {
        'first_name': first_name,
        'last_name': last_name,
        'security_answers': security_answers,
        'has_user': user is not None,  # For template logic only
    }
    return render(request, 'accounts/forgot_password_verify.html', context)


def forgot_password_reset(request):
    """Step 3: Set new password after successful verification."""
    # Check if user has been verified
    if not request.session.get('password_reset_verified'):
        messages.error(request, 'Please complete security verification first.')
        return redirect('accounts:forgot_password_search')
    
    user_id = request.session.get('password_reset_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('accounts:forgot_password_search')
    
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('accounts:forgot_password_search')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if not password1 or not password2:
            messages.error(request, 'Please fill in both password fields.')
            return render(request, 'accounts/forgot_password_reset.html', {'username': user.username})
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/forgot_password_reset.html', {'username': user.username})
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'accounts/forgot_password_reset.html', {'username': user.username})
        
        # Check password history (prevent reuse of last 5 passwords)
        from .models import PasswordHistory
        is_reused, message = PasswordHistory.check_password_reuse(user, password1, history_count=5)
        if is_reused:
            messages.error(request, message)
            return render(request, 'accounts/forgot_password_reset.html', {'username': user.username})
        
        # Add current password to history BEFORE changing
        if user.password:  # Only if user has existing password
            PasswordHistory.add_password_to_history(user, user.password)
        
        # Set new password
        user.set_password(password1)
        user.save()
        
        # SECURITY: Invalidate all existing sessions (logout from all devices)
        invalidate_all_user_sessions(user)
        
        # Clear session data
        request.session.pop('password_reset_user_id', None)
        request.session.pop('password_reset_verified', None)
        request.session.pop('reset_first_name', None)
        request.session.pop('reset_last_name', None)
        
        messages.success(
            request,
            'Password reset successful! You can now log in with your new password.'
        )
        return redirect('accounts:login')
    
    return render(request, 'accounts/forgot_password_reset.html', {'username': user.username})


# Legacy view - kept for backward compatibility
def direct_password_reset(request):
    """Redirect to new password reset flow."""
    return redirect('accounts:forgot_password_search')


def verify_email(request, user_id):
    """View for users to enter their OTP code to verify email."""
    User = get_user_model()
    
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('accounts:login')
    
    # If user is already verified, redirect to login
    if user.is_active and user.email_verified:
        messages.info(request, 'Your email is already verified. Please login.')
        return redirect('accounts:login')
    
    # Get the latest active verification for this user
    verification = EmailVerification.objects.filter(
        user=user,
        is_used=False
    ).order_by('-created_at').first()
    
    if not verification:
        messages.error(request, 'No active verification code found. Please request a new one.')
        return render(request, 'accounts/verify_email.html', {'user': user, 'no_code': True})
    
    # Check if account is locked
    if verification.locked_until and timezone.now() < verification.locked_until:
        minutes_left = int((verification.locked_until - timezone.now()).total_seconds() / 60)
        messages.error(
            request,
            f'Too many failed attempts. Account locked for {minutes_left} more minutes. Please try again later.'
        )
        return render(request, 'accounts/verify_email.html', {'user': user, 'locked': True})
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code:
            messages.error(request, 'Please enter the verification code.')
            return render(request, 'accounts/verify_email.html', {'user': user})
        
        # Check if OTP is still valid
        if not verification.is_valid():
            if verification.attempts >= 5:
                messages.error(request, 'Too many failed attempts. Please request a new code.')
            elif timezone.now() > verification.expires_at:
                messages.error(request, 'Verification code has expired. Please request a new one.')
            else:
                messages.error(request, 'Verification code is no longer valid. Please request a new one.')
            return render(request, 'accounts/verify_email.html', {'user': user, 'expired': True})
        
        # Verify the OTP
        if verification.check_otp(otp_code):
            # Success! Activate the user
            verification.mark_as_used()
            user.is_active = True
            user.email_verified = True
            user.save()
            
            messages.success(request, 'Email verified successfully! You can now login to your account.')
            return redirect('accounts:login')
        else:
            # Failed attempt
            verification.increment_attempts()
            attempts_left = 5 - verification.attempts
            
            if attempts_left > 0:
                messages.error(
                    request,
                    f'Invalid verification code. You have {attempts_left} attempt(s) remaining.'
                )
            else:
                messages.error(
                    request,
                    'Too many failed attempts. Your account has been locked for 15 minutes. Please request a new code after that.'
                )
            
            return render(request, 'accounts/verify_email.html', {'user': user})
    
    # Calculate time remaining
    time_left = verification.expires_at - timezone.now()
    minutes_left = int(time_left.total_seconds() / 60)
    
    # Get debug OTP from session if available (DEBUG mode only)
    debug_otp = None
    if settings.DEBUG:
        debug_otp = request.session.get(f'debug_otp_{user.pk}')
    
    context = {
        'user': user,
        'minutes_left': minutes_left if minutes_left > 0 else 0,
        'attempts_left': 5 - verification.attempts,
        'debug_mode': settings.DEBUG,
        'debug_otp': debug_otp,
    }
    
    return render(request, 'accounts/verify_email.html', context)


def resend_otp(request, user_id):
    """Resend OTP verification code to user's email."""
    User = get_user_model()
    
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Invalid request.')
        return redirect('accounts:login')
    
    # Check if user is already verified
    if user.is_active and user.email_verified:
        messages.info(request, 'Your email is already verified. Please login.')
        return redirect('accounts:login')
    
    # Rate limiting: Check if a code was sent recently (cooldown 2 minutes)
    recent_verification = EmailVerification.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(minutes=2)
    ).first()
    
    if recent_verification:
        messages.warning(
            request,
            "Please wait 2 minutes before requesting a new code. Check your spam folder if you haven't received it."
        )
        return redirect('accounts:verify_email', user_id=user.pk)
    
    # Generate new OTP
    verification, plain_otp = EmailVerification.create_for_user(user)
    
    # Send new OTP via email
    try:
        send_mail(
            subject='New Verification Code - Tamipee Integrated Farms',
            message=f'''
Hello {user.username},

You requested a new verification code.

Your new email verification code is: {plain_otp}

This code will expire in 15 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Tamipee Integrated Farms Team
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            timeout=10,  # 10 second timeout to prevent worker hangs
        )
        
        # Different success messages for DEBUG vs production
        if settings.DEBUG:
            messages.success(request, f'✅ NEW OTP GENERATED: {plain_otp} (This message only shows in local development)')
        else:
            messages.success(request, f'New verification code sent to {user.email}. Please check your inbox.')
    except Exception as e:
        messages.warning(request, 'Email delivery delayed. Your OTP code is displayed below.')
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('Failed to send resend OTP email: %s', e)
    
    # Store OTP in session for DEBUG mode only
    if settings.DEBUG:
        request.session[f'debug_otp_{user.pk}'] = plain_otp
        request.session.set_expiry(900)  # 15 minutes
    
    return redirect('accounts:verify_email', user_id=user.pk)


@login_required
def regenerate_recovery_code_confirm(request):
    """Show confirmation page before regenerating recovery code."""
    return render(request, 'accounts/regenerate_recovery_code_confirm.html')


@login_required
def regenerate_recovery_code(request):
    """Allow logged-in users to regenerate their recovery code."""
    if request.method != 'POST':
        return redirect('accounts:regenerate_recovery_code_confirm')
    
    # Verify user's password for security
    password = request.POST.get('password', '')
    
    if not request.user.check_password(password):
        messages.error(request, 'Incorrect password. Please try again.')
        return redirect('accounts:regenerate_recovery_code_confirm')
    
    # Generate new recovery code
    user = request.user
    new_code = user.generate_recovery_code()
    user.set_recovery_code(new_code)
    user.save()
    
    # Log this action for security
    from .models import LoginHistory
    LoginHistory.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        is_successful=True,
        is_suspicious=False,
        failure_reason='Recovery code regenerated'
    )
    
    # Show success page with new code
    messages.success(request, 'Recovery code regenerated successfully!')
    return render(request, 'accounts/recovery_code_regenerated.html', {
        'recovery_code': new_code,
        'username': user.username,
    })


def download_credentials_pdf(request, user_id):
    """Generate PDF with complete user credentials for download."""
    from django.http import FileResponse, HttpResponseForbidden
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from io import BytesIO
    import qrcode
    from PIL import Image as PILImage
    from reportlab.lib.utils import ImageReader
    
    # Retrieve credentials from session
    session_key = f'credentials_{user_id}'
    credentials = request.session.get(session_key)
    
    if not credentials:
        return HttpResponseForbidden("Credentials not available. Please register again.")
    
    # Extract data
    first_name = credentials['first_name']
    last_name = credentials['last_name']
    username = credentials['username']
    password = credentials['password']
    recovery_codes = credentials['recovery_codes']
    security_qa_pairs = credentials['security_qa_pairs']  # List of (question, answer) tuples
    email = credentials['email']
    
    # Create PDF in memory
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header with logo text
    p.setFont("Helvetica-Bold", 24)
    p.setFillColorRGB(0.1, 0.5, 0.2)  # Green
    p.drawCentredString(width/2, height - 50, "TAMIPEE INTEGRATED FARMS")
    
    p.setFont("Helvetica", 14)
    p.setFillColorRGB(0, 0, 0)
    p.drawCentredString(width/2, height - 72, "Account Credentials - Save Securely")
    
    # Warning banner
    p.setFillColorRGB(0.8, 0.1, 0.1)  # Red
    p.rect(50, height - 115, width - 100, 30, fill=1)
    p.setFillColorRGB(1, 1, 1)  # White text
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width/2, height - 103, "⚠ CONFIDENTIAL - KEEP SECURE - NEVER SHARE ⚠")
    
    # Generated date
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 9)
    p.drawString(50, height - 135, f"Generated: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}")
    
    y_pos = height - 165
    
    # Personal Information
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y_pos, "PERSONAL INFORMATION")
    p.setFont("Helvetica", 10)
    y_pos -= 18
    p.drawString(60, y_pos, f"First Name: {first_name}")
    y_pos -= 15
    p.drawString(60, y_pos, f"Last Name: {last_name}")
    y_pos -= 15
    p.drawString(60, y_pos, f"Email: {email}")
    y_pos -= 25
    
    # Login Credentials
    p.setFont("Helvetica-Bold", 11)
    p.setFillColorRGB(0, 0, 0.7)
    p.drawString(50, y_pos, "LOGIN CREDENTIALS")
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 10)
    y_pos -= 18
    p.drawString(60, y_pos, f"Username: ")
    p.setFont("Courier-Bold", 11)
    p.setFillColorRGB(0, 0, 0.8)
    p.drawString(125, y_pos, username)
    p.setFillColorRGB(0, 0, 0)
    y_pos -= 15
    p.setFont("Helvetica", 10)
    p.drawString(60, y_pos, f"Password: ")
    p.setFont("Courier-Bold", 11)
    p.setFillColorRGB(0, 0, 0.8)
    p.drawString(125, y_pos, password)
    p.setFillColorRGB(0, 0, 0)
    y_pos -= 25
    
    # 7 Recovery Codes
    p.setFont("Helvetica-Bold", 11)
    p.setFillColorRGB(0.8, 0.1, 0.1)
    p.drawString(50, y_pos, "7 RECOVERY CODES (Each can only be used ONCE!)")
    p.setFillColorRGB(0, 0, 0)
    y_pos -= 5
    p.setFillColorRGB(0.95, 0.95, 0.95)
    p.rect(50, y_pos - 95, width - 100, 100, fill=1, stroke=1)
    y_pos -= 18
    
    p.setFillColorRGB(0.8, 0.1, 0.1)
    p.setFont("Courier-Bold", 10)
    for i, code in enumerate(recovery_codes):
        col = i % 2
        row = i // 2
        x = 60 + (col * 250)
        y = y_pos - (row * 13)
        p.drawString(x, y, f"{i+1}. {code}")
    
    y_pos -= 110
    p.setFillColorRGB(0, 0, 0)
    
    # Security Questions with Answers
    p.setFont("Helvetica-Bold", 11)
    p.setFillColorRGB(0.8, 0.6, 0)
    p.drawString(50, y_pos, "YOUR SECURITY QUESTIONS & ANSWERS")
    p.setFillColorRGB(0, 0, 0)
    y_pos -= 5
    p.setFillColorRGB(1.0, 0.95, 0.85)
    p.rect(50, y_pos - 80, width - 100, 85, fill=1, stroke=1)
    y_pos -= 18
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 9)
    for i, (question, answer) in enumerate(security_qa_pairs):
        p.drawString(60, y_pos, f"{i+1}. {question}")
        y_pos -= 12
        p.setFont("Helvetica", 9)
        p.setFillColorRGB(0.2, 0.5, 0.2)
        p.drawString(70, y_pos, f"Answer: {answer}")
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica-Bold", 9)
        y_pos -= 15
    
    y_pos -= 15
    
    # Password Reset Requirements
    p.setFillColorRGB(0.9, 0.95, 1.0)
    box_height = 95
    p.rect(50, y_pos - box_height, width - 100, box_height, fill=1, stroke=1)
    
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, y_pos - 15, "PASSWORD RESET REQUIREMENTS:")
    p.setFont("Helvetica", 9)
    y_pos -= 28
    requirements = [
        "If you forget your password, you will need:",
        "  1. Your first name and last name",
        "  2. ONE of your 7 recovery codes (unused)",
        "  3. Correct answers to 2 out of 3 security questions",
    ]
    for req in requirements:
        p.drawString(65, y_pos, req)
        y_pos -= 12
    
    y_pos -= 110
    
    # Important Notes
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y_pos, "IMPORTANT SECURITY NOTES:")
    p.setFont("Helvetica", 8)
    y_pos -= 13
    notes = [
        "✓ Each recovery code can only be used ONCE - that's why we give you 7 codes",
        "✓ Keep this document in a secure location (safe, password manager, encrypted storage)",
        "✓ Never share your password or recovery codes with anyone",
        "✓ Tamipee staff will NEVER ask for your password or recovery codes",
        "✓ You can regenerate new recovery codes after logging in (Profile → Regenerate Codes)",
        "✓ Make sure to remember your security question answers",
    ]
    for note in notes:
        p.drawString(55, y_pos, note)
        y_pos -= 11
    
    # Footer
    p.setFont("Helvetica", 7)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.drawCentredString(width/2, 25, f"© {timezone.now().year} Tamipee Integrated Farms - All Rights Reserved")
    p.drawCentredString(width/2, 15, "This document contains sensitive information. Store securely and destroy when no longer needed.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'tamipee_credentials_{username}.pdf')


def download_credentials_image(request, user_id):
    """Generate PNG image with complete user credentials for download."""
    from django.http import HttpResponse, HttpResponseForbidden
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    
    # Retrieve credentials from session
    session_key = f'credentials_{user_id}'
    credentials = request.session.get(session_key)
    
    if not credentials:
        return HttpResponseForbidden("Credentials not available. Please register again.")
    
    # Extract data
    first_name = credentials['first_name']
    last_name = credentials['last_name']
    username = credentials['username']
    password = credentials['password']
    recovery_codes = credentials['recovery_codes']
    security_qa_pairs = credentials['security_qa_pairs']  # List of (question, answer) tuples
    email = credentials['email']
    
    # Create image (optimized for phone screens - tall format)
    img_width = 1080
    img_height = 2600  # Increased height for answers
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts, fallback to default if not available
    try:
        font_title = ImageFont.truetype("arial.ttf", 50)
        font_header = ImageFont.truetype("arialbd.ttf", 32)
        font_medium = ImageFont.truetype("arialbd.ttf", 28)
        font_normal = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 20)
        font_code = ImageFont.truetype("courier.ttf", 26)
    except:
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_code = ImageFont.load_default()
    
    # Draw border
    draw.rectangle([15, 15, img_width-15, img_height-15], outline='#2E7D32', width=6)
    
    # Header background
    draw.rectangle([30, 30, img_width-30, 150], fill='#2E7D32')
    draw.text((img_width//2, 70), "TAMIPEE INTEGRATED FARMS", fill='white', font=font_title, anchor='mm')
    draw.text((img_width//2, 120), "Account Credentials", fill='white', font=font_medium, anchor='mm')
    
    # Warning banner
    draw.rectangle([50, 170, img_width-50, 230], fill='#DC3545')
    draw.text((img_width//2, 200), "⚠ CONFIDENTIAL - KEEP SECURE ⚠", fill='white', font=font_medium, anchor='mm')
    
    y = 270
    
    # Personal Info
    draw.text((80, y), "PERSONAL INFORMATION", fill='#2E7D32', font=font_header, anchor='lm')
    y += 40
    draw.text((100, y), f"First Name: {first_name}", fill='black', font=font_normal, anchor='lm')
    y += 32
    draw.text((100, y), f"Last Name: {last_name}", fill='black', font=font_normal, anchor='lm')
    y += 50
    
    # Login Credentials
    draw.text((80, y), "LOGIN CREDENTIALS", fill='#1976D2', font=font_header, anchor='lm')
    y += 40
    draw.text((100, y), "Username:", fill='black', font=font_normal, anchor='lm')
    y += 30
    draw.rectangle([90, y, img_width-90, y+45], outline='#1976D2', width=3)
    draw.text((img_width//2, y+22), username, fill='#1976D2', font=font_code, anchor='mm')
    y += 60
    draw.text((100, y), "Password:", fill='black', font=font_normal, anchor='lm')
    y += 30
    draw.rectangle([90, y, img_width-90, y+45], outline='#1976D2', width=3)
    draw.text((img_width//2, y+22), password, fill='#1976D2', font=font_code, anchor='mm')
    y += 70
    
    # 7 Recovery Codes
    draw.text((80, y), "7 RECOVERY CODES", fill='#DC3545', font=font_header, anchor='lm')
    y += 35
    draw.text((100, y), "(Each can only be used ONCE!)", fill='#DC3545', font=font_small, anchor='lm')
    y += 40
    draw.rectangle([60, y, img_width-60, y+280], fill='#FFF8F8', outline='#DC3545', width=3)
    y += 20
    for i, code in enumerate(recovery_codes):
        draw.text((100, y), f"{i+1}. {code}", fill='#DC3545', font=font_code, anchor='lm')
        y += 38
    y += 30
    
    # Security Questions & Answers
    draw.text((80, y), "SECURITY QUESTIONS & ANSWERS", fill='#F57C00', font=font_header, anchor='lm')
    y += 40
    draw.rectangle([60, y, img_width-60, y+350], fill='#FFF9E6', outline='#F57C00', width=3)
    y += 20
    for i, (question, answer) in enumerate(security_qa_pairs):
        # Question
        draw.text((100, y), f"{i+1}. {question[:55]}", fill='#F57C00', font=font_medium, anchor='lm')
        if len(question) > 55:
            y += 28
            draw.text((115, y), question[55:], fill='#F57C00', font=font_medium, anchor='lm')
        y += 32
        # Answer
        draw.text((120, y), f"Answer: {answer}", fill='#2E7D32', font=font_normal, anchor='lm')
        y += 40
    y += 30
    
    # Password Reset Requirements
    draw.rectangle([60, y, img_width-60, y+180], fill='#E3F2FD', outline='#1976D2', width=3)
    y += 20
    draw.text((100, y), "PASSWORD RESET NEEDS:", fill='#1976D2', font=font_medium, anchor='lm')
    y += 35
    requirements = [
        "1. First & last name",
        "2. ONE recovery code (unused)",
        "3. 2 out of 3 security answers",
    ]
    for req in requirements:
        draw.text((120, y), req, fill='black', font=font_small, anchor='lm')
        y += 32
    y += 40
    
    # Important Notes
    draw.text((80, y), "IMPORTANT NOTES:", fill='#2E7D32', font=font_medium, anchor='lm')
    y += 35
    notes = [
        "✓ Keep this image secure",
        "✓ Never share recovery codes",
        "✓ Staff will NEVER ask for them",
        "✓ Can regenerate after login",
    ]
    for note in notes:
        draw.text((100, y), note, fill='black', font=font_small, anchor='lm')
        y += 30
    
    # Footer
    y = img_height - 80
    footer_text = f"Generated: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}"
    draw.text((img_width//2, y), footer_text, fill='#666', font=font_small, anchor='mm')
    y += 30
    draw.text((img_width//2, y), f"© {timezone.now().year} Tamipee Integrated Farms", fill='#666', font=font_small, anchor='mm')
    
    # Save to response
    response = HttpResponse(content_type='image/png')
    img.save(response, 'PNG', quality=95)
    response['Content-Disposition'] = f'attachment; filename="tamipee_credentials_{username}.png"'
    return response

