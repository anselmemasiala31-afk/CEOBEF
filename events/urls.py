from django.urls import path

from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='list'),
    path('creer/', views.event_create, name='create'),
    path('<slug:slug>/', views.event_detail, name='detail'),
    path('<slug:slug>/participer/', views.rsvp, name='rsvp'),
]