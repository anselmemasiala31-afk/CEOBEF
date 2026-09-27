from uuid import uuid4

from django import forms
from django.utils.text import slugify

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ('title', 'summary', 'description', 'location', 'starts_at', 'ends_at', 'image', 'capacity', 'status')
        widgets = {'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}), 'ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'})}

    def clean(self):
        cleaned = super().clean()
        starts_at = cleaned.get('starts_at')
        ends_at = cleaned.get('ends_at')
        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error('ends_at', 'La fin doit être postérieure au début.')
        return cleaned

    def save(self, commit=True):
        event = super().save(commit=False)
        event.slug = f'{slugify(event.title)[:175]}-{uuid4().hex[:6]}'
        if commit:
            event.save()
        return event