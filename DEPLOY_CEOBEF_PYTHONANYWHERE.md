# DEPLOY CEOBEF PYTHONANYWHERE

## Verdict and important constraints

**The CEOBEF HTTP/WSGI site is prepared for PythonAnywhere. This is not a full-feature-equivalent deployment of the local ASGI application.** PythonAnywhere Web apps use WSGI; its Free plan does not provide the WebSocket transport used by Django Channels. Chat delivery, typing, online presence and instant notification sockets therefore cannot work there without moving to an ASGI host. The web interface and ordinary Django HTTP views can run, but the live chat feature is unavailable on this host. No business code has been changed to hide this limitation.

PythonAnywhere's current Free-account documentation lists one web app/worker, a one-month expiry, 100 CPU seconds and 512 MiB storage. New Free accounts created on/after 15 January 2026 (8 January for the EU system) do not include MySQL. A small SQLite file in the account's home directory is used here. The app's images, documents and private media also occupy that limited quota. This is a temporary demonstration environment, not a suitable home for student records or financial receipts.

The runtime must be Python 3.12 or later because the repository requires Django 6. Check the Python versions offered for the account's selected system image in its Account/Web tabs. If no supported version >=3.12 is available, stop: deploying this requirements set requires a newer PythonAnywhere runtime or a reviewed Django compatibility change.

PythonAnywhere restricts outbound Internet access on Free accounts. Gmail SMTP on port 587 may not be reachable. If SMTP cannot connect from a PythonAnywhere console, signup verification, password reset and email notifications will not be delivered; no setting can bypass a network egress restriction. Test it before inviting users. Do not put a Google account password here: only use an app password, or a mail relay allowed by the host.

## Audit report

| Area | Result | Finding |
| --- | --- | --- |
| Django structure | OK | Project `config`; apps: accounts, community, core, events, finance, library, messaging. |
| Templates | OK | 29 Django templates found, including base, account, dashboard, event, gallery, library, finance and messaging views. |
| Static assets | OK | Three source files: `static/css/site.css`, `static/js/site.js`, `static/js/chat.js`; WhiteNoise configured and `STATIC_ROOT` is set. |
| Migrations | OK | Seven app migration packages; library has two migrations, six apps have one each, core has no models/migration. |
| WSGI | OK | `config/wsgi.py` exposes the standard Django application. PythonAnywhere needs its own Web-tab WSGI file; a ready template is included. |
| ASGI / Channels | WARNING | `config/asgi.py` and authenticated Consumers are present; PythonAnywhere Free WSGI cannot run them as WebSockets. |
| Database | WARNING | Current Render/PostgreSQL settings are retained. The `PYTHONANYWHERE=true` profile permits SQLite at a home-directory path. Free SQLite is limited by the account's disk and is not a multi-worker production database. |
| Static files | OK | Use `/static/` mapped to the absolute collected directory in the Web tab. |
| Private media | WARNING | 23 files exist locally under `private-media/`; they are git-ignored. They are not copied by Git, and must not be exposed as a static mapping. |
| SMTP | WARNING | Gmail values are environment-only; successful delivery depends on PythonAnywhere Free outbound access. |
| Dependencies | OK | `requirements.txt` includes Django 6, Daphne, Channels, channels-redis, Pillow, WhiteNoise, psycopg and python-dotenv. No dependency change was needed. |

## Files prepared

- `config/settings.py`: PythonAnywhere-specific allowance for home-directory SQLite and in-memory Channels; explicit slash-rooted static/media URLs and environment-overridable storage paths. Other deployment profiles retain their PostgreSQL/Redis/SMTP checks.
- `.env.example`: local defaults plus commented PythonAnywhere variables. It contains no real credentials.
- `deployment/pythonanywhere_wsgi.py`: complete WSGI content to copy to the WSGI file shown in the PythonAnywhere Web tab.
- `scripts/pythonanywhere_smoke_test.py`: safe HTTP/render/static/database smoke checks; optional authenticated checks use environment variables and never print the password.
- `docs/deployment.md` and `docs/pythonanywhere_setup.md`: short deployment guides and platform caveats.
- `DEPLOY_CEOBEF_PYTHONANYWHERE.md`: this audit and copy-ready handoff.
- `requirements.txt`: unchanged; dependencies already cover CEOBEF. Daphne/Channels are not a way to add WebSockets to PythonAnywhere's WSGI plan.

## Account setup and Bash commands

Replace `YOUR_NOM` below with the PythonAnywhere username. Choose an installed Python executable >=3.12 in the Web tab; `python3.13` is an example and may differ by account/system image.

```bash
# In a PythonAnywhere Bash console
ls -1 /usr/bin/python3.*
git clone https://github.com/anselmemasiala31-afk/CEOBEF.git
cd CEOBEF
mkvirtualenv --python=/usr/bin/python3.13 ceobef-venv
workon ceobef-venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the repository is private, authenticate to GitHub using a configured SSH key or PythonAnywhere's supported Git connection. Never put a GitHub token in the clone URL.

Create the untracked environment file with restrictive permissions:

```bash
cd /home/YOUR_NOM/CEOBEF
umask 077
touch .env
nano .env
chmod 600 .env
```

Paste and edit this template. Generate a fresh random key locally; never commit `.env`:

```dotenv
PYTHONANYWHERE=true
SECRET_KEY=PASTE_A_UNIQUE_RANDOM_DJANGO_SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=YOUR_NOM.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://YOUR_NOM.pythonanywhere.com
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_TRUST_PROXY_SSL=true
SECURE_HSTS_SECONDS=31536000
CHANNEL_LAYER=memory
SQLITE_PATH=/home/YOUR_NOM/CEOBEF/db.sqlite3
STATIC_ROOT=/home/YOUR_NOM/CEOBEF/staticfiles
MEDIA_ROOT=/home/YOUR_NOM/CEOBEF/private-media
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=YOUR_ORGANISATION_GMAIL
EMAIL_HOST_PASSWORD=YOUR_GOOGLE_APP_PASSWORD
DEFAULT_FROM_EMAIL="CEOBEF <YOUR_ORGANISATION_GMAIL>"
```

Generate a Django key in the console, then paste it into `.env` without sharing it:

```bash
workon ceobef-venv
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

The WSGI settings load this `.env` before Django starts. For SMTP, turn on Google 2-Step Verification and create a Google **App Password**. Do not use the main Google password. The Free plan may block Gmail's SMTP endpoint; a successful configuration is not evidence of network reachability.

Apply schema and collect assets:

```bash
cd /home/YOUR_NOM/CEOBEF
workon ceobef-venv
set -a
source .env
set +a
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python scripts/pythonanywhere_smoke_test.py
```

`makemigrations --check --dry-run` should report `No changes detected`. Do not run unreviewed production `makemigrations`; create and test migrations in development, commit them, then apply with `migrate`.

## Web tab configuration

1. **Web > Add a new web app**. Pick `YOUR_NOM.pythonanywhere.com`, then choose **Manual configuration** and the same Python version as `ceobef-venv`.
2. Set **Source code** and **Working directory** to `/home/YOUR_NOM/CEOBEF`.
3. Set **Virtualenv** to `/home/YOUR_NOM/.virtualenvs/ceobef-venv`.
4. Open the WSGI configuration link in the Web tab. Replace its contents with [`deployment/pythonanywhere_wsgi.py`](deployment/pythonanywhere_wsgi.py) and change the single `PROJECT_HOME` line from `/home/YOUR_PYTHONANYWHERE_USERNAME/CEOBEF` to `/home/YOUR_NOM/CEOBEF`. Do not put secrets in this file.
5. In **Static files**, add this mapping:

| URL | Directory |
| --- | --- |
| `/static/` | `/home/YOUR_NOM/CEOBEF/staticfiles` |

6. Do **not** add `/media/` -> `private-media/` or any other public media mapping. CEOBEF's documents, receipts and chat attachments are private and must continue through their authorization views. The Web-tab static server bypasses Django permissions.
7. Click **Reload** and open `https://YOUR_NOM.pythonanywhere.com/`. Inspect the error log in the Web tab if it does not return HTTP 200.

`STATIC_ROOT` and `MEDIA_ROOT` can be overridden in `.env` as above. The effective local/static file paths are:

| URL | Directory | Mapping |
| --- | --- | --- |
| `/static/` | `/home/YOUR_NOM/CEOBEF/staticfiles` | Configure in Web tab |
| `/media/` | `/home/YOUR_NOM/CEOBEF/private-media` | **No public mapping; protected views only** |

## Environment variables

All values below live in the untracked `/home/YOUR_NOM/CEOBEF/.env` file. Replace placeholders and never commit the file.

| Name | Purpose |
| --- | --- |
| `PYTHONANYWHERE` | Enables the platform-specific SQLite/WSGI deployment profile (`true`). |
| `SECRET_KEY` | Unique random Django secret; keep private. |
| `DEBUG` | `False`. |
| `ALLOWED_HOSTS` | Exact `YOUR_NOM.pythonanywhere.com` host. |
| `CSRF_TRUSTED_ORIGINS` | Exact HTTPS origin `https://YOUR_NOM.pythonanywhere.com`. |
| `DJANGO_SECURE_SSL_REDIRECT` | `true`. |
| `DJANGO_TRUST_PROXY_SSL` | `true`, for PythonAnywhere's TLS-terminating proxy. |
| `SECURE_HSTS_SECONDS` | Start at `0` during first HTTPS verification; only increase after confirming HTTPS. The example uses one year. |
| `SQLITE_PATH` | Persistent SQLite file under the home directory. |
| `STATIC_ROOT` | Absolute directory populated by `collectstatic`. |
| `MEDIA_ROOT` | Private upload directory in the home directory. |
| `CHANNEL_LAYER` | `memory`; WSGI still cannot provide WebSocket delivery. |
| `EMAIL_BACKEND` | Django SMTP backend. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS` | Gmail SMTP host, 587 and TLS. |
| `EMAIL_HOST_USER` | Organization Gmail address. |
| `EMAIL_HOST_PASSWORD` | Google App Password, not account password. |
| `DEFAULT_FROM_EMAIL` | CEOBEF sender address. |

No `DATABASE_URL` or Redis server is provisioned for this Free WSGI deployment. The app uses SQLite and an in-process channel layer. `.env` is excluded by `.gitignore`.

## Smoke checks and expected report

Run `python scripts/pythonanywhere_smoke_test.py` from the activated virtualenv after migrations/collectstatic. It reports `OK`, `ERROR`, or `WARNING` for homepage, login, registration, gallery, events, public/protected routes, admin redirect, static delivery, database, and the known WSGI/media limitations.

After creating the web app and reloading it, also make live HTTPS requests to the public site:

```bash
CEOBEF_SMOKE_BASE_URL=https://YOUR_NOM.pythonanywhere.com python scripts/pythonanywhere_smoke_test.py
```

If PythonAnywhere Free blocks an outbound request back to its own public hostname, run the default in-process Django checks and verify the public URLs from a browser instead.

To include member-only routes, set temporary console variables before running it (never put a real password in a shell history file):

```bash
read -r -p 'CEOBEF test username: ' CEOBEF_SMOKE_USERNAME
read -r -s -p 'CEOBEF test password: ' CEOBEF_SMOKE_PASSWORD; echo
export CEOBEF_SMOKE_USERNAME CEOBEF_SMOKE_PASSWORD
python scripts/pythonanywhere_smoke_test.py
unset CEOBEF_SMOKE_USERNAME CEOBEF_SMOKE_PASSWORD
```

Public URL checks after reload:

```text
https://YOUR_NOM.pythonanywhere.com/
https://YOUR_NOM.pythonanywhere.com/compte/connexion/
https://YOUR_NOM.pythonanywhere.com/compte/inscription/
https://YOUR_NOM.pythonanywhere.com/galerie/
https://YOUR_NOM.pythonanywhere.com/evenements/
https://YOUR_NOM.pythonanywhere.com/admin/
https://YOUR_NOM.pythonanywhere.com/static/css/site.css
```

Protected documents and notifications should redirect anonymous users to login. Do not test private files by mapping their storage directory as static content.

## Updating after a Git push

```bash
cd /home/YOUR_NOM/CEOBEF
git pull --ff-only origin main
workon ceobef-venv
python -m pip install -r requirements.txt
set -a
source .env
set +a
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
python scripts/pythonanywhere_smoke_test.py
```

Then click **Reload** in the PythonAnywhere Web tab. Check the website error log and server log. Keep a separate database/media backup before updates; do not assume Free accounts provide durable backups.
