from django import forms

from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('title', 'description', 'category', 'file', 'is_public')

