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

Le fichier `render.yaml` définit un service web Python `free`, Daphne/ASGI, un PostgreSQL `free`, la collecte WhiteNoise au build et les migrations au démarrage. Il référence les valeurs sensibles depuis Render (`generateValue`, `sync: false` et `fromDatabase`) ; aucun secret ou identifiant DB n’est commité. Render Free ne permet pas d’attacher un disque persistant au service web : cette configuration est une démo/hébergement d’essai et non un déploiement durable pour des données d’étudiants.

1. Pousser la branche `main` vers GitHub.
2. Dans Render, choisir **New > Blueprint**, connecter le dépôt GitHub CEOBEF et sélectionner `render.yaml`.
3. Vérifier les ressources proposées puis créer le Blueprint. Render crée le PostgreSQL et le service web dans la même région ; `DATABASE_URL` est relié par `fromDatabase`.
4. Lors de la première synchronisation, saisir les valeurs demandées pour le compte SMTP et les variables temporaires `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` et `DJANGO_SUPERUSER_PASSWORD`. Utiliser un mot de passe d’application Google, jamais le mot de passe principal. Le mot de passe administrateur est consommé par le hook initial, jamais commité.
5. Attendre le build et l’initialisation, puis ouvrir `https://<nom-du-service>.onrender.com`. Les migrations sont exécutées par `startCommand` à chaque démarrage ; `collectstatic` est exécuté durant le build et `initialDeployHook` crée le premier superutilisateur sans exiger de shell.
6. Après confirmation de la connexion `/admin/`, supprimer les trois variables `DJANGO_SUPERUSER_*` du service Render et ne pas les synchroniser à nouveau. Vérifier la page d’accueil, un chemin `/static/...`, la connexion, l’administration et un WebSocket `/ws/notifications/` avec une session membre. Le plan gratuit peut s’endormir ; le premier réveil peut prendre environ une minute.

### Limites bloquantes du plan gratuit

- **PostgreSQL Free expire après 30 jours**, est limité à 1 Go et ne dispose pas de sauvegardes Render. Il faut migrer vers une base durable/payante ou accepter la perte/suppression des données après la période de grâce. Ne pas y placer des dossiers, profils ou cotisations étudiants sans accord et sauvegarde externe.
- **Le système de fichiers du service web est éphémère** : photos de profil, images, documents, reçus et pièces jointes stockés dans `private-media/` sont perdus au spin-down, redémarrage ou redeploy. Le service Free ne peut pas avoir de disque persistant. Pour conserver les médias, ajouter un stockage objet externe durable et tester sa sécurité avant l’ouverture aux membres.
- **Render Free bloque les connexions sortantes SMTP sur les ports 25, 465 et 587.** Les connexions Gmail SMTP configurées par le Blueprint ne peuvent donc pas être délivrées depuis un web service gratuit, même avec les bons identifiants. Pour Gmail SMTP, il faut un plan Render autorisant cette sortie ou un relais externe ; un fournisseur d’e-mail avec API HTTPS nécessite un changement d’intégration.
- `CHANNEL_LAYER=memory` est délibérément utilisé pour la seule instance gratuite, sans Redis. Les WebSockets fonctionnent dans le processus unique, mais les groupes ne sont pas partagés, leur état n’est pas durable et tout redémarrage rompt les connexions. Pour plusieurs workers ou une disponibilité supérieure, configurer Redis et un plan adapté.
- Les instances gratuites peuvent s’endormir, redémarrer ou atteindre leurs quotas. Elles sont destinées à l’essai, pas aux données sensibles ni à une plateforme communautaire de production.

Pour une exploitation réelle, utiliser PostgreSQL sauvegardé, médias persistants privés, Redis, un service d’e-mail dont l’egress est permis, HTTPS et un plan de calcul sans limites gratuites. Les migrations au démarrage permettent le déploiement gratuit, mais une stratégie de migration séparée/pré-déploiement est préférable sur un environnement payant à plusieurs instances.

## Variables d’environnement

Copier `.env.example` vers `.env`. Ne jamais ajouter `.env` à un dépôt ou exposer un mot de passe d’application dans les logs.

- `DJANGO_SECRET_KEY` ou `SECRET_KEY` : valeur aléatoire unique, secrète et persistante pour l’environnement.
- `DJANGO_DEBUG` ou `DEBUG` : `false` en production.
- `DJANGO_ALLOWED_HOSTS` ou `ALLOWED_HOSTS` : noms d’hôte séparés par des virgules, sans schéma.
- `CSRF_TRUSTED_ORIGINS` : origines HTTPS complètes séparées par des virgules.
- `DJANGO_SECURE_SSL_REDIRECT` : activer derrière un proxy TLS correctement configuré.
- `DJANGO_TRUST_PROXY_SSL` : définir à `true` uniquement si un reverse proxy de confiance efface et réécrit `X-Forwarded-Proto`.
- `SECURE_HSTS_SECONDS` : durée HSTS ; la valeur de production par défaut est un an.
- `DATABASE_URL` : vide en local pour SQLite ; URL `postgresql://user:password@host:5432/database` en production.
- `DB_SSLMODE` : mode SSL PostgreSQL, généralement `require` chez l’hébergeur.
- `REDIS_URL` : Redis pour plusieurs processus, par exemple `redis://redis:6379/0`. Sans Redis en production, `CHANNEL_LAYER=memory` doit être explicitement défini et n’est pris en charge que pour une instance unique.
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

Le serveur d’application doit lancer `config.asgi:application` avec Daphne ou un serveur ASGI compatible, derrière un reverse proxy TLS qui prend en charge les upgrades WebSocket. WhiteNoise sert les fichiers statiques collectés. Ne jamais exposer `private-media/` directement via le serveur web. Quand `DEBUG=false`, les réglages refusent de démarrer sans secret, hôtes, PostgreSQL, SMTP configuré et redirection HTTPS ; `REDIS_URL` est nécessaire pour plusieurs workers, alors que `CHANNEL_LAYER=memory` est explicitement toléré pour un seul processus.

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