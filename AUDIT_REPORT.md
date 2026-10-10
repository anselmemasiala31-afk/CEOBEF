# CEOBEF — Rapport d'audit technique

Date de l'audit : 28 septembre 2026  
Révision de référence : `5eced11` (`Prepare CEOBEF for PythonAnywhere deployment`)  
Portée : code Django, configuration, dépendances, templates, statiques, médias, migrations, tests, Git et déploiement Render.

## Résumé exécutif

Le dépôt contient un projet Django 6.0 modulaire, exécuté localement avec Python 3.14.3. Les contrôles système Django sont propres, aucune migration ne manque, et les 20 tests HTTP/Channels passent après `collectstatic`. WhiteNoise est installé, middleware activé, `STATIC_ROOT` défini et la configuration PostgreSQL/Redis/SMTP est pilotée par l'environnement.

Le projet peut être déployé comme application Django HTTP sur Render avec le Blueprint existant. « Prêt à déployer » ne signifie pas que l'offre Render Free est un service de production durable : PostgreSQL gratuit expire après 30 jours, le disque des services gratuits est éphémère et Render bloque l'envoi SMTP sortant sur les ports Gmail 25/465/587. Les médias privés et courriels ne peuvent donc pas être garantis sur cette offre.

## Inventaire

| Élément | État observé |
| --- | --- |
| Applications Django | `accounts`, `community`, `core`, `events`, `finance`, `library`, `messaging` |
| Projet | `config` avec `settings.py`, `urls.py`, `wsgi.py`, `asgi.py` |
| Templates | 29 fichiers HTML Django |
| Statique source | 3 fichiers : une feuille CSS et deux scripts JavaScript |
| Migrations applicatives | 7 fichiers au total : 6 migrations initiales et `library.0002_alter_document_file` ; `core` n'a pas de modèle |
| Utilisateur | `accounts.User` dérive de `AbstractUser`; profil étudiant séparé |
| Base locale | SQLite dans `db.sqlite3` |
| Base Render | PostgreSQL via `DATABASE_URL`, sans identifiants dans le code |
| Fichiers privés locaux | 25 fichiers présents sous `private-media/`; répertoire ignoré par Git |
| Dépendances | Django, Daphne, Channels, channels-redis, Pillow, WhiteNoise, psycopg binaire, python-dotenv |
| Dépôt Git | Branche `main`, poussée vers `origin`; aucune donnée `private-media` suivie |

## Résultats par surface

### Architecture, modèles et migrations

Les domaines principaux sont séparés dans sept applications : comptes/profils/RBAC, communauté/notifications/galerie, événements/participations, finances/cotisations, bibliothèque documentaire et messagerie. Les modèles utilisent contraintes d'unicité, index et relations Django ORM. Les fichiers de migrations sont présents. `manage.py makemigrations --check --dry-run` répond `No changes detected`.

Risque fonctionnel à surveiller : migrations exécutées à chaque commande de démarrage Render peuvent être concurrentes si plusieurs instances sont ajoutées. Le plan Free reste mono-instance ; pour scaler, déplacer les migrations vers une étape pré-déploiement contrôlée.

### Vues, URLs, formulaires et templates

Les routes sont montées dans `config/urls.py`. Les vues appliquent `login_required`, permissions Django, filtrage de statut et contrôles d'appartenance. Les fichiers confidentiels utilisent `FileResponse` à travers des vues de contrôle, et non des URL publiques de stockage. Les formulaires valident extensions/taille des fichiers et mots de passe.

Les pages principales existent pour inscription/connexion, profil, espace membre, événements, actualités, notifications, galerie, bibliothèque, cotisations, bureau exécutif et messagerie. Les pages protégées testées redirigent les visiteurs anonymes.

### CSS et JavaScript

Le frontend repose sur HTML Django, CSS natif et JavaScript navigateur. Les assets sont dans `static/css/site.css`, `static/js/site.js` et `static/js/chat.js`. WhiteNoise sert le manifest compressé produit par `collectstatic`. La construction du manifeste est requise avant de lancer les tests de rendu en configuration de stockage production.

### WSGI, ASGI et Channels

`config/wsgi.py` expose le callable Django WSGI. `config/asgi.py` route HTTP et WebSocket avec `ProtocolTypeRouter`, `AuthMiddlewareStack` et `AllowedHostsOriginValidator`. Les Consumers authentifient les membres et contrôlent leur appartenance aux conversations. Les tests `WebsocketCommunicator` valident les accès et la persistance.

Le Blueprint Render lance Daphne/ASGI et relie Redis/Key Value, donc le transport WebSocket est prévu. Sur PythonAnywhere, le WSGI HTTP n'est pas un serveur ASGI : le chat temps réel, présence et notifications instantanées ne doivent pas être annoncés comme fonctionnels par une simple configuration WSGI.

### Variables et sécurité Django

Les secrets proviennent de l'environnement ou d'un `.env` local ignoré. En production, le démarrage exige secret, hôtes, PostgreSQL, HTTPS, et, pour le profil Render, Redis et SMTP configurés. Cookies secure, middleware CSRF, HSTS configurable, WhiteNoise et limites de type de fichiers sont présents. Les URL de médias privés ne sont pas ajoutées à `urlpatterns` comme un service de fichiers générique.

Risque : le SMTP Gmail peut échouer sur les plans gratuits d'hébergeurs qui filtrent l'egress SMTP. La configuration applicative ne peut pas contourner ce filtrage réseau.

### Git, données et fichiers générés

`.gitignore` exclut `.env`, `.venv`, fichiers compilés Python, SQLite, `private-media/` et `staticfiles/`. Les 25 fichiers médias locaux ne sont pas suivis. Les caches `__pycache__` et le dossier de build statique sont des artefacts locaux et ne sont pas versionnés. Aucune opération d'audit n'a supprimé les médias ou fichiers appartenant à l'utilisateur.

## Défauts et risques détectés

| Gravité | Constat | État / mesure |
| --- | --- | --- |
| Bloquant pour une équivalence complète sur Render Free | PostgreSQL Free expire; stockage fichier éphémère; SMTP Gmail egress bloqué | Documenté dans les limites du Blueprint; migration vers service avec stockage/base/courriel durables nécessaire pour l'exploitation |
| Élevée si l'équipe prétend à une disponibilité durable | Les médias, reçus et pièces jointes sont des fichiers locaux | Les vues protègent les téléchargements, mais la persistance sur Render Free n'existe pas; ne pas charger de données sensibles |
| Fonctionnel par plateforme | Plusieurs fonctionnalités requièrent ASGI/WebSocket | Render utilise Daphne; cible WSGI uniquement ne transporte pas les sockets |
| Bas | `collectstatic` est nécessaire au manifest WhiteNoise | Inclus au build Render; tests locaux lancés après collecte |
| Bas | Le SMTP peut être bloqué malgré des identifiants corrects | Test de délivrabilité à exécuter depuis l'environnement hébergeur |

Aucun doublon de configuration, code mort ou TODO/FIXME de déploiement n'a été établi par la recherche ciblée. Le scan d'import Pylance n'a relevé aucun import utilisateur non résolu.

## Validation observée

- `manage.py check` : aucune anomalie.
- `manage.py makemigrations --check --dry-run` : aucune migration manquante.
- `manage.py migrate --noinput` : toutes migrations appliquées, aucune en attente.
- `manage.py collectstatic --noinput` : réussi ; le manifest WhiteNoise est produit.
- `manage.py test --verbosity 1` : 20 tests réussis, dont HTTP, protection des fichiers, inscription et WebSockets.
- Smoke-test applicatif : 12 `OK`, 0 `ERROR`, avertissements sur l'absence de compte de test, d'URL publique en local, et sur les limites WSGI/médias.
- Contrôle Pylance : aucun diagnostic dans les fichiers examinés.
- `git diff --check` : propre.
