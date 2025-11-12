from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Event, Proposal

class EventForm(forms.ModelForm):
    needs = forms.MultipleChoiceField(
        choices=Event.NEEDS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select required services"
    )

    class Meta:
        model = Event
        fields = ['name', 'start_date', 'end_date', 'budget', 'guest_count', 'needs', 'banner', 'venue_details']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'venue_details': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # JS for future dates (template handles min date)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        budget = cleaned_data.get('budget')
        guest_count = cleaned_data.get('guest_count')

        if start_date and start_date <= timezone.now():
            raise ValidationError('Start date must be in the future.')
        if end_date and start_date and end_date <= start_date:
            raise ValidationError('End date must be after start date.')
        if budget and budget <= 0:
            raise ValidationError('Budget must be greater than 0.')
        if guest_count and guest_count <= 0:
            raise ValidationError('Guest count must be greater than 0.')

        # Handle multi needs
        needs = cleaned_data.get('needs', [])
        cleaned_data['needs'] = ','.join(needs)
        return cleaned_data


class ProposalAcceptForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ['status']

    def clean_status(self):
        status = self.cleaned_data['status']
        if status not in ['accepted', 'rejected']:
            raise ValidationError('Invalid status.')
        return status