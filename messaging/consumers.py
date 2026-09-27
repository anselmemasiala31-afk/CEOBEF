from datetime import timedelta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .models import Conversation, Message, MessageReadReceipt, PresenceConnection


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        user = self.scope['user']
        if not user.is_authenticated or not await self.is_participant(user.pk, self.conversation_id):
            await self.close(code=4403)
            return
        self.group_name = f'chat_{self.conversation_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.register_presence(user.pk, self.channel_name)
        await self.broadcast_presence(user.pk, True)
        await self.send_json({'type': 'history', 'messages': await self.load_history(user.pk, self.conversation_id)})

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            user_id = self.scope['user'].pk
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await self.remove_presence(self.channel_name)
            await self.broadcast_presence(user_id, False)

    async def receive_json(self, content, **kwargs):
        action = content.get('action')
        user = self.scope['user']
        if action == 'message':
            text = str(content.get('content', '')).strip()[:4000]
            if text:
                message = await self.store_message(user.pk, self.conversation_id, text)
                await self.channel_layer.group_send(self.group_name, {'type': 'chat_message', 'message': message})
        elif action == 'typing':
            await self.channel_layer.group_send(self.group_name, {'type': 'typing_update', 'user_id': user.pk, 'name': user.get_full_name() or user.username, 'active': bool(content.get('active'))})
        elif action == 'read':
            await self.mark_read(user.pk, self.conversation_id)
            await self.channel_layer.group_send(self.group_name, {'type': 'read_update', 'user_id': user.pk})
        elif action == 'heartbeat':
            await self.touch_presence(self.channel_name)

    async def chat_message(self, event):
        await self.send_json({'type': 'message', **event['message']})

    async def typing_update(self, event):
        if event['user_id'] != self.scope['user'].pk:
            await self.send_json({'type': 'typing', **event})

    async def read_update(self, event):
        await self.send_json({'type': 'read', **event})

    async def presence_update(self, event):
        await self.send_json({'type': 'presence', **event})

    async def broadcast_presence(self, user_id, online):
        user_ids = await self.online_participants(self.conversation_id)
        await self.channel_layer.group_send(self.group_name, {'type': 'presence_update', 'user_id': user_id, 'online': online, 'online_user_ids': user_ids})

    @database_sync_to_async
    def is_participant(self, user_id, conversation_id):
        return Conversation.objects.filter(pk=conversation_id, participants__id=user_id).exists()

    @database_sync_to_async
    def load_history(self, user_id, conversation_id):
        messages = Message.objects.filter(conversation_id=conversation_id).select_related('sender').prefetch_related('read_receipts').order_by('-created_at')[:60]
        messages = list(reversed(messages))
        MessageReadReceipt.objects.bulk_create([MessageReadReceipt(message=message, user_id=user_id) for message in messages if message.sender_id != user_id and not message.read_receipts.filter(user_id=user_id).exists()], ignore_conflicts=True)
        return [self.serialize(message) for message in messages]

    @database_sync_to_async
    def store_message(self, user_id, conversation_id, text):
        conversation = Conversation.objects.get(pk=conversation_id)
        message = Message.objects.create(conversation=conversation, sender_id=user_id, content=text)
        conversation.save(update_fields=['updated_at'])
        return self.serialize(message)

    @database_sync_to_async
    def mark_read(self, user_id, conversation_id):
        unread = Message.objects.filter(conversation_id=conversation_id).exclude(sender_id=user_id).exclude(read_receipts__user_id=user_id)
        MessageReadReceipt.objects.bulk_create([MessageReadReceipt(message=message, user_id=user_id) for message in unread], ignore_conflicts=True)

    @database_sync_to_async
    def register_presence(self, user_id, channel_name):
        PresenceConnection.objects.update_or_create(channel_name=channel_name, defaults={'user_id': user_id})

    @database_sync_to_async
    def remove_presence(self, channel_name):
        PresenceConnection.objects.filter(channel_name=channel_name).delete()

    @database_sync_to_async
    def touch_presence(self, channel_name):
        PresenceConnection.objects.filter(channel_name=channel_name).update(last_seen=timezone.now())

    @database_sync_to_async
    def online_participants(self, conversation_id):
        cutoff = timezone.now() - timedelta(minutes=2)
        return list(PresenceConnection.objects.filter(user__conversations__id=conversation_id, last_seen__gte=cutoff).values_list('user_id', flat=True).distinct())

    @staticmethod
    def serialize(message):
        return {'id': message.pk, 'sender_id': message.sender_id, 'sender': message.sender.get_full_name() or message.sender.username, 'content': message.content, 'attachment_url': f'/messagerie/{message.conversation_id}/fichier/{message.pk}/' if message.attachment else '', 'created_at': message.created_at.isoformat(), 'read': message.read_receipts.exists()}


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close(code=4401)
            return
        self.group_name = f'user_{user.pk}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification(self, event):
        await self.send_json(event['data'])