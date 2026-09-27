def ceobef_notifications(request):
    if request.user.is_authenticated:
        return {'ceobef_unread_notifications': request.user.notifications.filter(read_at__isnull=True).count()}
    return {'ceobef_unread_notifications': 0}