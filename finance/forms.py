from django import forms

from accounts.models import User
from .models import Contribution


class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ('member', 'amount', 'currency', 'period', 'reference', 'status', 'receipt')
        widgets = {'member': forms.Select(attrs={'class': 'field-control'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name')