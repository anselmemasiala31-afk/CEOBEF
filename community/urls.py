from django.urls import path

from . import views

app_name = 'community'

urlpatterns = [
    path('actualites/', views.announcement_list, name='announcements'),
    path('actualites/creer/', views.announcement_create, name='announcement-create'),
    path('actualites/<int:announcement_id>/commenter/', views.add_comment, name='comment'),
    path('galerie/', views.gallery, name='gallery'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/lues/', views.mark_notifications_read, name='mark-read'),
]