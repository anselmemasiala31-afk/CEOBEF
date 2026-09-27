from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('inscription/', views.register, name='register'),
    path('verification/<str:token>/', views.verify_email, name='verify-email'),
    path('connexion/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='logout'),
    path('mot-de-passe/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html', success_url='/compte/mot-de-passe/modifie/'), name='password-change'),
    path('mot-de-passe/modifie/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password-change-done'),
    path('mot-de-passe/oublie/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html', email_template_name='accounts/password_reset_email.txt', subject_template_name='accounts/password_reset_subject.txt'), name='password-reset'),
    path('mot-de-passe/envoye/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password-reset-done'),
    path('mot-de-passe/reinitialiser/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password-reset-confirm'),
    path('mot-de-passe/reinitialise/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password-reset-complete'),
    path('profil/', views.profile, name='profile'),
    path('bureau/', views.executive, name='executive'),
]