from django.shortcuts import redirect
from django.contrib.auth import login
from django import forms
from .models import CustomUser
from django.contrib.auth import logout
from .forms import *
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordResetView,
    PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
import secrets
import string
from .forms import SignUpForm, ProfileUpdateForm
from utils.pagination import paginate_queryset  # your global paginator


class HomeView(TemplateView):
    template_name = 'accounts/home.html'

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registration successful! Your account is awaiting admin approval.')
        return response

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        user = form.get_user()

        # Account not active
        if not user.is_active:
            messages.error(self.request, 'Your account is not active. Contact admin if needed.')
            return self.form_invalid(form)

        # Account pending approval
        if user.role in ['planner', 'guest'] and not user.is_approved:
            messages.error(self.request, 'Your account is pending admin approval. Please wait.')
            return self.form_invalid(form)

        # Log the user in
        response = super().form_valid(form)

        # Role-based redirect
        return self.redirect_based_on_role(user)

    def redirect_based_on_role(self, user):
        """Redirect user to a dashboard based on their role."""
        if user.role == 'admin' or user.is_superuser:
            return redirect('adminpanel:dashboard')
        elif user.role == 'host':
            return redirect('host:dashboard')
        elif user.role == 'planner':
            return redirect('planner:dashboard')
        elif user.role == 'guest':
            return redirect('guest:dashboard')
        else:
            return redirect('accounts:home')  # fallback

    def get_success_url(self):
        """Optional: Override default success URL just in case."""
        return reverse_lazy('accounts:home')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:home')

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, 'Profile updated successfully.')
        return reverse_lazy('profile_edit')

class AddHostView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CustomUser
    form_class = None  # Dynamic
    template_name = 'accounts/add_host.html'
    success_url = reverse_lazy('accounts:home')

    def test_func(self):
        return self.request.user.is_superuser

    def get_form_class(self):
        class HostForm(forms.ModelForm):
            class Meta:
                model = CustomUser
                fields = ['username', 'email', 'full_name', 'mobile_number', 'address', 'profile_picture']
                widgets = {
                    'address': forms.Textarea(attrs={'rows': 3}),
                }
            
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Make fields required
                self.fields['full_name'].required = True
                self.fields['mobile_number'].required = True
                self.fields['address'].required = True
                # Add labels and help text
                self.fields['full_name'].label = 'Full Name '
                self.fields['mobile_number'].label = 'Mobile Number '
                self.fields['mobile_number'].help_text = '10 digits starting with 6, 7, 8, or 9'
                self.fields['address'].label = 'Address '
                
            def clean_mobile_number(self):
                mobile = self.cleaned_data.get('mobile_number')
                if mobile:
                    if not mobile.isdigit() or len(mobile) != 10 or mobile[0] not in '6789':
                        raise forms.ValidationError("Mobile number must be exactly 10 digits starting with 6, 7, 8, or 9.")
                return mobile
        
        return HostForm

    def form_valid(self, form):
        form.instance.role = 'host'
        form.instance.is_approved = True
        form.instance.is_active = True
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        form.instance.set_password(password)
        response = super().form_valid(form)
        
        # Send email with error handling
        try:
            send_mail(
                'Welcome to EventApp - Your Account Details',
                f'Dear {form.instance.full_name},\n\n'
                f'Your host account has been created by the admin.\n'
                f'Username: {form.instance.username}\n'
                f'Temporary Password: {password}\n\n'
                f'Please login at /accounts/login/ and change your password immediately.\n\n'
                f'Best regards,\nEventApp Team',
                settings.DEFAULT_FROM_EMAIL,
                [form.instance.email],
                fail_silently=False,
            )
            messages.success(self.request, f'Host "{form.instance.username}" added successfully. Credentials emailed to {form.instance.email}.')
        except Exception as e:
            messages.warning(self.request, f'Host "{form.instance.username}" created but email failed: {str(e)}')
        
        return response



# Password views (custom templates)
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:home')

    def form_valid(self, form):
        messages.success(self.request, 'Password changed successfully.')
        return super().form_valid(form)

class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'  # Optional custom email template
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'