#!/usr/bin/env python3
"""Read-only Django smoke checks for a deployed CEOBEF WSGI site."""

import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import connection
from django.test import Client
from django.urls import reverse


results = []


def record(status, label, detail):
    results.append((status, label, detail))


def check_route(client, label, url, expected):
    try:
        response = client.get(url, follow=False, secure=settings.PYTHONANYWHERE)
        if response.status_code in expected:
            record('OK', label, f'HTTP {response.status_code}')
        else:
            record('ERROR', label, f'HTTP {response.status_code}; expected {sorted(expected)}')
    except Exception as error:
        record('ERROR', label, f'{type(error).__name__}: {error}')


smoke_host = os.getenv('CEOBEF_SMOKE_HOST', '')
if not smoke_host:
    smoke_host = next((host.lstrip('.') for host in settings.ALLOWED_HOSTS if host != '*'), 'localhost')
client = Client(HTTP_HOST=smoke_host)
public_routes = (
    ('Accueil', reverse('core:home')),
    ('Connexion', reverse('accounts:login')),
    ('Inscription', reverse('accounts:register')),
    ('Galerie', reverse('community:gallery')),
    ('Événements', reverse('events:list')),
    ('Actualités', reverse('community:announcements')),
    ('Bureau exécutif', reverse('accounts:executive')),
)
for label, url in public_routes:
    check_route(client, label, url, {200})

check_route(client, 'Bibliothèque sans session', reverse('library:list'), {301, 302})
check_route(client, 'Notifications sans session', reverse('community:notifications'), {301, 302})
check_route(client, 'Administration sans session', reverse('admin:index'), {301, 302})

try:
    static_url = staticfiles_storage.url('css/site.css')
    response = client.get(static_url, secure=settings.PYTHONANYWHERE)
    if response.status_code == 200:
        record('OK', 'CSS collecté via WhiteNoise', f'{static_url} -> HTTP 200')
    else:
        record('ERROR', 'CSS collecté via WhiteNoise', f'{static_url} -> HTTP {response.status_code}')
except Exception as error:
    record('ERROR', 'CSS collecté via WhiteNoise', f'{type(error).__name__}: {error}')

try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
    record('OK', 'Connexion à la base', settings.DATABASES['default']['ENGINE'])
except Exception as error:
    record('ERROR', 'Connexion à la base', f'{type(error).__name__}: {error}')

username = os.getenv('CEOBEF_SMOKE_USERNAME', '')
password = os.getenv('CEOBEF_SMOKE_PASSWORD', '')
if username and password:
    try:
        if client.login(username=username, password=password):
            for label, route_name in (
                ('Tableau de bord', 'core:dashboard'),
                ('Documents', 'library:list'),
                ('Cotisations', 'finance:list'),
                ('Messagerie HTTP', 'messaging:list'),
                ('Notifications membre', 'community:notifications'),
            ):
                check_route(client, label, reverse(route_name), {200})
            member = get_user_model().objects.get(username=username)
            if member.is_staff:
                check_route(client, 'Administration authentifiée', reverse('admin:index'), {200})
            else:
                record('WARNING', 'Administration authentifiée', 'Le compte de test n’a pas le rôle staff.')
        else:
            record('ERROR', 'Connexion avec le compte de test', 'Échec de connexion ; identifiants non affichés.')
    except Exception as error:
        record('ERROR', 'Vérifications authentifiées', f'{type(error).__name__}: {error}')
else:
    record('WARNING', 'Pages protégées', 'Définir temporairement CEOBEF_SMOKE_USERNAME et CEOBEF_SMOKE_PASSWORD pour tester la session membre. Les valeurs ne sont jamais affichées.')

if settings.PYTHONANYWHERE:
    record('WARNING', 'WebSockets Channels', 'PythonAnywhere Free WSGI ne relaie pas les WebSockets ; le chat temps réel et les notifications WebSocket ne sont pas testables sur cette offre.')
else:
    record('WARNING', 'Profil PythonAnywhere', 'Lancer ce script dans l’environnement PythonAnywhere avec PYTHONANYWHERE=true pour valider ce profil.')

record('WARNING', 'Médias privés', 'Les uploads sont servis par les vues d’autorisation ; ne pas ajouter de mapping /media/ statique.')

base_url = os.getenv('CEOBEF_SMOKE_BASE_URL', '').rstrip('/')
if base_url:
    live_routes = (
        ('Accueil HTTP public', '/', {200}),
        ('Connexion HTTP publique', '/compte/connexion/', {200}),
        ('Inscription HTTP publique', '/compte/inscription/', {200}),
        ('Galerie HTTP publique', '/galerie/', {200}),
        ('Événements HTTP publics', '/evenements/', {200}),
        ('Documents HTTP protégés', '/documents/', {200, 301, 302}),
        ('Notifications HTTP protégées', '/notifications/', {200, 301, 302}),
        ('Administration HTTP', '/admin/', {200, 301, 302}),
    )
    for label, path, expected in live_routes:
        try:
            request = Request(f'{base_url}{path}', headers={'User-Agent': 'CEOBEF deployment smoke test'})
            with urlopen(request, timeout=20) as response:
                code = response.status
            status = 'OK' if code in expected else 'ERROR'
            record(status, label, f'{base_url}{path} -> HTTP {code}')
        except HTTPError as error:
            status = 'OK' if error.code in expected else 'ERROR'
            record(status, label, f'{base_url}{path} -> HTTP {error.code}')
        except (URLError, TimeoutError, OSError) as error:
            record('ERROR', label, f'{base_url}{path} -> {type(error).__name__}: {error}')

    try:
        static_url = staticfiles_storage.url('css/site.css')
        with urlopen(Request(f'{base_url}{static_url}', headers={'User-Agent': 'CEOBEF deployment smoke test'}), timeout=20) as response:
            code = response.status
        record('OK' if code == 200 else 'ERROR', 'CSS HTTP public', f'{base_url}{static_url} -> HTTP {code}')
    except HTTPError as error:
        record('ERROR', 'CSS HTTP public', f'{base_url}{static_url} -> HTTP {error.code}')
    except (URLError, TimeoutError, OSError) as error:
        record('ERROR', 'CSS HTTP public', f'{base_url}{static_url} -> {type(error).__name__}: {error}')
else:
    record('WARNING', 'Site HTTP public', 'Définir CEOBEF_SMOKE_BASE_URL=https://VOTRE_NOM.pythonanywhere.com pour tester le serveur public en plus du client Django local.')

for status, label, detail in results:
    print(f'{status:7} {label}: {detail}')

ok_count = sum(status == 'OK' for status, _, _ in results)
errors = sum(status == 'ERROR' for status, _, _ in results)
warning_count = sum(status == 'WARNING' for status, _, _ in results)
print(f'\nRésumé : {ok_count} OK, {errors} ERROR, {warning_count} AVERTISSEMENT.')
sys.exit(1 if errors else 0)
