from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class RenderAdminBootstrapTests(TestCase):
	@patch.dict('os.environ', {
		'DJANGO_SUPERUSER_USERNAME': 'render-admin',
		'DJANGO_SUPERUSER_EMAIL': 'admin@example.com',
		'DJANGO_SUPERUSER_PASSWORD': 'Long-unique-password-947!x',
	})
	def test_bootstrap_creates_superuser_and_is_idempotent(self):
		call_command('bootstrap_render_admin', verbosity=0)
		user = get_user_model().objects.get(username='render-admin')
		self.assertTrue(user.is_superuser)
		self.assertTrue(user.is_staff)
		self.assertEqual(user.email, 'admin@example.com')
		original_password = user.password

		with patch.dict('os.environ', {'DJANGO_SUPERUSER_PASSWORD': 'A-different-password-827!x'}):
			call_command('bootstrap_render_admin', verbosity=0)

		user.refresh_from_db()
		self.assertEqual(user.password, original_password)

	@patch.dict('os.environ', {
		'DJANGO_SUPERUSER_USERNAME': '',
		'DJANGO_SUPERUSER_EMAIL': '',
		'DJANGO_SUPERUSER_PASSWORD': '',
	})
	def test_bootstrap_requires_environment_secrets(self):
		with self.assertRaises(CommandError):
			call_command('bootstrap_render_admin', verbosity=0)
