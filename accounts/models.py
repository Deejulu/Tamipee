from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from datetime import timedelta
import random
import string


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('customer', 'Customer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_verified = models.BooleanField(default=False)
    recovery_code_hash = models.CharField(max_length=128, blank=True)  # Hashed recovery code for account recovery
    
    # Progressive login lockout fields
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('email'),
                condition=~models.Q(email=''),
                name='unique_lower_email',
            )
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()

        # Keep role in sync with Django's superuser/staff flags so
        # accounts created via createsuperuser are never mis-tagged.
        if self.is_superuser and self.role != 'admin':
            self.role = 'admin'
        elif self.is_staff and not self.is_superuser and self.role == 'customer':
            self.role = 'staff'
        super().save(*args, **kwargs)

    def is_admin_user(self):
        return self.role == 'admin'

    def is_staff_user(self):
        return self.role == 'staff'

    def is_customer(self):
        return self.role == 'customer'

    def __str__(self):
        return f"{self.username} ({self.role})"

    @staticmethod
    def generate_recovery_code():
        """Generate a random recovery code in format: XXXX-XXXX-XXXX"""
        import secrets
        part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part3 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{part1}-{part2}-{part3}"

    def set_recovery_code(self, plain_code):
        """Hash and store recovery code."""
        import hashlib
        # Normalize: remove dashes and convert to uppercase
        normalized = plain_code.replace('-', '').replace(' ', '').upper()
        self.recovery_code_hash = hashlib.sha256(normalized.encode()).hexdigest()

    def check_recovery_code(self, plain_code):
        """Verify recovery code against stored hash."""
        import hashlib
        if not self.recovery_code_hash:
            return False
        normalized = plain_code.replace('-', '').replace(' ', '').upper()
        provided_hash = hashlib.sha256(normalized.encode()).hexdigest()
        return self.recovery_code_hash == provided_hash    
    def record_failed_login(self):
        """Record failed login attempt with progressive lockout."""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        # Progressive lockout durations
        if self.failed_login_attempts == 3:
            self.locked_until = timezone.now() + timedelta(minutes=5)
        elif self.failed_login_attempts == 5:
            self.locked_until = timezone.now() + timedelta(minutes=15)
        elif self.failed_login_attempts == 10:
            self.locked_until = timezone.now() + timedelta(hours=1)
        elif self.failed_login_attempts >= 15:
            self.locked_until = timezone.now() + timedelta(days=1)
            self.is_active = False  # Require admin unlock
        
        self.save()
    
    def reset_failed_logins(self):
        """Reset failed login counter after successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_failed_login = None
        self.save()
    
    def is_locked(self):
        """Check if account is currently locked."""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        elif self.locked_until and self.locked_until <= timezone.now():
            # Lock expired, reset counter
            self.locked_until = None
            self.failed_login_attempts = 0
            self.save()
        return False

class EmailVerification(models.Model):
    """Store OTP codes for email verification with security features."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_verifications')
    otp_hash = models.CharField(max_length=128)  # Hashed OTP for security
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    is_used = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)  # Account lockout

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"OTP for {self.user.email} - {'Used' if self.is_used else 'Active'}"

    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP."""
        return ''.join(random.choices(string.digits, k=6))

    def set_otp(self, plain_otp):
        """Hash and store the OTP securely."""
        self.otp_hash = make_password(plain_otp)

    def check_otp(self, plain_otp):
        """Verify the OTP against the stored hash."""
        return check_password(plain_otp, self.otp_hash)

    def is_valid(self):
        """Check if OTP is still valid (not expired, not used, not locked)."""
        now = timezone.now()
        
        # Check if account is locked
        if self.locked_until and now < self.locked_until:
            return False
        
        # Check if OTP has expired
        if now > self.expires_at:
            return False
        
        # Check if OTP has been used
        if self.is_used:
            return False
        
        # Check if too many attempts
        if self.attempts >= 5:
            return False
        
        return True

    def increment_attempts(self):
        """Increment failed attempts and lock account if threshold reached."""
        self.attempts += 1
        
        # Lock account for 15 minutes after 5 failed attempts
        if self.attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=15)
        
        self.save()

    def mark_as_used(self):
        """Mark this OTP as used."""
        self.is_used = True
        self.save()

    @classmethod
    def create_for_user(cls, user):
        """Create a new OTP verification for a user."""
        # Invalidate all previous unused OTPs for this user
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new OTP
        plain_otp = cls.generate_otp()
        
        # Create verification record
        verification = cls.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(minutes=15)  # 15-minute expiration
        )
        verification.set_otp(plain_otp)
        verification.save()
        
        return verification, plain_otp

    @classmethod
    def cleanup_expired(cls):
        """Delete expired OTP records (run periodically)."""
        expired_time = timezone.now() - timedelta(days=7)  # Keep for 7 days then delete
        cls.objects.filter(created_at__lt=expired_time).delete()


class RecoveryCode(models.Model):
    """Store multiple recovery codes for account recovery (each usable once)"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='recovery_codes')
    code_hash = models.CharField(max_length=128)  # Hashed recovery code
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    @staticmethod
    def generate_code():
        """Generate a single 12-character recovery code in format XXXX-XXXX-XXXX"""
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choices(chars, k=12))
        return f"{code[:4]}-{code[4:8]}-{code[8:12]}"
    
    def set_code(self, plain_code):
        """Hash and store the recovery code"""
        # Normalize: uppercase, no dashes, then hash
        normalized = plain_code.upper().replace('-', '')
        self.code_hash = make_password(normalized)
    
    def check_code(self, plain_code):
        """Verify a recovery code matches this record"""
        normalized = plain_code.upper().replace('-', '')
        return check_password(normalized, self.code_hash)
    
    def mark_used(self):
        """Mark this recovery code as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
    
    @classmethod
    def generate_codes_for_user(cls, user, count=7):
        """Generate multiple recovery codes for a user
        
        Returns:
            list: Plain text recovery codes (not hashed)
        """
        plain_codes = []
        
        for _ in range(count):
            # Generate unique code
            while True:
                code = cls.generate_code()
                if code not in plain_codes:
                    break
            
            plain_codes.append(code)
            
            # Create and save hashed version
            recovery_code = cls(user=user)
            recovery_code.set_code(code)
            recovery_code.save()
        
        return plain_codes
    
    @classmethod
    def verify_code_for_user(cls, user, plain_code):
        """Verify a recovery code for a user and mark it as used if valid
        
        Returns:
            bool: True if code is valid and unused, False otherwise
        """
        # Get all unused codes for this user
        unused_codes = cls.objects.filter(user=user, is_used=False)
        
        for recovery_code in unused_codes:
            if recovery_code.check_code(plain_code):
                recovery_code.mark_used()
                return True
        
        return False


class SecurityQuestion(models.Model):
    """Predefined security questions for account recovery."""
    question_text = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'question_text']
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.question_text


class UserSecurityAnswer(models.Model):
    """Store user's answers to security questions (hashed with PBKDF2 + unique salt)."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='security_answers')
    question = models.ForeignKey(SecurityQuestion, on_delete=models.PROTECT)
    answer_hash = models.CharField(max_length=256)  # PBKDF2 hashed answer
    salt = models.CharField(max_length=64)  # Unique salt per answer (prevents rainbow tables)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'question')]
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.question.question_text}"

    def set_answer(self, plain_answer):
        """Hash and store the answer securely with PBKDF2 + unique salt."""
        import hashlib
        import secrets
        
        # Normalize answer (case-insensitive, trimmed)
        normalized_answer = plain_answer.lower().strip()
        
        # Generate unique salt for this answer (32 bytes = 64 hex chars)
        self.salt = secrets.token_hex(32)
        
        # Use PBKDF2 with 100,000 iterations (industry standard)
        self.answer_hash = hashlib.pbkdf2_hmac(
            'sha256',
            normalized_answer.encode(),
            self.salt.encode(),
            100000  # Iterations - makes brute force very slow
        ).hex()

    def check_answer(self, plain_answer):
        """Verify the answer against the stored hash using stored salt."""
        import hashlib
        
        if not self.salt:
            # Legacy answers without salt - fallback to SHA-256 (backward compatibility)
            normalized_answer = plain_answer.lower().strip()
            provided_hash = hashlib.sha256(normalized_answer.encode()).hexdigest()
            return self.answer_hash == provided_hash
        
        # Normalize answer
        normalized_answer = plain_answer.lower().strip()
        
        # Recreate hash with stored salt
        provided_hash = hashlib.pbkdf2_hmac(
            'sha256',
            normalized_answer.encode(),
            self.salt.encode(),
            100000
        ).hex()
        
        return self.answer_hash == provided_hash


class PasswordResetAttempt(models.Model):
    """Track password reset attempts for security and admin approval."""
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('success', 'Successful Reset'),
        ('failed', 'Failed Verification'),
        ('locked', 'Account Locked'),
        ('admin_review', 'Awaiting Admin Approval'),
        ('admin_approved', 'Admin Approved'),
        ('admin_denied', 'Admin Denied'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Security question verification
    questions_answered = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Admin review
    reviewed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_reset_attempts'
    )
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def is_locked(self):
        """Check if this attempt is currently locked."""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False

    def lock_account(self, minutes=30):
        """Lock account for specified minutes."""
        self.locked_until = timezone.now() + timedelta(minutes=minutes)
        self.status = 'locked'
        self.save()

    def mark_success(self):
        """Mark reset as successful."""
        self.status = 'success'
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self):
        """Mark reset as failed."""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.save()

    def require_admin_review(self):
        """Send to admin for manual review."""
        self.status = 'admin_review'
        self.save()

    @classmethod
    def can_attempt_reset(cls, user, ip_address=None):
        """Check if user can attempt password reset (rate limiting)."""
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Check for locked attempts
        locked_attempt = cls.objects.filter(
            user=user,
            status='locked',
            locked_until__gt=now
        ).first()
        
        if locked_attempt:
            return False, f"Account locked until {locked_attempt.locked_until.strftime('%H:%M')}"
        
        # Check recent failed attempts (max 3 per hour)
        recent_failed = cls.objects.filter(
            user=user,
            status__in=['failed', 'locked'],
            created_at__gte=one_hour_ago
        ).count()
        
        if recent_failed >= 3:
            return False, "Too many failed attempts. Please try again later or contact admin."
        
        # Rate limit by IP if provided (max 5 attempts per hour per IP)
        if ip_address:
            ip_attempts = cls.objects.filter(
                ip_address=ip_address,
                created_at__gte=one_hour_ago
            ).count()
            
            if ip_attempts >= 5:
                return False, "Too many attempts from this location. Please try again later."
        
        return True, "OK"

    @classmethod
    def cleanup_old_attempts(cls):
        """Delete old password reset attempts (run periodically)."""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        cls.objects.filter(created_at__lt=thirty_days_ago).delete()


class PasswordHistory(models.Model):
    """Track password history to prevent reuse of recent passwords."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def check_password_reuse(cls, user, new_password, history_count=5):
        """
        Check if new password matches any of the last N passwords.
        Returns (is_reused, message)
        """
        old_passwords = cls.objects.filter(user=user)[:history_count]
        
        for old_password_record in old_passwords:
            if check_password(new_password, old_password_record.password_hash):
                return True, f"Cannot reuse your last {history_count} passwords"
        
        return False, "Password is unique"
    
    @classmethod
    def add_password_to_history(cls, user, password_hash):
        """Add current password to history before changing."""
        cls.objects.create(user=user, password_hash=password_hash)
        
        # Keep only last 10 passwords in history
        old_passwords = list(cls.objects.filter(user=user)[10:])
        if old_passwords:
            cls.objects.filter(id__in=[p.id for p in old_passwords]).delete()


class LoginHistory(models.Model):
    """Track login history for security monitoring and geographic anomaly detection."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Geographic information (can be populated via IP geolocation API)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Login details
    login_time = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)
    is_suspicious = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_suspicious']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_successful else "✗"
        return f"{status} {self.user.username} - {self.ip_address} - {self.login_time.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def record_login(cls, user, request, is_successful=True, failure_reason=''):
        """Record a login attempt with IP and user agent."""
        from accounts.views import get_client_ip
        
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return cls.objects.create(
            user=user,
            ip_address=ip,
            user_agent=user_agent,
            is_successful=is_successful,
            failure_reason=failure_reason
        )
    
    @classmethod
    def check_suspicious_login(cls, user, current_ip):
        """
        Check if login from current IP is suspicious based on history.
        Returns (is_suspicious, reason)
        """
        # Get last successful login
        last_login = cls.objects.filter(
            user=user,
            is_successful=True
        ).exclude(ip_address=current_ip).first()
        
        if not last_login:
            return False, ""  # First login or same IP
        
        # Check if IP changed (simple geographic anomaly detection)
        # In production, you'd use IP geolocation API to check distance
        if last_login.ip_address != current_ip:
            # Check if new IP has been used before
            known_ip = cls.objects.filter(
                user=user,
                ip_address=current_ip,
                is_successful=True
            ).exists()
            
            if not known_ip:
                return True, f"New login location detected. Last login from {last_login.ip_address}"
        
        return False, ""
    
    @classmethod
    def cleanup_old_history(cls, days=90):
        """Delete login history older than specified days."""
        cutoff = timezone.now() - timedelta(days=days)
        cls.objects.filter(login_time__lt=cutoff).delete()
