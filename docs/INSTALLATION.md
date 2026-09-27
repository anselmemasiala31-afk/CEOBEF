# Installation et exploitation

## Prérequis

- Python 3.14 (Django 6.0) et PowerShell sous Windows pour le développement.
- PostgreSQL 15+ en production.
- Redis 7+ pour la messagerie et les notifications WebSocket multi-workers.
- Un compte Gmail organisationnel avec validation en deux étapes et mot de passe d’application.

## Environnement local

Depuis la racine `CEOBEF` :

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Si PowerShell bloque l’activation de l’environnement, utilisez directement `\.venv\Scripts\python.exe` pour chaque commande. Le backend e-mail console affiche les liens de validation dans le terminal. Le canal Channels mémoire convient au développement avec un seul processus.

## Configuration VS Code

1. Ouvrir le dossier racine `CEOBEF` dans VS Code.
2. Installer l’extension Microsoft Python si elle n’est pas présente.
3. Exécuter `Python: Select Interpreter`, puis choisir `.venv\Scripts\python.exe`.
4. Ouvrir le terminal intégré et exécuter les commandes de migration ci-dessus.
5. Pour lancer le serveur, utiliser `python manage.py runserver`. Pour lancer les tests, utiliser `python manage.py test`.

Les fichiers `.env`, SQLite, médias téléversés et environnement virtuel sont ignorés par Git.

## Variables d’environnement

Copier `.env.example` vers `.env`. Ne jamais ajouter `.env` à un dépôt ou exposer un mot de passe d’application dans les logs.

- `DJANGO_SECRET_KEY` : valeur aléatoire unique, secrète et persistante pour l’environnement.
- `DJANGO_DEBUG` : `false` en production.
- `DJANGO_ALLOWED_HOSTS` : noms d’hôte séparés par des virgules, sans schéma.
- `CSRF_TRUSTED_ORIGINS` : origines HTTPS complètes séparées par des virgules.
- `DJANGO_SECURE_SSL_REDIRECT` : activer derrière un proxy TLS correctement configuré.
- `DJANGO_TRUST_PROXY_SSL` : définir à `true` uniquement si un reverse proxy de confiance efface et réécrit `X-Forwarded-Proto`.
- `SECURE_HSTS_SECONDS` : durée HSTS ; la valeur de production par défaut est un an.
- `DATABASE_URL` : vide en local pour SQLite ; URL `postgresql://user:password@host:5432/database` en production.
- `DB_SSLMODE` : mode SSL PostgreSQL, généralement `require` chez l’hébergeur.
- `REDIS_URL` : obligatoire quand `DJANGO_DEBUG=false`, par exemple `redis://redis:6379/0`.
- `EMAIL_BACKEND` : backend console local ou `django.core.mail.backends.smtp.EmailBackend` pour Gmail.
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` : paramètres SMTP organisationnels.

## PostgreSQL et Redis

Créer une base PostgreSQL et un rôle applicatif à privilèges minimum, puis définir `DATABASE_URL`. Les caractères réservés du nom d’utilisateur et du mot de passe doivent être encodés dans l’URL. Définir `DB_SSLMODE=require` lorsque la politique de l’hébergeur l’exige.

Redis est requis en production : le canal mémoire ne transmet pas les événements entre plusieurs processus. Le déploiement doit fournir la même valeur `REDIS_URL` à chaque worker ASGI. Les tables de présence utilisent des battements et expirent logiquement après deux minutes ; prévoir une tâche périodique de nettoyage des connexions obsolètes dans un déploiement long-lived.

## SMTP Gmail

1. Utiliser une boîte organisationnelle CEOBEF et activer la validation en deux étapes.
2. Générer un mot de passe d’application dans le compte Google ; utiliser cette valeur de 16 caractères comme `EMAIL_HOST_PASSWORD`.
3. Définir `EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587` et `EMAIL_USE_TLS=true`.
4. Utiliser la même boîte organisationnelle dans `EMAIL_HOST_USER` et `DEFAULT_FROM_EMAIL`.
5. Tester le flux de réinitialisation et la publication d’un événement avant l’ouverture aux membres.

Le mot de passe principal Google et les codes de récupération ne doivent jamais être utilisés. Préférer le gestionnaire de secrets de l’hébergeur à un fichier `.env` en production.

## Démarrage et livraison

```powershell
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py test
```

Le serveur d’application doit lancer `config.asgi:application` avec Daphne ou un serveur ASGI compatible, derrière un reverse proxy TLS qui prend en charge les upgrades WebSocket. WhiteNoise sert les fichiers statiques collectés. Ne jamais exposer `private-media/` directement via le serveur web. Quand `DJANGO_DEBUG=false`, les réglages refusent de démarrer sans secret, hôtes, PostgreSQL, Redis, SMTP Gmail et redirection HTTPS configurés.

Les photos publiques passent par la vue contrôlée `core:public-image`. Les documents, reçus et pièces jointes ne sont transmis qu’après vérification de l’identité, du rôle ou de l’appartenance à la conversation. Conserver `private-media/` sur un stockage persistant chiffré et sauvegardé ; mettre en œuvre rétention, antivirus et restauration testée avant une exploitation réelle.

Pour ajouter un responsable, définir son rôle depuis l’administration et enregistrer l’utilisateur. Le groupe Django `CEOBEF: …` et ses permissions sont synchronisés automatiquement. Les fiches exécutives publiques se gèrent dans « Bureau exécutif ».

## Contrôles avant lancement

- Remplacer le `SECRET_KEY` de développement et configurer tous les domaines/origines.
- Confirmer HTTPS, cookies sécurisés, proxy ASGI et règles pare-feu.
- Configurer PostgreSQL, Redis, SMTP et stockage privé persistant.
- Créer un superutilisateur avec un secret robuste et activer MFA au niveau de l’hébergement/SSO si disponible.
- Vérifier quotas upload, analyse antivirus, sauvegardes, journaux, alertes et procédure de restauration.
- Tester vérification e-mail, récupération de compte, permissions des responsables, téléchargements privés, WebSocket et délivrabilité.
- Définir les responsables métier habilités à traiter les données personnelles, photos et justificatifs financiers.

Le code fournit les mécanismes applicatifs principaux, mais ne remplace pas ces engagements d’exploitation, la revue de sécurité indépendante ni une procédure de réponse aux incidents.