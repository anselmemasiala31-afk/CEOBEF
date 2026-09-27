from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver

from messaging.models import Conversation
from .models import StudentProfile, User


@receiver(post_save, sender=User)
def provision_member(sender, instance, created, **kwargs):
    if created:
        StudentProfile.objects.get_or_create(user=instance)
    should_be_staff = instance.is_superuser or instance.role == User.Role.ADMIN
    if instance.is_staff != should_be_staff:
        User.objects.filter(pk=instance.pk).update(is_staff=should_be_staff)
        instance.is_staff = should_be_staff
    if instance.is_active:
        for conversation in Conversation.objects.filter(official=True):
            conversation.participants.add(instance)
    group, _ = Group.objects.get_or_create(name=f'CEOBEF: {instance.get_role_display()}')
    stale_groups = list(instance.groups.filter(name__startswith='CEOBEF: ').exclude(pk=group.pk))
    if stale_groups:
        instance.groups.remove(*stale_groups)
    instance.groups.add(group)


def ensure_role_groups(sender, **kwargs):
    role_permissions = {
        User.Role.SECRETARY: [('events', 'add_event'), ('events', 'change_event'), ('community', 'add_announcement'), ('community', 'change_announcement'), ('library', 'add_document'), ('library', 'download_document')],
        User.Role.TREASURER: [('finance', 'view_contribution'), ('finance', 'add_contribution'), ('finance', 'change_contribution'), ('finance', 'view_all_contributions'), ('library', 'download_document')],
        User.Role.PRESIDENT: [('events', 'add_event'), ('events', 'change_event'), ('community', 'add_announcement'), ('community', 'change_announcement'), ('library', 'add_document'), ('library', 'download_document'), ('finance', 'add_contribution'), ('finance', 'change_contribution'), ('finance', 'view_all_contributions')],
    }
    for role, label in User.Role.choices:
        group, _ = Group.objects.get_or_create(name=f'CEOBEF: {label}')
        if role == User.Role.ADMIN:
            group.permissions.set(Permission.objects.all())
        elif role in role_permissions:
            permissions = [Permission.objects.filter(content_type__app_label=app, codename=code).first() for app, code in role_permissions[role]]
            group.permissions.set([permission for permission in permissions if permission])