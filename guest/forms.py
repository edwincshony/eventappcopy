from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['ticket_quantity']
        widgets = {
            'ticket_quantity': forms.NumberInput(attrs={'min': 1, 'max': 10}),
        }

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        if event:
            self.fields['ticket_quantity'].help_text = f"Tickets for {event.name} (₹{event.budget / event.guest_count:.2f} each approx.)"

    def clean_ticket_quantity(self):
        quantity = self.cleaned_data['ticket_quantity']
        if quantity < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return quantity

class PaymentForm(forms.Form):
    card_number = forms.CharField(
        max_length=20,
        min_length=20,
        widget=forms.TextInput(attrs={'placeholder': '1234 5678 9012 3456'})
    )
    expiry_date = forms.CharField(max_length=5, widget=forms.TextInput(attrs={'placeholder': 'MM/YY'}))
    cvv = forms.CharField(max_length=3, widget=forms.PasswordInput(attrs={'placeholder': '123'}))
    name_on_card = forms.CharField(max_length=255)

    def clean_card_number(self):
        card = self.cleaned_data['card_number'].replace(' ', '')
        if len(card) != 16 or not card.isdigit():
            raise forms.ValidationError('Invalid card number.')
        return card