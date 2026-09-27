from django.conf import settings
from django.db import models
from django.db.models import Q


class Conversation(models.Model):
	class Kind(models.TextChoices):
		DIRECT = 'direct', 'Privée'
		GROUP = 'group', 'Groupe'

	kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.GROUP)
	title = models.CharField(max_length=120, blank=True)
	direct_key = models.CharField(max_length=42, blank=True)
	official = models.BooleanField(default=False)
	participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='started_conversations', null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-updated_at']
		constraints = [models.UniqueConstraint(fields=['direct_key'], condition=Q(kind='direct') & ~Q(direct_key=''), name='unique_direct_conversation_key')]

	def __str__(self):
		return self.title or f'Conversation {self.pk}'


class Message(models.Model):
	conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
	sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sent_messages')
	content = models.TextField(max_length=4000, blank=True)
	attachment = models.FileField(upload_to='chat/%Y/%m/', blank=True)
	attachment_name = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	edited_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['created_at']
		indexes = [models.Index(fields=['conversation', '-created_at'])]

	def __str__(self):
		return f'{self.sender}: {self.content[:60]}'


class MessageReadReceipt(models.Model):
	message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_receipts')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_receipts')
	read_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=['message', 'user'], name='unique_message_read_receipt')]


class PresenceConnection(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='presence_connections')
	channel_name = models.CharField(max_length=100, unique=True)
	connected_at = models.DateTimeField(auto_now_add=True)
	last_seen = models.DateTimeField(auto_now=True)

	class Meta:
		indexes = [models.Index(fields=['user', 'last_seen'])]
