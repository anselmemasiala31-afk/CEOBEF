from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CommunityConfig(AppConfig):
    name = 'community'

    def ready(self):
        from . import signals
