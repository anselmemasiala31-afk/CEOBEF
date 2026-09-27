from asgiref.sync import async_to_sync
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase
from django.urls import reverse

from accounts.models import User
from .models import Conversation, Message
from .routing import websocket_urlpatterns


class ChatConsumerTests(TransactionTestCase):
	def setUp(self):
		self.member = User.objects.create_user(username='chat-member', email='chat@example.com', password='Secure-pass-449!')
		self.outsider = User.objects.create_user(username='outsider', email='outsider@example.com', password='Secure-pass-449!')
		self.conversation = Conversation.objects.create(kind=Conversation.Kind.GROUP, title='Groupe test', created_by=self.member)
		self.conversation.participants.add(self.member)
		self.message = Message.objects.create(conversation=self.conversation, sender=self.member, content='Bienvenue au groupe.')

	def test_participant_receives_history_and_can_send_persistent_message(self):
		async_to_sync(self._test_authorized_socket)()
		self.assertTrue(Message.objects.filter(conversation=self.conversation, content='Bonjour la communauté.').exists())

	async def _test_authorized_socket(self):
		communicator = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f'/ws/chat/{self.conversation.pk}/')
		communicator.scope['user'] = self.member
		connected, _ = await communicator.connect()
		self.assertTrue(connected)
		history = await communicator.receive_json_from()
		self.assertEqual(history['type'], 'history')
		self.assertEqual(history['messages'][0]['content'], self.message.content)
		await communicator.send_json_to({'action': 'message', 'content': 'Bonjour la communauté.'})
		message = await communicator.receive_json_from()
		while message['type'] != 'message':
			message = await communicator.receive_json_from()
		self.assertEqual(message['type'], 'message')
		self.assertEqual(message['content'], 'Bonjour la communauté.')
		await communicator.disconnect()

	def test_nonparticipant_is_rejected(self):
		async_to_sync(self._test_unauthorized_socket)()

	async def _test_unauthorized_socket(self):
		communicator = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f'/ws/chat/{self.conversation.pk}/')
		communicator.scope['user'] = self.outsider
		connected, close_code = await communicator.connect()
		self.assertFalse(connected)
		self.assertEqual(close_code, 4403)

	def test_anonymous_user_is_rejected(self):
		async_to_sync(self._test_anonymous_socket)()

	async def _test_anonymous_socket(self):
		communicator = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f'/ws/chat/{self.conversation.pk}/')
		communicator.scope['user'] = AnonymousUser()
		connected, close_code = await communicator.connect()
		self.assertFalse(connected)
		self.assertEqual(close_code, 4403)

	def test_member_can_create_group_with_selected_active_members(self):
		self.client.force_login(self.member)
		response = self.client.post(reverse('messaging:create-group'), {'title': 'Projet entraide', 'members': [self.outsider.pk]})
		conversation = Conversation.objects.get(title='Projet entraide')
		self.assertRedirects(response, reverse('messaging:detail', args=[conversation.pk]))
		self.assertSetEqual(set(conversation.participants.values_list('pk', flat=True)), {self.member.pk, self.outsider.pk})
