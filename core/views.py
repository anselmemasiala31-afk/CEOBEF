from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
import mimetypes

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from accounts.models import ExecutiveMember, User
from community.models import Announcement, GalleryAlbum, GalleryPhoto
from events.models import Event, EventRSVP
from finance.models import Contribution
from library.models import Document


def home(request):
    events = Event.objects.filter(status=Event.Status.PUBLISHED, starts_at__gte=timezone.now()).order_by('starts_at')[:3]
    news = Announcement.objects.filter(published=True).select_related('author')[:3]
    return render(request, 'core/home.html', {'events': events, 'news': news})


@login_required
def dashboard(request):
    now = timezone.now()
    upcoming_events = Event.objects.filter(status=Event.Status.PUBLISHED, starts_at__gte=now).annotate(attendee_count=Count('rsvps', filter=Q(rsvps__status=EventRSVP.Status.GOING))).order_by('starts_at')[:4]
    context = {
        'upcoming_events': upcoming_events,
        'announcements': Announcement.objects.filter(published=True).select_related('author')[:4],
        'recent_documents': Document.objects.filter(is_public=True).select_related('uploaded_by')[:4],
        'recent_notifications': request.user.notifications.all()[:5],
        'unread_count': request.user.notifications.filter(read_at__isnull=True).count(),
        'my_rsvps': EventRSVP.objects.filter(user=request.user, status=EventRSVP.Status.GOING).count(),
        'my_contributions': Contribution.objects.filter(member=request.user, status=Contribution.Status.PAID).count(),
        'album_count': GalleryAlbum.objects.count(),
    }
    return render(request, 'core/dashboard.html', context)


def public_image(request, kind, object_id):
    if kind == 'profile':
        member = get_object_or_404(User, pk=object_id)
        if not member.is_active or (not member.email_verified and not (request.user.is_authenticated and request.user.pk == member.pk)):
            raise Http404
        image = member.profile.photo
    elif kind == 'executive':
        position = get_object_or_404(ExecutiveMember.objects.select_related('user', 'user__profile'), pk=object_id, is_public=True)
        image = position.user.profile.photo
    elif kind == 'event':
        event = get_object_or_404(Event, pk=object_id)
        if event.status != Event.Status.PUBLISHED and (not request.user.is_authenticated or request.user.role not in [User.Role.SECRETARY, User.Role.PRESIDENT, User.Role.ADMIN] and not request.user.is_superuser):
            raise Http404
        image = event.image
    elif kind == 'announcement':
        announcement = get_object_or_404(Announcement, pk=object_id, published=True)
        image = announcement.image
    elif kind == 'album':
        album = get_object_or_404(GalleryAlbum, pk=object_id)
        image = album.cover
    elif kind == 'gallery':
        photo = get_object_or_404(GalleryPhoto.objects.select_related('album'), pk=object_id)
        image = photo.image
    else:
        raise Http404

    if not image:
        raise Http404
    content_type, _ = mimetypes.guess_type(image.name)
    if content_type not in {'image/jpeg', 'image/png', 'image/webp'}:
        raise Http404
    try:
        response = FileResponse(image.open('rb'), content_type=content_type)
    except (OSError, ValueError) as error:
        raise Http404 from error
    response['Cache-Control'] = 'public, max-age=3600'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
