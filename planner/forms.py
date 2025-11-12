from django import forms
from host.models import Proposal

class ProposalForm(forms.ModelForm):
    services = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), help_text="List services offered (e.g., Catering + Decorations)")
    timeline = forms.CharField(max_length=255, required=False, help_text="Setup timeline (e.g., 3 days)")

    class Meta:
        model = Proposal
        fields = ['amount', 'services', 'timeline']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': 0.01, 'step': '0.01'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')
        return amount

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        if event:
            self.instance.event = event