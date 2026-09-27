import logging

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ProfileForm, RegistrationForm
from .models import ExecutiveMember, User

logger = logging.getLogger(__name__)
TOKEN_SALT = 'ceobef.accounts.email-verification'


def register(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    form = RegistrationForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save(commit=False)
            user.role = User.Role.MEMBER
            user.is_active = False
            user.email_verified = False
            user.save()
            profile = user.profile
            profile.photo = form.cleaned_data['photo']
            profile.save(update_fields=['photo'])
        token = signing.dumps(user.pk, salt=TOKEN_SALT)
        verify_url = request.build_absolute_uri(reverse('accounts:verify-email', args=[token]))
        try:
            send_mail('Confirmez votre adresse e-mail CEOBEF', f'Bonjour {user.first_name}, confirmez votre compte : {verify_url}', None, [user.email])
        except Exception:
            logger.exception('Email verification could not be sent for user %s', user.pk)
            messages.error(request, 'Le compte est créé, mais le courriel n’a pas pu être envoyé. Contactez le secrétariat.')
        else:
            messages.success(request, 'Compte créé. Consultez votre boîte e-mail pour confirmer votre adresse.')
        return redirect('accounts:login')
    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request, token):
    try:
        user_id = signing.loads(token, salt=TOKEN_SALT, max_age=60 * 60 * 24 * 3)
        user = get_object_or_404(User, pk=user_id)
    except (signing.BadSignature, signing.SignatureExpired):
        messages.error(request, 'Ce lien de vérification est invalide ou a expiré.')
        return redirect('accounts:login')
    user.email_verified = True
    user.is_active = True
    user.save(update_fields=['email_verified', 'is_active'])
    messages.success(request, 'Votre adresse e-mail est confirmée. Vous pouvez vous connecter.')
    return redirect('accounts:login')


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user.profile, user=request.user)
    if request.method == 'POST' and form.is_valid():
        previous_email = request.user.email
        form.save()
        if request.user.email != previous_email:
            request.user.email_verified = False
            request.user.is_active = False
            request.user.save(update_fields=['email_verified', 'is_active'])
            token = signing.dumps(request.user.pk, salt=TOKEN_SALT)
            verify_url = request.build_absolute_uri(reverse('accounts:verify-email', args=[token]))
            try:
                send_mail('Confirmez votre nouvelle adresse e-mail CEOBEF', f'Confirmez votre nouvelle adresse : {verify_url}', None, [request.user.email])
            except Exception:
                logger.exception('Email verification could not be sent for user %s', request.user.pk)
                messages.error(request, 'Votre adresse a changé, mais le courriel de vérification n’a pas pu être envoyé. Contactez le secrétariat.')
            else:
                messages.success(request, 'Confirmez votre nouvelle adresse e-mail. Votre compte sera réactivé après vérification.')
            logout(request)
            return redirect('accounts:login')
        messages.success(request, 'Votre profil a été mis à jour.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})


def executive(request):
    members = ExecutiveMember.objects.filter(is_public=True).select_related('user', 'user__profile')
    return render(request, 'accounts/executive.html', {'members': members})
