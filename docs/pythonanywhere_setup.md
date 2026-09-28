# PythonAnywhere Free : guide court

## Limites à accepter

- L’application est publiée par WSGI ; PythonAnywhere Free ne prend pas en charge le WebSocket Channels. Les pages HTTP restent disponibles, mais chat temps réel, saisie, présence et notifications instantanées ne fonctionnent pas.
- Un compte Free a une application Web, un worker, 100 secondes CPU, 512 MiB de disque et une expiration après un mois.
- Les nouveaux comptes Free depuis le 15 janvier 2026 (8 janvier dans le système UE) n’ont pas la base MySQL gratuite. Le guide utilise SQLite dans le répertoire du projet, persistant sur le home mais adapté seulement à une petite démo.
- La disponibilité SMTP externe est soumise à la liste des domaines autorisés PythonAnywhere. Gmail SMTP peut être bloqué par la politique réseau Free. Tester avant d’ouvrir les inscriptions ; un autre relais ou une offre qui permet l’accès réseau est nécessaire si l’envoi échoue.
- Le projet demande Python 3.12 minimum à cause de Django 6. Choisir une version disponible dans l’onglet Web qui satisfait ce minimum. Si le compte ne propose pas Python 3.12+, le projet n’est pas installable en conservant les dépendances et le comportement présents.

## Création du site

1. Créer/ouvrir un compte PythonAnywhere, puis l’onglet **Consoles > Bash**.
2. Vérifier les versions Python installées avec `ls -1 /usr/bin/python3.*`. Sélectionner Python 3.12 ou plus récent disponible pour l’application Web.
3. Cloner le dépôt et installer l’environnement (adapter l’exécutable à la version choisie) :

```bash
git clone https://github.com/anselmemasiala31-afk/CEOBEF.git
cd CEOBEF
mkvirtualenv --python=/usr/bin/python3.13 ceobef-venv
workon ceobef-venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Le nom `python3.13` est un exemple : remplacez-le par l’exécutable ≥3.12 réellement présent dans votre compte. Si le dépôt est privé, utilisez la configuration GitHub déjà autorisée dans PythonAnywhere ; ne mettez jamais un token dans la commande `git clone`.

4. Créer le fichier secret local, ignoré par Git :

```bash
umask 077
touch .env
nano .env
chmod 600 .env
```

Contenu à adapter. Générer une clé unique ; ne pas reprendre le texte d’exemple comme clé réelle :

```dotenv
PYTHONANYWHERE=true
SECRET_KEY=REMPLACER_PAR_UNE_CLE_ALEATOIRE_LONGUE
DEBUG=False
ALLOWED_HOSTS=VOTRE_NOM.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://VOTRE_NOM.pythonanywhere.com
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_TRUST_PROXY_SSL=true
SECURE_HSTS_SECONDS=31536000
CHANNEL_LAYER=memory
SQLITE_PATH=/home/VOTRE_NOM/CEOBEF/db.sqlite3
STATIC_ROOT=/home/VOTRE_NOM/CEOBEF/staticfiles
MEDIA_ROOT=/home/VOTRE_NOM/CEOBEF/private-media
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=ADRESSE_ORGANISATION_GMAIL
EMAIL_HOST_PASSWORD=MOT_DE_PASSE_APPLICATION_GOOGLE
DEFAULT_FROM_EMAIL="CEOBEF <ADRESSE_ORGANISATION_GMAIL>"
```

Remplacer `VOTRE_NOM` et les valeurs de messagerie. Si PythonAnywhere n’autorise pas l’accès SMTP vers Gmail, ne remplacez pas l’erreur par le backend console en production : l’e-mail de vérification ne serait pas délivré. Choisir alors un relais autorisé et adapté ou un plan qui permet Gmail SMTP.

5. Vérifier la configuration, préparer la base persistante et les assets :

```bash
cd /home/VOTRE_NOM/CEOBEF
workon ceobef-venv
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python scripts/pythonanywhere_smoke_test.py
```

`makemigrations --check --dry-run` doit répondre `No changes detected`. Ne lancez pas `makemigrations` sans `--check` sur la production : les migrations appartiennent au dépôt et se génèrent localement avec revue/tests.

## Web tab

6. Dans **Web > Add a new web app**, sélectionner le domaine `VOTRE_NOM.pythonanywhere.com` puis **Manual configuration** (ne pas utiliser le générateur Django intégré). Choisir exactement la même version Python que la virtualenv.
7. Dans **Virtualenv**, saisir `/home/VOTRE_NOM/.virtualenvs/ceobef-venv`.
8. Dans **Code > Working directory**, saisir `/home/VOTRE_NOM/CEOBEF`.
9. Ouvrir le fichier WSGI indiqué dans l’onglet Web et remplacer tout son contenu par celui de [`deployment/pythonanywhere_wsgi.py`](../deployment/pythonanywhere_wsgi.py), après avoir remplacé le nom d’utilisateur dans `PROJECT_HOME`.
10. Dans **Static files**, ajouter uniquement :

| URL | Répertoire |
| --- | --- |
| `/static/` | `/home/VOTRE_NOM/CEOBEF/staticfiles` |

Ne pas ajouter de mapping `/media/`. Les vues de CEOBEF livrent images publiques via contrôle applicatif et gardent documents, reçus et pièces jointes derrière autorisation. Mapping direct de `private-media/` = divulgation de données.

11. Cliquer **Reload**, ouvrir `https://VOTRE_NOM.pythonanywhere.com` et vérifier les logs d’erreur accessibles dans l’onglet Web.

## Après une mise à jour

Dans la console Bash :

```bash
cd /home/VOTRE_NOM/CEOBEF
git pull origin main
workon ceobef-venv
python -m pip install -r requirements.txt
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
python scripts/pythonanywhere_smoke_test.py
```

Puis cliquer **Reload** dans l’onglet Web. L’application Free peut expirer après un mois ; les bases, fichiers téléchargés et paramètres du compte doivent être sauvegardés/exportés avant suppression ou renouvellement.
