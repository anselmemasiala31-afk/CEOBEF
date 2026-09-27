from django.urls import path

from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.conversation_list, name='list'),
    path('groupes/creer/', views.create_group, name='create-group'),
    path('demarrer/<int:user_id>/', views.start_direct, name='start-direct'),
    path('<int:conversation_id>/fichier/<int:message_id>/', views.download_attachment, name='download-attachment'),
    path('<int:pk>/', views.conversation_detail, name='detail'),
    path('<int:pk>/piece-jointe/', views.upload_attachment, name='upload-attachment'),
]