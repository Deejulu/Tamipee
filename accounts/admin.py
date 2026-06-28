from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, SecurityQuestion, UserSecurityAnswer, PasswordResetAttempt, PasswordHistory, LoginHistory


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'created_at', 'delete_button']
    list_filter = ['role', 'is_active']
    actions = ['delete_selected_users', 'deactivate_users', 'activate_users']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Farm Role & Contact', {'fields': ('role', 'phone', 'address', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Farm Role & Contact', {'fields': ('role', 'phone', 'address')}),
    )
    
    def delete_button(self, obj):
        """Display a delete button/link for each user in the list view."""
        return format_html(
            '<a class="button" href="/admin/accounts/customuser/{}/delete/" '
            'style="background-color: #ba2121; color: white; padding: 5px 10px; '
            'text-decoration: none; border-radius: 3px;">Delete</a>',
            obj.pk
        )
    delete_button.short_description = 'Actions'
    delete_button.allow_tags = True
    
    def delete_selected_users(self, request, queryset):
        """Custom delete action with detailed feedback."""
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request, 
            f'Successfully deleted {count} user(s) and all associated data (security answers, login history, etc.).'
        )
    delete_selected_users.short_description = '🗑️ Delete selected users (permanent)'
    
    def deactivate_users(self, request, queryset):
        """Deactivate users instead of deleting them."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {updated} user(s). They cannot log in but data is preserved.')
    deactivate_users.short_description = '🔒 Deactivate selected users (preserve data)'
    
    def activate_users(self, request, queryset):
        """Reactivate previously deactivated users."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Activated {updated} user(s). They can now log in.')
    activate_users.short_description = '✅ Activate selected users'


@admin.register(SecurityQuestion)
class SecurityQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'is_active', 'order', 'created_at']
    list_filter = ['is_active']
    search_fields = ['question_text']
    ordering = ['order', 'question_text']


@admin.register(UserSecurityAnswer)
class UserSecurityAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'question__question_text']
    readonly_fields = ['answer_hash', 'created_at', 'updated_at']
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing answers for security
        return False


@admin.register(PasswordResetAttempt)
class PasswordResetAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'correct_answers', 'questions_answered', 'created_at', 'ip_address']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'ip_address']
    readonly_fields = ['user', 'ip_address', 'user_agent', 'questions_answered', 'correct_answers', 
                       'created_at', 'completed_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'status')
        }),
        ('Attempt Details', {
            'fields': ('questions_answered', 'correct_answers', 'ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at', 'locked_until')
        }),
        ('Admin Review', {
            'fields': ('reviewed_by', 'admin_notes'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reset', 'deny_reset']
    
    def approve_reset(self, request, queryset):
        """Approve password reset requests."""
        updated = queryset.filter(status='admin_review').update(
            status='admin_approved',
            reviewed_by=request.user
        )
        self.message_user(request, f'{updated} reset request(s) approved.')
    approve_reset.short_description = 'Approve selected reset requests'
    
    def deny_reset(self, request, queryset):
        """Deny password reset requests."""
        updated = queryset.filter(status='admin_review').update(
            status='admin_denied',
            reviewed_by=request.user
        )
        self.message_user(request, f'{updated} reset request(s) denied.')
    deny_reset.short_description = 'Deny selected reset requests'


@admin.register(PasswordHistory)
class PasswordHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['user', 'password_hash', 'created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        # Prevent manual creation - passwords added automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Read-only for security
        return False


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'login_time', 'is_successful', 'is_suspicious', 'city', 'country']
    list_filter = ['is_successful', 'is_suspicious', 'login_time']
    search_fields = ['user__username', 'user__email', 'ip_address', 'city', 'country']
    readonly_fields = ['user', 'ip_address', 'user_agent', 'city', 'country', 
                      'latitude', 'longitude', 'login_time', 'is_successful', 
                      'is_suspicious', 'failure_reason']
    date_hierarchy = 'login_time'
    
    fieldsets = (
        ('User & Result', {
            'fields': ('user', 'is_successful', 'is_suspicious', 'failure_reason')
        }),
        ('Location Information', {
            'fields': ('ip_address', 'city', 'country', 'latitude', 'longitude')
        }),
        ('Technical Details', {
            'fields': ('user_agent', 'login_time'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_suspicious', 'mark_as_safe']
    
    def mark_as_suspicious(self, request, queryset):
        updated = queryset.update(is_suspicious=True)
        self.message_user(request, f'{updated} login(s) marked as suspicious.')
    mark_as_suspicious.short_description = 'Mark selected logins as suspicious'
    
    def mark_as_safe(self, request, queryset):
        updated = queryset.update(is_suspicious=False)
        self.message_user(request, f'{updated} login(s) marked as safe.')
    mark_as_safe.short_description = 'Mark selected logins as safe'
    
    def has_add_permission(self, request):
        # Prevent manual creation
        return False
    
    def has_change_permission(self, request, obj=None):
        # Read-only except for is_suspicious flag
        return True if request.user.is_superuser else False

