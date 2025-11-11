from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Format: yourname@example.com")
    role = forms.ChoiceField(
        choices=[('planner', 'Planner'), ('guest', 'Guest')],
        widget=forms.RadioSelect,
        help_text="Select your role (Hosts are added by admins)"
    )
    full_name = forms.CharField(max_length=255, required=True)
    mobile_number = forms.CharField(max_length=10, required=True, help_text="10 digits starting with 6,7,8,9")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True)
    profile_picture = forms.ImageField(required=False, help_text="Optional profile picture")

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role', 'full_name', 'mobile_number', 'address', 'profile_picture', 'password1', 'password2')

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number')
        if mobile:
            if not mobile.isdigit() or len(mobile) != 10 or mobile[0] not in '6789':
                raise ValidationError('Mobile number must be exactly 10 digits starting with 6, 7, 8, or 9.')
        return mobile

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.full_name = self.cleaned_data['full_name']
        user.mobile_number = self.cleaned_data['mobile_number']
        user.address = self.cleaned_data['address']
        if self.cleaned_data.get('profile_picture'):
            user.profile_picture = self.cleaned_data['profile_picture']
        user.is_approved = False
        user.is_active = False  # Pending approval
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    pass  # Uses default, but custom validation in view

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'mobile_number', 'address', 'profile_picture']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'mobile_number': '10 digits starting with 6,7,8,9',
        }

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number')
        if mobile:
            if not mobile.isdigit() or len(mobile) != 10 or mobile[0] not in '6789':
                raise forms.ValidationError('Mobile number must be exactly 10 digits starting with 6, 7, 8, or 9.')
        return mobile