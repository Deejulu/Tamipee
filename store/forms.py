from django import forms
from django.core.validators import RegexValidator
from .models import Order, Newsletter, Testimonial, FAQ, Banner, Promotion, Announcement, SiteContent, Product


class CheckoutForm(forms.ModelForm):
    phone = forms.CharField(
        validators=[RegexValidator(r'^\+?[0-9\-\s]{7,20}$', 'Enter a valid phone number.')]
    )

    class Meta:
        model = Order
        fields = ['delivery_address', 'phone', 'notes']
        widgets = {
            'delivery_address': forms.Textarea(attrs={'rows': 3, 'maxlength': 500}),
            'notes': forms.Textarea(attrs={'rows': 2, 'maxlength': 500}),
        }

    def clean_delivery_address(self):
        value = self.cleaned_data['delivery_address'].strip()
        if len(value) < 10:
            raise forms.ValidationError('Enter a more complete delivery address.')
        return value

    def clean_notes(self):
        value = self.cleaned_data.get('notes', '').strip()
        if len(value) > 500:
            raise forms.ValidationError('Notes must be 500 characters or fewer.')
        return value


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['email']

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=254)
    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[RegexValidator(r'^\+?[0-9\-\s]{7,20}$', 'Enter a valid phone number.')],
    )
    message = forms.CharField(min_length=10, max_length=2000, widget=forms.Textarea)

    def clean_name(self):
        return self.cleaned_data['name'].strip()

    def clean_message(self):
        return self.cleaned_data['message'].strip()


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['livestock_species', 'name', 'description', 'price', 'unit',
                  'stock_quantity', 'image', 'is_available', 'is_featured']


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['title', 'subtitle', 'image', 'link_url', 'is_active', 'order']


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['customer_name', 'message', 'rating', 'image', 'is_active']


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'order', 'is_active']


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['title', 'description', 'discount_percent', 'product', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('Promotion end date cannot be earlier than start date.')
        return cleaned_data


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'body', 'is_active']


class SiteContentForm(forms.ModelForm):
    class Meta:
        model = SiteContent
        fields = ['key', 'value']
