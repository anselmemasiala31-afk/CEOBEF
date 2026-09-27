from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from .models import Notification


def broadcast_notification(user_id, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'user_{user_id}', {'type': 'notification', 'data': data})


def notify_users(user_ids, *, category, title, body='', url=''):
    recipients = list(user_ids)
    if not recipients:
        return
    Notification.objects.bulk_create([
        Notification(user_id=user_id, category=category, title=title, body=body[:300], url=url)
        for user_id in recipients
    ], batch_size=500)
    payload = {'category': category, 'title': title, 'body': body[:300], 'url': url}

    def publish():
        for user_id in recipients:
            broadcast_notification(user_id, payload)

    transaction.on_commit(publish)