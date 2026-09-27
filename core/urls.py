from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('espace/', views.dashboard, name='dashboard'),
    path('visuels/<str:kind>/<int:object_id>/', views.public_image, name='public-image'),
]