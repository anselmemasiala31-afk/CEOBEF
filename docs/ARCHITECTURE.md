# Architecture et données

## Découpage

Le projet suit une séparation pragmatique : les modèles et migrations représentent la persistance Django ORM ; les vues/fournisseurs assemblent les requêtes et autorisations HTTP ; formulaires et validations contrôlent les entrées ; `community.services` coordonne les notifications ; les signaux gèrent les événements de cycle de vie ; `messaging.consumers` porte le protocole WebSocket. Les templates rendent la présentation HTML, les feuilles CSS et modules JavaScript assurent le comportement du navigateur sans framework.

Les dépendances de configuration sont au centre dans `config`. Les applications de domaine restent isolées autant que les relations métier le permettent : `accounts`, `events`, `community`, `library`, `finance` et `messaging`.

## Applications et modèles

### accounts

- `User` dérive de `AbstractUser`. Son e-mail est unique ; son rôle et la vérification de l’adresse sont persistés sur le compte.
- `StudentProfile` est OneToOne avec `User`, avec photo, université, faculté, promotion, lieu d’origine, téléphone, biographie et date d’adhésion.
- `ExecutiveMember` est OneToOne avec `User`. Il décrit la fonction, le mandat, l’ordre d’affichage et la visibilité publique.

Un utilisateur est l’acteur commun référencé par les autres domaines. Le signal crée un profil et associe son groupe de rôle. Après validation e-mail, il rejoint les groupes officiels.

### events

- `Event` référence son auteur de création, porte un statut, un slug, les dates, un lieu, une capacité et une image.
- `EventRSVP` relie un `Event` et un `User`. Une contrainte unique empêche les doublons. La capacité est vérifiée dans une transaction avec verrouillage de l’événement.

La publication d’un événement crée des notifications et envoie l’annonce par e-mail aux membres actifs dont l’e-mail est vérifié. L’envoi démarre après validation de la transaction.

### community

- `Announcement` référence son auteur et peut contenir une image ; `Comment` référence une annonce et son auteur.
- `Notification` appartient à un utilisateur, possède catégorie, texte, URL interne, horodatage et date de lecture.
- `GalleryAlbum` référence optionnellement un événement et un créateur ; `GalleryPhoto` référence son album.

Le service `notify_users` crée les notifications en lots et publie l’événement dans le canal personnel Channels après commit. Les créations unitaires utilisent le signal de notification.

### library et finance

- `Document` référence son téléverseur et conserve catégorie, nom d’origine et visibilité membre.
- `Contribution` référence un membre, éventuellement l’agent d’enregistrement, et stocke montant, devise, période, état et reçu.

Les téléchargements privés utilisent des vues dédiées avec `has_perm()` ou propriété du document/versement ; les champs `FileField` ne sont pas exposés directement comme média public.

### messaging

- `Conversation` possède un ensemble de participants, un créateur, un type et un identifiant déterministe pour les conversations privées ; les groupes officiels sont provisionnés après migration.
- `Message` référence sa conversation et son auteur, contient le texte et une pièce jointe optionnelle.
- `MessageReadReceipt` associe un message à un lecteur avec contrainte d’unicité.
- `PresenceConnection` associe un utilisateur à un canal WebSocket et son dernier battement.

Les pièces jointes PDF/images sont filtrées par extension et taille à la réception, puis téléchargeables seulement par les participants. En production, compléter la validation MIME par analyse antivirus et inspection de contenu.

## Relations (résumé)

```text
User 1──1 StudentProfile
User 1──0..1 ExecutiveMember
User 1──N Event (created_by)
Event N──N User (through EventRSVP)
User 1──N Announcement 1──N Comment
User 1──N Notification
Event 1──N GalleryAlbum 1──N GalleryPhoto
User 1──N Document
User 1──N Contribution (member / recorded_by)
Conversation N──N User (participants)
Conversation 1──N Message 1──N MessageReadReceipt
User 1──N PresenceConnection
```

Les suppressions sont majoritairement protégées pour les historiques financiers et institutionnels (`PROTECT`), tandis que les enfants dépendants comme commentaires, photos et messages sont supprimés avec leur parent (`CASCADE`).

## RBAC

Les rôles d’application sont reliés à des groupes Django nommés `CEOBEF: Membre`, `CEOBEF: Secrétaire`, `CEOBEF: Trésorier`, `CEOBEF: Président` et `CEOBEF: Administrateur`. Les permissions créées par Django et celles déclarées dans les modèles sont assignées après migrations. Les points d’écriture réservés vérifient les permissions effectives via `has_perm()` ; le superutilisateur garde l’accès complet.

Le visiteur est un état non authentifié, pas un groupe. Les pages publiques sont limitées aux listes publiées, actualités et albums publics, tandis que tableau de bord, bibliothèque et cotisations exigent une connexion.

## Cycle WebSocket

1. Daphne reçoit HTTP et WebSocket via `config.asgi:application`.
2. `AllowedHostsOriginValidator` valide l’origine et `AuthMiddlewareStack` hydrate la session.
3. Le consumer vérifie l’authentification et l’appartenance à la conversation avant `accept()`.
4. Les messages et reçus sont écrits en base ; `group_send` diffuse message, saisie, lecture et présence.
5. Un battement met à jour `PresenceConnection`; une connexion déconnectée supprime sa ligne.
6. Le consumer de notifications utilise un groupe individuel `user_<id>`.

La couche mémoire locale convient à un seul processus. En production Redis est obligatoire pour synchroniser les groupes entre workers. Le navigateur reconnecte le chat après interruption réseau.

## SMTP et signaux

L’inscription sauvegarde le compte inactif et un profil avec la photo obligatoire ; un jeton Django signé expire après 72 heures. La vérification active le compte et l’ajoute aux groupes officiels. `events.signals` détecte la première publication, attend le commit, crée des notifications et envoie l’e-mail SMTP. Les erreurs d’e-mail d’événement sont journalisées sans annuler l’événement. En production, un worker de tâches (Celery/RQ) est recommandé pour sortir les envois et créations en lots du cycle HTTP.

## Extensions différées

Le modèle de commentaires est prêt, mais il n’existe pas encore de modération/anti-abus dédiée. Les paiements ne sont pas automatisés : les cotisations sont enregistrées par un trésorier avec historique. Les fichiers ne sont pas stockés dans S3 et il n’y a pas encore de tâche périodique de purge de présence, d’indexation de recherche ou de métriques centralisées.