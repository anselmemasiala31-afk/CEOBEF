from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import StudentProfile, User


class RegistrationForm(UserCreationForm):
    photo = forms.ImageField(label='Photo de profil')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {'username': 'Nom d’utilisateur', 'first_name': 'Prénom', 'last_name': 'Nom', 'email': 'Adresse e-mail'}


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(label='Prénom', max_length=150)
    last_name = forms.CharField(label='Nom', max_length=150)
    email = forms.EmailField(label='Adresse e-mail')

    class Meta:
        model = StudentProfile
        fields = ('photo', 'university', 'faculty', 'study_year', 'hometown', 'phone', 'bio')

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists():
            raise ValidationError('Cette adresse e-mail est déjà utilisée.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        if commit:
            self.user.save(update_fields=['first_name', 'last_name', 'email'])
        return profile