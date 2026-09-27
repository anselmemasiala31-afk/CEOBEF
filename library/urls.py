from django.urls import path

from . import views

app_name = 'library'

urlpatterns = [
    path('', views.document_list, name='list'),
    path('ajouter/', views.document_upload, name='upload'),
    path('<int:pk>/telecharger/', views.document_download, name='download'),
]