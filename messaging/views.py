from pathlib import Path

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from .models import Conversation, Message


@login_required
def conversation_list(request):
    conversations = request.user.conversations.prefetch_related('participants').order_by('-updated_at')
    query = request.GET.get('q', '').strip()
    if query:
        conversations = conversations.filter(title__icontains=query) | conversations.filter(participants__first_name__icontains=query) | conversations.filter(participants__last_name__icontains=query)
    members = User.objects.filter(is_active=True).exclude(pk=request.user.pk).order_by('first_name', 'last_name')[:50]
    conversations = list(conversations.distinct())
    for conversation in conversations:
        other_members = [member for member in conversation.participants.all() if member.pk != request.user.pk]
        conversation.display_title = conversation.title or ', '.join(member.get_full_name() or member.username for member in other_members) or 'Conversation privée'
    return render(request, 'messaging/list.html', {'conversations': conversations, 'members': members, 'query': query})


@require_POST
@login_required
def start_direct(request, user_id):
    recipient = get_object_or_404(User, pk=user_id, is_active=True)
    if recipient.pk == request.user.pk:
        messages.error(request, 'Vous ne pouvez pas démarrer une conversation avec vous-même.')
        return redirect('messaging:list')
    direct_key = ':'.join(map(str, sorted([recipient.pk, request.user.pk])))
    conversation, created = Conversation.objects.get_or_create(direct_key=direct_key, defaults={'kind': Conversation.Kind.DIRECT, 'created_by': request.user})
    if created:
        conversation.participants.add(request.user, recipient)
    return redirect('messaging:detail', pk=conversation.pk)


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation.objects.prefetch_related('participants'), pk=pk, participants=request.user)
    other_members = conversation.participants.exclude(pk=request.user.pk)
    title = conversation.title or ', '.join(member.get_full_name() or member.username for member in other_members)
    history = list(conversation.messages.select_related('sender').prefetch_related('read_receipts').order_by('-created_at')[:60])
    history.reverse()
    return render(request, 'messaging/chat.html', {'conversation': conversation, 'chat_title': title, 'history': history})


@require_POST
@login_required
def create_group(request):
    title = request.POST.get('title', '').strip()
    member_ids = request.POST.getlist('members')
    selected_members = list(User.objects.filter(pk__in=member_ids, is_active=True).exclude(pk=request.user.pk))
    if not title or len(title) > 120 or not selected_members:
        messages.error(request, 'Indiquez un nom de groupe et choisissez au moins un autre membre.')
        return redirect('messaging:list')
    conversation = Conversation.objects.create(kind=Conversation.Kind.GROUP, title=title, created_by=request.user)
    conversation.participants.add(request.user, *selected_members)
    return redirect('messaging:detail', pk=conversation.pk)


@require_POST
@login_required
def upload_attachment(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, participants=request.user)
    attachment = request.FILES.get('attachment')
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.webp'}
    if not attachment or Path(attachment.name).suffix.lower() not in allowed_extensions or attachment.size > 10 * 1024 * 1024:
        messages.error(request, 'Choisissez une image ou un PDF de 10 Mo maximum.')
        return redirect('messaging:detail', pk=conversation.pk)
    message = Message(conversation=conversation, sender=request.user, content=request.POST.get('content', '')[:4000], attachment=attachment, attachment_name=attachment.name)
    message.save()
    conversation.save(update_fields=['updated_at'])
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'chat_{conversation.pk}', {
        'type': 'chat_message',
        'message': {
            'id': message.pk,
            'sender_id': request.user.pk,
            'sender': request.user.get_full_name() or request.user.username,
            'content': message.content,
            'attachment_url': f'/messagerie/{conversation.pk}/fichier/{message.pk}/',
            'created_at': message.created_at.isoformat(),
            'read': False,
        },
    })
    return redirect('messaging:detail', pk=conversation.pk)


@login_required
def download_attachment(request, conversation_id, message_id):
    message = get_object_or_404(
        Message.objects.select_related('conversation'),
        pk=message_id,
        conversation_id=conversation_id,
        conversation__participants=request.user,
    )
    try:
        return FileResponse(message.attachment.open('rb'), as_attachment=True, filename=message.attachment_name or 'piece-jointe')
    except (OSError, ValueError) as error:
        raise Http404 from error
