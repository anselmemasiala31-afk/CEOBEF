from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from community.models import Notification
from core.permissions import permissions_required
from .forms import EventForm
from .models import Event, EventRSVP


def event_list(request):
    events = Event.objects.filter(status=Event.Status.PUBLISHED).annotate(
        attendee_count=Count('rsvps', filter=Q(rsvps__status=EventRSVP.Status.GOING))
    ).order_by('starts_at')
    page = Paginator(events, 9).get_page(request.GET.get('page'))
    return render(request, 'events/list.html', {'page': page})


def event_detail(request, slug):
    event = get_object_or_404(Event.objects.annotate(
        attendee_count=Count('rsvps', filter=Q(rsvps__status=EventRSVP.Status.GOING))
    ), slug=slug)
    if event.status != Event.Status.PUBLISHED and (not request.user.is_authenticated or not request.user.has_perm('events.change_event')):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied
    rsvp = EventRSVP.objects.filter(event=event, user=request.user).first() if request.user.is_authenticated else None
    return render(request, 'events/detail.html', {'event': event, 'rsvp': rsvp})


@require_POST
@login_required
def rsvp(request, slug):
    with transaction.atomic():
        event = get_object_or_404(Event.objects.select_for_update(), slug=slug, status=Event.Status.PUBLISHED)
        response = EventRSVP.objects.filter(event=event, user=request.user).first()
        is_new_participation = not response or response.status != EventRSVP.Status.GOING
        if is_new_participation:
            going_count = event.rsvps.filter(status=EventRSVP.Status.GOING).count()
            if event.capacity and going_count >= event.capacity:
                messages.error(request, 'Les places disponibles sont épuisées.')
                return redirect('events:detail', slug=slug)
        EventRSVP.objects.update_or_create(event=event, user=request.user, defaults={'status': EventRSVP.Status.GOING})
        if is_new_participation and event.created_by_id != request.user.pk:
            Notification.objects.create(
                user=event.created_by,
                category=Notification.Category.EVENT,
                title=f'Nouvelle participation : {event.title}',
                body=request.user.get_full_name() or request.user.username,
                url=f'/evenements/{event.slug}/',
            )
    messages.success(request, 'Votre participation est confirmée.')
    return redirect('events:detail', slug=slug)


@login_required
@permissions_required('events.add_event')
def event_create(request):
    form = EventForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.created_by = request.user
        event.save()
        messages.success(request, 'L’événement a été enregistré.')
        return redirect('events:detail', slug=event.slug)
    return render(request, 'events/form.html', {'form': form})
