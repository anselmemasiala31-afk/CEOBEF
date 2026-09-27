from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification
from .services import broadcast_notification


@receiver(post_save, sender=Notification)
def publish_notification(sender, instance, created, **kwargs):
    if created:
        payload = {
            'id': instance.pk,
            'category': instance.category,
            'title': instance.title,
            'body': instance.body,
            'url': instance.url,
            'created_at': instance.created_at.isoformat(),
        }
        transaction.on_commit(lambda: broadcast_notification(instance.user_id, payload))