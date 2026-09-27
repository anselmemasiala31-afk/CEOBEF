import logging

from django.conf import settings
from django.core.mail import send_mass_mail
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from accounts.models import User
from community.models import Notification
from community.services import notify_users
from .models import Event

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Event)
def remember_event_publication(sender, instance, **kwargs):
    if instance.pk:
        instance._was_published = sender.objects.filter(pk=instance.pk, status=Event.Status.PUBLISHED).exists()
    else:
        instance._was_published = False


@receiver(post_save, sender=Event)
def notify_members_of_published_event(sender, instance, created, **kwargs):
    newly_published = instance.status == Event.Status.PUBLISHED and (created or not getattr(instance, '_was_published', False))
    if newly_published:
        transaction.on_commit(lambda: dispatch_event_notice(instance.pk))


def dispatch_event_notice(event_id):
    event = Event.objects.get(pk=event_id)
    members = User.objects.filter(is_active=True).exclude(pk=event.created_by_id)
    notify_users(
        members.values_list('id', flat=True),
        category=Notification.Category.EVENT,
        title=f'Nouvel événement : {event.title}',
        body=event.summary,
        url=f'/evenements/{event.slug}/',
    )
    recipients = members.filter(email_verified=True).values_list('email', flat=True).iterator(chunk_size=50)
    batch = []
    for email in recipients:
        batch.append(email)
        if len(batch) == 50:
            _send_event_email(event, batch)
            batch = []
    if batch:
        _send_event_email(event, batch)


def _send_event_email(event, recipients):
    try:
        subject = f'Nouvel événement CEOBEF : {event.title}'
        body = f'{event.summary}\n\n{event.starts_at:%d/%m/%Y à %H:%M} - {event.location}'
        send_mass_mail([
            (subject, body, settings.DEFAULT_FROM_EMAIL, [recipient])
            for recipient in recipients
        ], fail_silently=False)
    except Exception:
        logger.exception('Unable to send event announcement email for event %s', event.pk)