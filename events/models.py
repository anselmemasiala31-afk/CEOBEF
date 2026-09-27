from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Event(models.Model):
	class Status(models.TextChoices):
		DRAFT = 'draft', 'Brouillon'
		PUBLISHED = 'published', 'Publié'
		CANCELLED = 'cancelled', 'Annulé'

	title = models.CharField('titre', max_length=180)
	slug = models.SlugField('identifiant', max_length=200, unique=True)
	summary = models.CharField('résumé', max_length=280)
	description = models.TextField('description')
	location = models.CharField('lieu', max_length=180)
	starts_at = models.DateTimeField('début')
	ends_at = models.DateTimeField('fin')
	image = models.ImageField('visuel', upload_to='events/%Y/%m/', blank=True)
	capacity = models.PositiveIntegerField('capacité', null=True, blank=True, validators=[MinValueValidator(1)])
	status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_events')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['starts_at']
		permissions = [('publish_event', 'Peut publier un événement')]
		indexes = [models.Index(fields=['status', 'starts_at'])]

	def __str__(self):
		return self.title

	@property
	def participant_count(self):
		return self.rsvps.filter(status=EventRSVP.Status.GOING).count()


class EventRSVP(models.Model):
	class Status(models.TextChoices):
		GOING = 'going', 'Participe'
		MAYBE = 'maybe', 'À confirmer'
		DECLINED = 'declined', 'Ne participe pas'

	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_rsvps')
	status = models.CharField(max_length=10, choices=Status.choices, default=Status.GOING)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=['event', 'user'], name='unique_event_rsvp')]
		indexes = [models.Index(fields=['event', 'status'])]

	def __str__(self):
		return f'{self.user} - {self.event}: {self.get_status_display()}'

# Create your models here.
