from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import CustomUser, SecurityQuestion, UserSecurityAnswer, RecoveryCode
import secrets


def _normalized_email(value):
    return (value or '').strip().lower()


# Blacklist of common/weak answers
WEAK_ANSWERS_BLACKLIST = {
    'yes', 'no', 'a', 'b', 'c', 'd', 'none', 'null', 'na', 'n/a',
    'pizza', 'chicken', 'rice', 'water', 'red', 'blue', 'black', 'white',
    'fluffy', 'max', 'buddy', 'spot', 'lucky', 'duke', 'baby',
    'john', 'jane', 'mary', 'mike', 'david', 'sarah',
    '123', '1234', 'test', 'password', 'admin',
}


def validate_security_answer(answer, question_number):
    """Validate security answer strength."""
    answer = answer.strip()
    answer_lower = answer.lower()
    
    # Check minimum length
    if len(answer) < 4:
        raise ValidationError(
            f'Answer {question_number} is too short. Must be at least 4 characters.'
        )
    
    # Check maximum length
    if len(answer) > 200:
        raise ValidationError(
            f'Answer {question_number} is too long. Maximum 200 characters.'
        )
    
    # Check if it's only numbers
    if answer.isdigit() and len(answer) < 6:
        raise ValidationError(
            f'Answer {question_number} cannot be only numbers. Add some letters.'
        )
    
    # Check if it's in the weak answers blacklist
    if answer_lower in WEAK_ANSWERS_BLACKLIST:
        raise ValidationError(
            f'Answer {question_number} is too common. Please choose a more unique answer.'
        )
    
    # Check if it's just repeated characters (e.g., "aaaa")
    if len(set(answer_lower)) == 1:
        raise ValidationError(
            f'Answer {question_number} cannot be the same character repeated.'
        )
    
    # Check if it's a keyboard pattern (qwerty, asdf, etc.)
    keyboard_patterns = ['qwerty', 'asdf', 'zxcv', '1234', 'abcd']
    if any(pattern in answer_lower for pattern in keyboard_patterns):
        raise ValidationError(
            f'Answer {question_number} contains a keyboard pattern. Please choose something more secure.'
        )
    
    return answer


class CustomerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, help_text="Your first name")
    last_name = forms.CharField(max_length=150, required=True, help_text="Your last name")
    email = forms.EmailField(required=True, help_text="Required for account verification and password recovery")
    
    # Security questions for password recovery
    security_question_1 = forms.ModelChoiceField(
        queryset=SecurityQuestion.objects.none(),
        required=True,
        label="Security Question 1",
        help_text="Choose a question you'll remember the answer to"
    )
    security_answer_1 = forms.CharField(
        max_length=200,
        required=True,
        label="Answer 1",
        help_text="Answer will be case-insensitive",
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )
    
    security_question_2 = forms.ModelChoiceField(
        queryset=SecurityQuestion.objects.none(),
        required=True,
        label="Security Question 2",
        help_text="Choose a different question"
    )
    security_answer_2 = forms.CharField(
        max_length=200,
        required=True,
        label="Answer 2",
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )
    
    security_question_3 = forms.ModelChoiceField(
        queryset=SecurityQuestion.objects.none(),
        required=True,
        label="Security Question 3",
        help_text="Choose a third different question"
    )
    security_answer_3 = forms.CharField(
        max_length=200,
        required=True,
        label="Answer 3",
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].help_text = 'Your first name.'
        self.fields['last_name'].help_text = 'Your last name.'
        self.fields['email'].help_text = 'Required for account verification.'
        self.fields['password1'].help_text = 'Use at least 8 characters.'
        
        # Load active security questions for all three dropdowns
        active_questions = SecurityQuestion.objects.filter(is_active=True)
        self.fields['security_question_1'].queryset = active_questions
        self.fields['security_question_2'].queryset = active_questions
        self.fields['security_question_3'].queryset = active_questions

    def clean(self):
        """Validate that all three security questions are different and answers are strong."""
        cleaned_data = super().clean()
        q1 = cleaned_data.get('security_question_1')
        q2 = cleaned_data.get('security_question_2')
        q3 = cleaned_data.get('security_question_3')
        
        # Check questions are different
        if q1 and q2 and q1 == q2:
            raise ValidationError('Please choose three different security questions.')
        if q1 and q3 and q1 == q3:
            raise ValidationError('Please choose three different security questions.')
        if q2 and q3 and q2 == q3:
            raise ValidationError('Please choose three different security questions.')
        
        # Validate answer strength
        for i in range(1, 4):
            answer = cleaned_data.get(f'security_answer_{i}', '').strip()
            if answer:
                try:
                    validate_security_answer(answer, i)
                except ValidationError as e:
                    raise ValidationError(e.message)
        
        # Check if any two answers are the same
        answers = [
            cleaned_data.get('security_answer_1', '').lower().strip(),
            cleaned_data.get('security_answer_2', '').lower().strip(),
            cleaned_data.get('security_answer_3', '').lower().strip(),
        ]
        if len(answers) != len(set(answers)):
            raise ValidationError('All three security answers must be different.')
        
        return cleaned_data

    def _generate_username(self):
        """Generate unique username from first_name + last_name + random identifier"""
        first = slugify(self.cleaned_data.get('first_name', '')).replace('-', '_') or 'user'
        last = slugify(self.cleaned_data.get('last_name', '')).replace('-', '_') or ''
        
        # Create base username from first and last name
        if last:
            base_username = f"{first}_{last}"
        else:
            base_username = first
        
        # Add random 6-character identifier
        random_suffix = secrets.token_hex(3)  # 6 hex characters
        candidate = f"{base_username}_{random_suffix}"[:150]
        
        # Ensure uniqueness (very unlikely to collide with 6 random hex chars, but check anyway)
        suffix = 1
        while CustomUser.objects.filter(username__iexact=candidate).exists():
            suffix_text = f'_{suffix}'
            candidate = f"{base_username}_{random_suffix}{suffix_text}"[:150]
            suffix += 1

        return candidate

    def clean_email(self):
        """Ensure email is unique if provided"""
        email = _normalized_email(self.cleaned_data.get('email'))
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self._generate_username()
        user.role = 'customer'
        user.is_active = False  # Inactive until email is verified
        
        # Capture password before it's hashed
        plain_password = self.cleaned_data.get('password1')
        
        if commit:
            user.save()
            
            # Generate 7 recovery codes
            recovery_codes = RecoveryCode.generate_codes_for_user(user, count=7)
            
            # Save security questions and answers
            security_qa_pairs = []  # List of (question, answer) tuples
            for i in range(1, 4):
                question = self.cleaned_data.get(f'security_question_{i}')
                answer = self.cleaned_data.get(f'security_answer_{i}')
                
                if question and answer:
                    security_answer = UserSecurityAnswer(user=user, question=question)
                    security_answer.set_answer(answer)
                    security_answer.save()
                    security_qa_pairs.append((question.question_text, answer))  # Store both Q&A
            
            # Store data in user object for display (not saved to DB)
            user.plain_recovery_codes = recovery_codes  # List of 7 codes
            user.plain_password = plain_password
            user.security_qa_pairs = security_qa_pairs  # List of (question, answer) tuples
        
        return user


class StaffRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def clean_email(self):
        email = _normalized_email(self.cleaned_data.get('email'))
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'staff'
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username or Email', 
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your username or email',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'form-control'
        })
    )
    
    def clean_username(self):
        """Allow login with either username or email."""
        username_or_email = self.cleaned_data.get('username')
        
        # Check if it looks like an email
        if '@' in username_or_email:
            # Try to find user by email
            User = get_user_model()
            try:
                user = User.objects.get(email__iexact=username_or_email)
                # Return the actual username for authentication
                return user.username
            except User.DoesNotExist:
                # Let the authentication fail naturally
                pass
        
        # Return as-is if it's a username
        return username_or_email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'address', 'profile_picture']

    def clean_email(self):
        email = _normalized_email(self.cleaned_data.get('email'))
        if not email:
            return email

        queryset = CustomUser.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError('That email is already in use by another account.')
        return email


class AdminCustomerRegistrationForm(UserCreationForm):
    """
    Admin-only customer creation:
    - email is optional (customers without email)
    - no OTP/email verification flow
    - creates an active customer immediately
    """
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(max_length=500, required=False)

    # Email is optional, but if provided it must be unique.
    email = forms.EmailField(required=False)

    # Security questions for password recovery
    security_question_1 = forms.ModelChoiceField(
        queryset=SecurityQuestion.objects.none(),
        required=True,
        label="Security Question 1",
    )
    security_answer_1 = forms.CharField(
        max_length=200,
        required=True,
        label="Answer 1",
        help_text="Answer will be case-insensitive",
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )

    security_question_2 = forms.ModelChoiceField(
        queryset=SecurityQuestion.objects.none(),
        required=True,
        label="Security Question 2",
    )
    security_answer_2 = forms.CharField(
        max_length=200,
        required=True,
        label="Answer 2",
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )

    security_question_3 = forms.ModelChoiceField(
        queryset=SecurityQuestion.objects.none(),
        required=True,
        label="Security Question 3",
    )
    security_answer_3 = forms.CharField(
        max_length=200,
        required=True,
        label="Answer 3",
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        active_questions = SecurityQuestion.objects.filter(is_active=True)
        self.fields['security_question_1'].queryset = active_questions
        self.fields['security_question_2'].queryset = active_questions
        self.fields['security_question_3'].queryset = active_questions

        # We generate username automatically; disable username field if present.
        if 'username' in self.fields:
            self.fields['username'].disabled = True
            self.fields['username'].required = False

    def clean_email(self):
        email = _normalized_email(self.cleaned_data.get('email'))
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()

        q1 = cleaned_data.get('security_question_1')
        q2 = cleaned_data.get('security_question_2')
        q3 = cleaned_data.get('security_question_3')

        if q1 and q2 and q1 == q2:
            raise ValidationError('Please choose three different security questions.')
        if q1 and q3 and q1 == q3:
            raise ValidationError('Please choose three different security questions.')
        if q2 and q3 and q2 == q3:
            raise ValidationError('Please choose three different security questions.')

        answers = []
        for i in range(1, 4):
            answer = cleaned_data.get(f'security_answer_{i}', '').strip()
            if answer:
                validate_security_answer(answer, i)
            answers.append((answer or '').lower())

        if len(set(answers)) != 3:
            raise ValidationError('All three security answers must be different.')

        return cleaned_data

    def _generate_username(self):
        first = slugify(self.cleaned_data.get('first_name', '')).replace('-', '_') or 'user'
        last = slugify(self.cleaned_data.get('last_name', '')).replace('-', '_') or ''
        base_username = f"{first}_{last}" if last else first

        random_suffix = secrets.token_hex(3)
        candidate = f"{base_username}_{random_suffix}"[:150]

        suffix = 1
        while CustomUser.objects.filter(username__iexact=candidate).exists():
            candidate = f"{base_username}_{random_suffix}_{suffix}"[:150]
            suffix += 1
        return candidate

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self._generate_username()
        user.role = 'customer'
        user.is_active = True  # Admin-created customer works immediately (no email)

        plain_password = self.cleaned_data.get('password1')

        if commit:
            user.phone = (self.cleaned_data.get('phone') or '').strip()
            user.address = (self.cleaned_data.get('address') or '').strip()

            email = self.cleaned_data.get('email')
            if email:
                user.email = _normalized_email(email)
                user.email_verified = False
            else:
                user.email = ''
                user.email_verified = False

            user.save()

            RecoveryCode.generate_codes_for_user(user, count=7)

            for i in range(1, 4):
                question = self.cleaned_data.get(f'security_question_{i}')
                answer = self.cleaned_data.get(f'security_answer_{i}')
                if question and answer:
                    security_answer = UserSecurityAnswer(user=user, question=question)
                    security_answer.set_answer(answer)
                    security_answer.save()

            # Attach for template display if needed (not saved to DB)
            user.plain_recovery_codes = RecoveryCode.generate_codes_for_user(user, count=0) if False else []
            user.plain_password = plain_password

        return user
