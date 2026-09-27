from django.db import models
from django.conf import settings


class Announcement(models.Model):
	class Category(models.TextChoices):
		NEWS = 'news', 'Actualité'
		NOTICE = 'notice', 'Communiqué'
		SUCCESS = 'success', 'Réussite'
		COMMUNITY = 'community', 'Communauté'

	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='announcements')
	title = models.CharField('titre', max_length=180)
	body = models.TextField('contenu')
	category = models.CharField(max_length=12, choices=Category.choices, default=Category.NEWS)
	image = models.ImageField('image', upload_to='announcements/%Y/%m/', blank=True)
	published = models.BooleanField('publiée', default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [models.Index(fields=['published', '-created_at'])]

	def __str__(self):
		return self.title


class Comment(models.Model):
	announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='comments')
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='comments')
	body = models.TextField('commentaire', max_length=1000)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at']

	def __str__(self):
		return f'Commentaire de {self.author}'


class Notification(models.Model):
	class Category(models.TextChoices):
		EVENT = 'event', 'Événement'
		ANNOUNCEMENT = 'announcement', 'Annonce'
		DOCUMENT = 'document', 'Document'
		MESSAGE = 'message', 'Message'
		CONTRIBUTION = 'contribution', 'Cotisation'
		SYSTEM = 'system', 'Système'

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
	category = models.CharField(max_length=20, choices=Category.choices)
	title = models.CharField(max_length=180)
	body = models.CharField(max_length=300, blank=True)
	url = models.CharField(max_length=300, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	read_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [models.Index(fields=['user', 'read_at', '-created_at'])]

	def __str__(self):
		return f'{self.title} ({self.user})'


class GalleryAlbum(models.Model):
	title = models.CharField('album', max_length=160)
	event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True, related_name='albums')
	year = models.PositiveSmallIntegerField('année')
	cover = models.ImageField(upload_to='gallery/covers/%Y/', blank=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-year', 'title']

	def __str__(self):
		return self.title


class GalleryPhoto(models.Model):
	album = models.ForeignKey(GalleryAlbum, on_delete=models.CASCADE, related_name='photos')
	image = models.ImageField(upload_to='gallery/photos/%Y/%m/')
	caption = models.CharField(max_length=240, blank=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['uploaded_at']

	def __str__(self):
		return self.caption or self.image.name

# Create your models here.
