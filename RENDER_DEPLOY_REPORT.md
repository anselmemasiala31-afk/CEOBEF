# CEOBEF — Rapport de préparation Render

Date : 28 septembre 2026  
Branche : `main`  
Commit de base : `5eced11` — `Prepare CEOBEF for PythonAnywhere deployment`

## Résumé

CEOBEF est préparé pour l'application d'un Blueprint Render : le fichier `render.yaml` définit un web service Python/Daphne, PostgreSQL et Key Value/Redis, le site lit les variables Render `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, et les contrôles de production ont été exercés localement avec des valeurs factices non secrètes.

Le déploiement Render réel n'a pas été appliqué depuis ce dépôt pendant cet audit. L'URL publique, la connexion PostgreSQL distante, le handshake WebSocket distant et la livraison Gmail ne peuvent donc pas être certifiés sans exécuter le Blueprint dans le tableau de bord Render et disposer de ses secrets.

Le Blueprint gratuit est un environnement de démonstration, pas une cible 100 % fonctionnelle/durable pour la production : PostgreSQL gratuit expire au bout de 30 jours; les uploads vivent sur un système de fichiers éphémère; Render Free bloque le SMTP sortant sur 25/465/587, dont Gmail 587. Les e-mails d'inscription/récupération et la conservation des médias ne sont donc pas garantis sur ce plan.

## Audit de préparation

- `requirements.txt` comprend Django 6, Daphne, Channels, channels-redis, Pillow, WhiteNoise, psycopg et python-dotenv.
- `manage.py` est standard et opérationnel.
- `config/wsgi.py` et `config/asgi.py` exposent respectivement WSGI HTTP et ASGI HTTP/WebSocket.
- `STATIC_URL=/static/`, `STATIC_ROOT`, `STORAGES` WhiteNoise et middleware WhiteNoise sont configurés.
- `MEDIA_ROOT` vise `private-media/`; téléchargements de documents, reçus et pièces jointes passent par les contrôles applicatifs.
- `DATABASE_URL` configure PostgreSQL en production; aucun identifiant n'est codé en dur.
- `.env.example` n'inclut aucune valeur secrète réelle.
- `render.yaml` lance `collectstatic`, applique les migrations avant Daphne et lie PostgreSQL/Key Value.
- Les fichiers des utilisateurs présents sous `private-media/` ne sont pas suivis par Git.

## Problèmes corrigés/préparés

- Ajout d'un profil `PYTHONANYWHERE` sans altérer le profil Render ou local; ce point est documenté à titre de préparation WSGI séparée, pas utilisé par Render.
- SQLite peut résider sous le home via `SQLITE_PATH` si l'équipe choisit un hébergement WSGI limité, tout en conservant PostgreSQL obligatoire pour Render lorsque `PYTHONANYWHERE` est faux.
- `STATIC_URL`/`MEDIA_URL` sont des chemins absolus et `STATIC_ROOT`/`MEDIA_ROOT` sont configurables par environnement.
- Ajout d'un WSGI PythonAnywhere prêt à adapter et d'un smoke-test HTTP/WhiteNoise avec sorties `OK`, `ERROR`, `WARNING`.
- Documentation des limites de médias privés et absence de mapping public `/media/`.

Les modifications récentes dans `events/views.py`, `finance/views.py` et `messaging/views.py` ne suppriment que des imports inutilisés; aucune logique métier n'a été modifiée.

## Fichiers modifiés / ajoutés dans cette préparation

- `.env.example`
- `README.md`
- `config/settings.py`
- `DEPLOY_CEOBEF_PYTHONANYWHERE.md`
- `deployment/pythonanywhere_wsgi.py`
- `docs/deployment.md`
- `docs/pythonanywhere_setup.md`
- `AUDIT_REPORT.md`
- `RENDER_DEPLOY_REPORT.md`
- `scripts/pythonanywhere_smoke_test.py`
- `events/views.py`, `finance/views.py`, `messaging/views.py` : suppression d'importations inutilisées déjà présente dans le working tree; aucun comportement métier changé.
- `requirements.txt` n'a pas été modifié, car toutes les dépendances requises y sont déjà déclarées.

## Variables Render

À configurer/réviser sur le web service Render créé par le Blueprint :

| Variable | Valeur/source |
| --- | --- |
| `PYTHON_VERSION` | `3.14.3` |
| `SECRET_KEY` | Générée par Render (`generateValue`) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com,localhost,127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` |
| `DATABASE_URL` | Référence privée à la base Blueprint |
| `REDIS_URL` | Référence au Key Value Blueprint |
| `DB_SSLMODE` | `require` |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` |
| `DJANGO_TRUST_PROXY_SSL` | `true` |
| `SECURE_HSTS_SECONDS` | `31536000` |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | `smtp.gmail.com` |
| `EMAIL_PORT` | `587` |
| `EMAIL_USE_TLS` | `true` |
| `EMAIL_HOST_USER` | Gmail organisationnel, secret Render |
| `EMAIL_HOST_PASSWORD` | Mot de passe d'application Gmail, secret Render |
| `DEFAULT_FROM_EMAIL` | Adresse CEOBEF, secret/config Render |
| `DJANGO_SUPERUSER_USERNAME` | Secret initial, supprimer après création |
| `DJANGO_SUPERUSER_EMAIL` | Adresse initiale, supprimer après création |
| `DJANGO_SUPERUSER_PASSWORD` | Secret initial long, supprimer après création |

Le nom d'utilisateur et le mot de passe de l'administrateur sont utilisés par `bootstrap_render_admin`, ne sont pas inclus dans Git et ne doivent pas être partagés avec l'assistant.

## Commandes de déploiement Blueprint

Build :

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

Démarrage :

```bash
python manage.py migrate --noinput && daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

Hook initial :

```bash
python manage.py bootstrap_render_admin
```

## Contrôles exécutés

- `python manage.py check` : aucune anomalie.
- `python manage.py check --deploy` avec les noms/valeurs de configuration Render fictifs en environnement temporaire : aucune anomalie.
- `python manage.py makemigrations --check --dry-run` : `No changes detected`.
- `python manage.py migrate --noinput` : réussi, aucune migration en attente.
- `python manage.py collectstatic --noinput` : réussi.
- `python manage.py test --verbosity 1` : 20 tests réussis.
- `python scripts/pythonanywhere_smoke_test.py` : 12 `OK`, 0 `ERROR`; avertissements explicites pour tests authentifiés/live et contraintes de médias/WebSockets.
- Parse `render.yaml` : ressources web, keyvalue, PostgreSQL et références attendues présentes.
- Diagnostics éditeur sur settings/WSGI/smoke-test : aucun.

## Étapes manuelles restantes

1. Connecter/appliquer `render.yaml` dans Render **New > Blueprint**.
2. Fournir les secrets requis dans le tableau Render; ne jamais les ajouter au dépôt.
3. Surveiller build/migrations, récupérer l'URL `.onrender.com`, vérifier la page, les statiques et les sockets pendant que l'instance est éveillée.
4. Tester Gmail seulement avec un service/réseau autorisant SMTP : le port 587 est bloqué sur le service Web Free.
5. Avant toute donnée réelle, choisir une base sauvegardée et une persistance privée pour les médias; le plan Free actuel n'en fournit pas.

## Commandes Git

La préparation sera ajoutée et poussée après vérification finale :

```bash
git status
git add .env.example README.md config/settings.py DEPLOY_CEOBEF_PYTHONANYWHERE.md deployment/pythonanywhere_wsgi.py docs/deployment.md docs/pythonanywhere_setup.md scripts/pythonanywhere_smoke_test.py
git commit -m "Audit CEOBEF and prepare Render deployment"
git push origin main
```

Avant le push, vérifier `git status --short --branch` pour conserver toutes les modifications utilisateur et confirmer que `.env`, `private-media/`, `db.sqlite3`, `.venv`, `__pycache__` et `staticfiles/` ne sont pas suivis.
