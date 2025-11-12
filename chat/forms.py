from django import forms

class MessageForm(forms.Form):
    content = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={'rows': 1, 'placeholder': 'Type your message...', 'class': 'form-control'}),
        label=False
    )

    def clean_content(self):
        content = self.cleaned_data['content'].strip()
        if not content:
            raise forms.ValidationError('Message cannot be empty.')
        return content