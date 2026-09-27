from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from .models import Conversation


@receiver(post_save, sender=User)
def add_member_to_official_conversations(sender, instance, created, **kwargs):
    if created and instance.is_active:
        for conversation in Conversation.objects.filter(official=True):
            conversation.participants.add(instance)


def create_official_conversations(sender, **kwargs):
    creator = User.objects.filter(is_superuser=True).first() or User.objects.order_by('pk').first()
    for title in ('Annonces CEOBEF', 'Communauté Bas-Fleuve'):
        conversation, _ = Conversation.objects.get_or_create(
            title=title,
            official=True,
            defaults={'kind': Conversation.Kind.GROUP, 'created_by': creator},
        )
        conversation.participants.add(*User.objects.filter(is_active=True))