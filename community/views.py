from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from core.permissions import permissions_required
from .forms import AnnouncementForm, CommentForm
from .models import Announcement, GalleryAlbum, Notification
from .services import notify_users


def announcement_list(request):
    items = Announcement.objects.filter(published=True).select_related('author', 'author__profile').prefetch_related('comments__author')
    page = Paginator(items, 10).get_page(request.GET.get('page'))
    return render(request, 'community/announcements.html', {'page': page})


@login_required
@permissions_required('community.add_announcement')
def announcement_create(request):
    form = AnnouncementForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        announcement = form.save(commit=False)
        announcement.author = request.user
        announcement.save()
        if announcement.published:
            notify_users(
                User.objects.filter(is_active=True).exclude(pk=request.user.pk).values_list('id', flat=True),
                category=Notification.Category.ANNOUNCEMENT,
                title=announcement.title,
                body=announcement.body[:280],
                url='/actualites/',
            )
        messages.success(request, 'La publication a été enregistrée.')
        return redirect('community:announcements')
    return render(request, 'community/announcement_form.html', {'form': form})


@require_POST
@login_required
def add_comment(request, announcement_id):
    announcement = get_object_or_404(Announcement, pk=announcement_id, published=True)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.announcement = announcement
        comment.author = request.user
        comment.save()
        if announcement.author_id != request.user.pk:
            Notification.objects.create(user=announcement.author, category=Notification.Category.ANNOUNCEMENT, title='Nouveau commentaire', body=comment.body[:280], url='/actualites/')
    return redirect('community:announcements')


@login_required
def notifications(request):
    page = Paginator(request.user.notifications.all(), 30).get_page(request.GET.get('page'))
    return render(request, 'community/notifications.html', {'page': page})


@require_POST
@login_required
def mark_notifications_read(request):
    request.user.notifications.filter(read_at__isnull=True).update(read_at=timezone.now())
    target = request.POST.get('next', '')
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(target)
    return redirect('community:notifications')


def gallery(request):
    albums = GalleryAlbum.objects.prefetch_related('photos').select_related('event')
    year = request.GET.get('year')
    if year and year.isdecimal():
        albums = albums.filter(year=int(year))
    years = GalleryAlbum.objects.order_by().values_list('year', flat=True).distinct()
    return render(request, 'community/gallery.html', {'albums': albums, 'years': years, 'selected_year': year})
