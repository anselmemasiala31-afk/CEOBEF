from django.urls import path

from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.contribution_list, name='list'),
    path('enregistrer/', views.contribution_record, name='record'),
    path('<int:pk>/justificatif/', views.download_receipt, name='receipt'),
]