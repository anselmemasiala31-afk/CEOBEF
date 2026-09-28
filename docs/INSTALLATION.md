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

## Déploiement Render gratuit

Le Blueprint [render.yaml](../render.yaml) crée un service web Daphne, un PostgreSQL Free de 1 Go et un Key Value Free pour `channels_redis`, tous dans la région Oregon. Python 3.14.3 est sélectionné par `PYTHON_VERSION` ; le fichier local `.python-version` n’est pas requis par le Blueprint.

1. Pousser la branche contenant `render.yaml` sur GitHub.
2. Dans le tableau de bord Render, choisir **New > Blueprint**, connecter le dépôt CEOBEF et sélectionner la branche `main`.
3. Lors de la création initiale, saisir les variables demandées par Render : `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` et `DJANGO_SUPERUSER_PASSWORD`. Le mot de passe Gmail doit être un mot de passe d’application ; le mot de passe superutilisateur doit être unique et long. Ces valeurs `sync: false` restent dans les secrets Render et ne sont pas écrites dans le Blueprint.
4. Laisser Render construire et déployer. `collectstatic --noinput` s’exécute au build ; `migrate --noinput` précède le lancement Daphne à chaque démarrage. Après le premier déploiement réussi, `initialDeployHook` crée le superutilisateur de manière idempotente.
5. Une fois la connexion à `/admin/` vérifiée, supprimer du service les trois variables `DJANGO_SUPERUSER_*`. Ne pas supprimer les variables SMTP tant que le backend SMTP est configuré.
6. Ouvrir l’URL `https://<nom-du-service>.onrender.com`. Le service gratuit s’endort après 15 minutes sans trafic ; le réveil peut prendre environ une minute.

Commandes Blueprint utilisées :

```text
Build: pip install -r requirements.txt && python manage.py collectstatic --noinput
Start: python manage.py migrate --noinput && daphne -b 0.0.0.0 -p $PORT config.asgi:application
Initial deploy hook: python manage.py bootstrap_render_admin
```

### Limites bloquantes du plan gratuit

- Le Blueprint configure volontairement SMTP Gmail sur le port 587, mais Render bloque le trafic SMTP sortant sur les ports 25, 465 et 587 des services Web Free. **Les e-mails de validation, de récupération de mot de passe et de notification ne seront donc pas délivrés depuis ce plan**, même avec les bons secrets Gmail. Ne pas considérer la vérification e-mail ni les notifications Gmail comme opérationnelles en Free. Pour les délivrer, utiliser un plan Render qui permet SMTP ou intégrer un relais API HTTPS dans un changement ultérieur.
- PostgreSQL Free est limité à 1 Go, sans sauvegardes Render, et expire 30 jours après création. Après une période de grâce de 14 jours, Render supprime la base. Exporter les données et migrer vers une base durable avant expiration.
- Le disque du service Free est éphémère : photos, documents, reçus et pièces jointes dans `private-media/` sont perdus à chaque redémarrage, redéploiement ou mise en veille. Aucun disque persistant n’est disponible sur ce plan.
- Render Key Value Free dispose de 25 Mo, ne persiste pas ses données et peut redémarrer. Les WebSockets passent par Redis et fonctionnent entre consommateurs pendant que les services sont actifs, mais ne constituent pas une présence durable ; les connexions et messages non persistés par CEOBEF disparaissent au redémarrage.
- L’instance Web Free peut s’endormir, redémarrer, être suspendue à l’épuisement des heures gratuites et ne peut pas être mise à l’échelle. Cette offre sert à une démonstration, pas à l’exploitation de données d’étudiants ou à un service officiel fiable.

Pour une exploitation réelle, utiliser un calcul payant, PostgreSQL avec sauvegardes, un stockage média privé persistant, Key Value/Redis durable et un fournisseur de courriel dont la méthode d’envoi est autorisée. Ne pas téléverser de documents sensibles sur l’offre gratuite.

### Contrôles après déploiement

- Accueil : `https://<service>.onrender.com/` doit répondre `200`.
- Statique : demander l’URL `static/css/site.css` ou `static/js/site.js` affichée dans le HTML ; WhiteNoise doit répondre `200`.
- PostgreSQL : vérifier le démarrage et les migrations dans les logs Render ; la commande `python manage.py showmigrations` est aussi disponible depuis un shell lorsque le plan le permet.
- Administration : ouvrir `/admin/` et utiliser le superutilisateur créé par le hook initial.
- WebSocket : connecté comme membre, vérifier l’onglet Réseau du navigateur pour `wss://<service>.onrender.com/ws/notifications/` et `/ws/chat/<id>/`. Le chat exige d’abord une conversation et une session membre valide.
- Médias : ne pas vérifier en supposant une persistance. Sur Free, un fichier autorisé peut être servi par sa vue tant que le même processus et son disque temporaire existent ; il sera perdu au prochain redémarrage/spin-down.
- E-mail : un test d’envoi Gmail ne réussira pas depuis le service Web Free à cause du blocage réseau du port 587. Effectuer ce test uniquement depuis un plan/relais autorisant le SMTP.

## Variables d’environnement

Copier `.env.example` vers `.env`. Ne jamais ajouter `.env` à un dépôt ou exposer un mot de passe d’application dans les logs.

- `SECRET_KEY` (Render) ou `DJANGO_SECRET_KEY` (développement) : valeur secrète aléatoire générée par Render ou créée pour l’environnement.
- `DEBUG` (Render) ou `DJANGO_DEBUG` (développement) : `False` en production, `true` localement.
- `ALLOWED_HOSTS` (Render) ou `DJANGO_ALLOWED_HOSTS` (développement) : noms d’hôte séparés par des virgules, sans schéma.
- `CSRF_TRUSTED_ORIGINS` : origines HTTPS complètes séparées par des virgules.
- `DJANGO_SECURE_SSL_REDIRECT` : activer derrière un proxy TLS correctement configuré.
- `DJANGO_TRUST_PROXY_SSL` : définir à `true` uniquement si un reverse proxy de confiance efface et réécrit `X-Forwarded-Proto`.
- `SECURE_HSTS_SECONDS` : durée HSTS ; la valeur de production par défaut est un an.
- `DATABASE_URL` : vide en local pour SQLite ; URL `postgresql://user:password@host:5432/database` en production.
- `DB_SSLMODE` : mode SSL PostgreSQL, généralement `require` chez l’hébergeur.
- `REDIS_URL` : URL interne Key Value/Redis, injectée par le Blueprint ; pour un autre environnement, par exemple `redis://redis:6379/0`.
- `EMAIL_BACKEND` : backend console local ou `django.core.mail.backends.smtp.EmailBackend` pour Gmail.
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` : paramètres SMTP organisationnels.

Variables présentes sur le service Web du Blueprint Render :

| Variable | Source / valeur |
| --- | --- |
| `PYTHON_VERSION` | `3.14.3` |
| `SECRET_KEY` | Générée par Render (`generateValue`) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com,localhost,127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` |
| `DJANGO_TRUST_PROXY_SSL` | `true` |
| `SECURE_HSTS_SECONDS` | `31536000` |
| `DB_SSLMODE` | `require` |
| `DATABASE_URL` | Référence privée à la base Render (`fromDatabase`) |
| `REDIS_URL` | Référence au Key Value Render (`fromService`) |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | `smtp.gmail.com` |
| `EMAIL_PORT` | `587` |
| `EMAIL_USE_TLS` | `true` |
| `EMAIL_HOST_USER` | À fournir dans Render ; adresse Gmail organisationnelle |
| `EMAIL_HOST_PASSWORD` | À fournir dans Render ; mot de passe d’application Gmail |
| `DEFAULT_FROM_EMAIL` | À fournir dans Render ; adresse d’expédition CEOBEF |
| `DJANGO_SUPERUSER_USERNAME` | À fournir pour le premier déploiement, puis supprimer |
| `DJANGO_SUPERUSER_EMAIL` | À fournir pour le premier déploiement, puis supprimer |
| `DJANGO_SUPERUSER_PASSWORD` | À fournir pour le premier déploiement, puis supprimer |

Render fournit également `PORT` automatiquement ; ne pas créer de variable `PORT` personnalisée.

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