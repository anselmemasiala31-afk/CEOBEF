from django.db import models
from django.conf import settings

from .validators import validate_document_file


class Document(models.Model):
	class Category(models.TextChoices):
		ACADEMIC = 'academic', 'Académique'
		ADMINISTRATIVE = 'administrative', 'Administratif'
		COMMUNITY = 'community', 'Communauté'
		FINANCIAL = 'financial', 'Financier'

	title = models.CharField('titre', max_length=180)
	description = models.TextField('description', blank=True)
	category = models.CharField(max_length=20, choices=Category.choices, default=Category.COMMUNITY)
	file = models.FileField(upload_to='documents/%Y/%m/', validators=[validate_document_file])
	original_name = models.CharField(max_length=255, blank=True)
	uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='uploaded_documents')
	is_public = models.BooleanField('accessible aux membres', default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		permissions = [('download_document', 'Peut télécharger les documents réservés')]
		indexes = [models.Index(fields=['category', '-created_at'])]

	def __str__(self):
		return self.title

# Create your models here.
