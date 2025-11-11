from django import forms
from accounts.models import CustomUser

class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'mobile_number', 'address', 'profile_picture', 'is_active']
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