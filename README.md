# CEOBEF

CEOBEF est le portail communautaire de la Communauté Estudiantine Originaire de Bas-Fleuve. Cette première version réunit le site institutionnel, les comptes étudiants, les événements, les actualités, les notifications, la bibliothèque, le suivi des cotisations, le bureau exécutif et une messagerie Django Channels.

## État du produit

Le projet fournit un socle fonctionnel Django, ses migrations, l’interface responsive en HTML/CSS/JavaScript natif, les contrôles d’accès côté serveur, un back-office Django et des tests HTTP/WebSocket. Le lancement local fonctionne avec SQLite, l’e-mail console et le canal mémoire de Channels.

Un déploiement multi-processus nécessite PostgreSQL, Redis pour les groupes WebSocket, une clé secrète dédiée, SMTP Gmail correctement configuré, HTTPS et un stockage sauvegardé pour `private-media/`. L’inscription publique crée un compte inactif et envoie un lien de vérification. En développement, le lien est imprimé dans le terminal via le backend e-mail console.

## Démarrage rapide

Windows PowerShell :

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Le site est disponible sur `http://127.0.0.1:8000/`. Le serveur `runserver` est fourni par Daphne et prend en charge HTTP et WebSocket.

Pour compiler les ressources statiques comme en production :

```powershell
python manage.py collectstatic --noinput
```

Pour exécuter les contrôles et les tests :

```powershell
python manage.py check
python manage.py test
```

## Applications Django

- `config` : réglages par environnement, URLs racine, routage ASGI/WSGI et déploiement.
- `accounts` : utilisateur personnalisé, profil étudiant, rôles, bureau exécutif, inscription et vérification de l’e-mail.
- `core` : pages d’accueil et de synthèse, permissions communes et livraison contrôlée des images publiques.
- `events` : événements, inscriptions, capacité, notifications et annonces e-mail.
- `community` : actualités, commentaires, notifications, albums, photos et diffusion WebSocket des notifications.
- `library` : documents téléchargeables derrière authentification et permissions.
- `messaging` : conversations directes et officielles, messages, accusés de lecture, présence et sockets privés.
- `finance` : cotisations et reçus accessibles uniquement au membre concerné ou aux rôles autorisés.

Les pages/templates sont sous `templates/`. Les styles et scripts Vanilla sont sous `static/css/` et `static/js/`. Les migrations sont conservées dans chaque application.

## Modèle de données

- `accounts.User` est l’identité authentifiée. Il porte le rôle, l’adresse vérifiée et les relations Django Group/Permission.
- `accounts.StudentProfile` complète l’utilisateur via une relation OneToOne : photo, université, faculté, promotion, origine, téléphone et biographie.
- `accounts.ExecutiveMember` associe un utilisateur à une fonction et à un mandat public.
- `events.Event` est publié par un utilisateur ; `events.EventRSVP` relie un événement et un membre avec une contrainte d’unicité par paire.
- `community.Announcement` possède un auteur et des `community.Comment`. `community.Notification` appartient à un destinataire. `GalleryAlbum` possède des `GalleryPhoto` et peut référencer un événement.
- `library.Document` appartient à son téléverseur. Le téléchargement passe par une vue d’autorisation, pas par une URL média publique.
- `finance.Contribution` référence le membre, éventuellement l’enregistreur et un justificatif.
- `messaging.Conversation` possède plusieurs participants et `Message`. `MessageReadReceipt` relie message et lecteur de manière unique. `PresenceConnection` représente une connexion WebSocket active.

## Rôles et permissions

Les rôles `member`, `secretary`, `treasurer`, `president` et `admin` sont associés à des groupes Django `CEOBEF: …`. Les permissions de modèle Django sont provisionnées après migration et contrôlées avec `has_perm()` sur les actions réservées. Le visiteur correspond à un utilisateur non authentifié. Le superutilisateur Django conserve les privilèges globaux.

Pour attribuer un rôle, utiliser le champ Rôle de l’administration Django, puis enregistrer l’utilisateur. Les groupes et permissions effectifs sont synchronisés par le signal `post_save`.

## WebSocket et messagerie

`config.asgi` route les requêtes HTTP vers Django et les sockets vers les consommateurs Channels. `AuthMiddlewareStack` fournit la session, `AllowedHostsOriginValidator` vérifie l’origine et `ChatConsumer` vérifie l’appartenance à chaque conversation avant l’acceptation. Les messages, reçus et connexions de présence sont persistés en base. Les groupes officiels sont initialisés après migration. Les pièces jointes utilisent une route de téléchargement qui exige l’appartenance à la conversation.

Le canal mémoire convient à un seul processus de développement et n’est pas partagé entre plusieurs workers. La production exige `REDIS_URL` et `channels_redis`.

## E-mail

Les paramètres SMTP sont lus dans `.env`. Gmail doit utiliser SMTP TLS sur le port 587 avec l’adresse de l’organisation et un mot de passe d’application Google ; ne jamais utiliser le mot de passe principal ni le committer. Le backend console local imprime les e-mails de validation. La publication d’un événement envoie une notification interne et un message aux membres vérifiés.

## Administration

`/admin/` fournit la gestion des membres, profils, responsables, événements/participants, publications/commentaires, albums/photos, notifications, documents, conversations et cotisations. L’export CSV des membres est disponible comme action de la liste des utilisateurs. Créer un superutilisateur avec `python manage.py createsuperuser`.

## Production

Lire [docs/INSTALLATION.md](docs/INSTALLATION.md) pour les variables, PostgreSQL, Redis, SMTP Gmail, collecte statique et vérifications de sécurité. Le répertoire `private-media/` ne doit jamais être servi directement par un reverse proxy ; les vues applicatives servent les images publiques et protègent les documents, reçus et pièces jointes.

Voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) pour les relations entre tables, le RBAC et les flux WebSocket/SMTP.
