from io import BytesIO
from datetime import timedelta

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail, signing
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from community.models import Announcement, Notification
from events.models import Event, EventRSVP
from library.models import Document
from messaging.models import Conversation, Message


TEST_STORAGES = {
	'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
	'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def png_upload():
	image_data = BytesIO()
	Image.new('RGB', (1, 1), color='green').save(image_data, format='PNG')
	return SimpleUploadedFile('profile.png', image_data.getvalue(), content_type='image/png')


def create_member(username, email=None, **kwargs):
	return User.objects.create_user(
		username=username,
		email=email or f'{username}@example.com',
		password='Strong-password-842!',
		**kwargs,
	)


@override_settings(STORAGES=TEST_STORAGES)
class PublicPagesTests(TestCase):
	def test_homepage_and_member_landing_pages_render(self):
		for url in ('core:home', 'events:list', 'community:announcements', 'community:gallery', 'accounts:executive'):
			with self.subTest(url=url):
				response = self.client.get(reverse(url))
				self.assertEqual(response.status_code, 200)

	def test_registration_requires_a_valid_profile_photo_and_sends_verification_email(self):
		with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
			response = self.client.post(reverse('accounts:register'), {
				'username': 'new-student',
				'first_name': 'Aline',
				'last_name': 'Mavungu',
				'email': 'aline@example.com',
				'password1': 'A-very-Strong-pass-482!',
				'password2': 'A-very-Strong-pass-482!',
				'photo': png_upload(),
			})
			user = User.objects.get(username='new-student')
			self.assertRedirects(response, reverse('accounts:login'))
			self.assertFalse(user.is_active)
			self.assertFalse(user.email_verified)
			self.assertTrue(user.profile.photo)

			response = self.client.get(reverse('accounts:verify-email', args=[signing.dumps(user.pk, salt='ceobef.accounts.email-verification')]))
			user.refresh_from_db()
			self.assertRedirects(response, reverse('accounts:login'))
			self.assertTrue(user.is_active)
			self.assertTrue(user.email_verified)
			self.assertEqual(user.conversations.filter(official=True).count(), 2)

	def test_registration_rejects_missing_profile_photo(self):
		response = self.client.post(reverse('accounts:register'), {
			'username': 'no-photo',
			'first_name': 'Jean',
			'last_name': 'Lukusa',
			'email': 'jean@example.com',
			'password1': 'A-very-Strong-pass-482!',
			'password2': 'A-very-Strong-pass-482!',
		})
		self.assertEqual(response.status_code, 200)
		self.assertFalse(User.objects.filter(username='no-photo').exists())


@override_settings(STORAGES=TEST_STORAGES)
class EventWorkflowTests(TestCase):
	def setUp(self):
		self.member = create_member('event-member')
		self.event = Event.objects.create(
			title='Rencontre étudiante',
			slug='rencontre-etudiante',
			summary='Une rencontre de la communauté.',
			description='Présentation et échanges.',
			location='Matadi',
			starts_at=timezone.now() + timedelta(days=4),
			ends_at=timezone.now() + timedelta(days=4, hours=2),
			capacity=1,
			status=Event.Status.PUBLISHED,
			created_by=self.member,
		)

	def test_member_can_confirm_once_and_event_capacity_is_enforced(self):
		first = create_member('first-rsvp')
		second = create_member('second-rsvp')
		self.client.force_login(first)
		response = self.client.post(reverse('events:rsvp', args=[self.event.slug]))
		self.assertRedirects(response, reverse('events:detail', args=[self.event.slug]))
		self.assertEqual(self.event.rsvps.filter(status=EventRSVP.Status.GOING).count(), 1)

		self.client.force_login(second)
		self.client.post(reverse('events:rsvp', args=[self.event.slug]))
		self.assertFalse(self.event.rsvps.filter(user=second, status=EventRSVP.Status.GOING).exists())

	def test_member_cannot_publish_event(self):
		self.client.force_login(self.member)
		response = self.client.get(reverse('events:create'))
		self.assertEqual(response.status_code, 403)


@override_settings(STORAGES=TEST_STORAGES)
class AccessControlTests(TestCase):
	def test_member_only_sees_public_documents_and_private_attachment_requires_membership(self):
		member = create_member('reader')
		other_member = create_member('other-reader')
		self.client.force_login(member)
		public_document = Document.objects.create(title='Guide public', category='academic', file='documents/guide.pdf', uploaded_by=other_member, is_public=True)
		private_document = Document.objects.create(title='Dossier interne', category='financial', file='documents/secret.pdf', uploaded_by=other_member, is_public=False)
		response = self.client.get(reverse('library:list'))
		self.assertContains(response, public_document.title)
		self.assertNotContains(response, private_document.title)
		self.assertEqual(self.client.get(reverse('library:download', args=[private_document.pk])).status_code, 404)

		conversation = Conversation.objects.create(kind=Conversation.Kind.DIRECT, direct_key='1:2', created_by=other_member)
		conversation.participants.add(other_member)
		attachment = Message.objects.create(conversation=conversation, sender=other_member, attachment='chat/private.pdf', attachment_name='private.pdf')
		response = self.client.get(reverse('messaging:download-attachment', args=[conversation.pk, attachment.pk]))
		self.assertEqual(response.status_code, 404)

	def test_only_officers_can_publish_announcement(self):
		member = create_member('ordinary')
		self.client.force_login(member)
		self.assertEqual(self.client.get(reverse('community:announcement-create')).status_code, 403)

	def test_notification_read_redirect_rejects_external_hosts(self):
		member = create_member('notify-me')
		Notification.objects.create(user=member, category=Notification.Category.SYSTEM, title='Bienvenue')
		self.client.force_login(member)
		response = self.client.post(reverse('community:mark-read'), {'next': 'https://example.org'})
		self.assertRedirects(response, reverse('community:notifications'))


@override_settings(STORAGES=TEST_STORAGES)
class AccountIntegrationTests(TestCase):
	def test_dashboard_requires_authenticated_member(self):
		response = self.client.get(reverse('core:dashboard'))
		self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('core:dashboard')}")

	def test_authenticated_member_workspaces_render(self):
		member = create_member('workspace-member')
		self.client.force_login(member)
		for url in ('core:dashboard', 'accounts:profile', 'library:list', 'finance:list', 'messaging:list', 'community:notifications'):
			with self.subTest(url=url):
				self.assertEqual(self.client.get(reverse(url)).status_code, 200)

	def test_administrator_role_is_staff_but_not_superuser(self):
		administrator = create_member('ceobef-admin', role=User.Role.ADMIN)
		self.assertTrue(administrator.is_staff)
		self.assertFalse(administrator.is_superuser)

	def test_event_publication_records_notifications(self):
		member = create_member('alerted-member', is_superuser=False)
		officer = create_member('event-officer')
		with self.captureOnCommitCallbacks(execute=True):
			Event.objects.create(
				title='Assemblée', slug='assemblee-annuelle', summary='Assemblée générale.', description='Ordre du jour.',
				location='Boma', starts_at=timezone.now() + timedelta(days=10), ends_at=timezone.now() + timedelta(days=10, hours=1),
				status=Event.Status.PUBLISHED, created_by=officer,
			)
		self.assertTrue(Notification.objects.filter(user=member, category=Notification.Category.EVENT).exists())

	def test_event_email_recipients_are_private(self):
		first = create_member('first-recipient', email_verified=True)
		second = create_member('second-recipient', email_verified=True)
		officer = create_member('mailing-officer')
		with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
			with self.captureOnCommitCallbacks(execute=True):
				Event.objects.create(
					title='Rencontre privée', slug='rencontre-privee', summary='Rendez-vous CEOBEF.', description='Présentation.',
					location='Boma', starts_at=timezone.now() + timedelta(days=11), ends_at=timezone.now() + timedelta(days=11, hours=1),
					status=Event.Status.PUBLISHED, created_by=officer,
				)
		delivered = [message for message in mail.outbox if first.email in message.to or second.email in message.to]
		self.assertEqual(len(delivered), 2)
		self.assertTrue(all(len(message.to) == 1 for message in delivered))

	def test_changing_email_requires_a_new_verification(self):
		member = create_member('email-change', first_name='Aline', last_name='Mavungu')
		self.client.force_login(member)
		with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
			response = self.client.post(reverse('accounts:profile'), {
				'first_name': 'Aline',
				'last_name': 'Mavungu',
				'email': 'aline.new@example.com',
			})
		member.refresh_from_db()
		self.assertRedirects(response, reverse('accounts:login'))
		self.assertEqual(member.email, 'aline.new@example.com')
		self.assertFalse(member.is_active)
		self.assertFalse(member.email_verified)
