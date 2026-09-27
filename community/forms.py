from django import forms

from .models import Announcement, Comment


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('title', 'body', 'category', 'image', 'published')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body',)
        widgets = {'body': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Écrire un commentaire…'})}