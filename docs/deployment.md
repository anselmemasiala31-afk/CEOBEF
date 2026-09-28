# Déploiement CEOBEF

Les procédures par hébergeur sont documentées séparément :

- [PythonAnywhere gratuit](pythonanywhere_setup.md)
- [Guide complet PythonAnywhere](../DEPLOY_CEOBEF_PYTHONANYWHERE.md)
- [Render gratuit](INSTALLATION.md#déploiement-render-gratuit)

## Avertissement fonctionnel PythonAnywhere Free

PythonAnywhere Free déploie CEOBEF en WSGI. Il ne prend pas en charge le transport WebSocket Channels : la messagerie instantanée, la présence et les notifications WebSocket ne fonctionneront pas sur cette plateforme. Le site web HTTP, les comptes, l’administration, la bibliothèque, les événements et les formulaires ordinaires peuvent être servis par Django, mais le chat temps réel ne sera pas équivalent à l’installation ASGI locale. Ce guide ne modifie pas le code métier pour masquer cette différence.

Le compte gratuit expire après un mois et est limité à un worker, 100 secondes CPU et 512 MiB de disque. Les nouveaux comptes gratuits (à partir du 15 janvier 2026, ou du 8 janvier dans l’environnement UE) n’incluent pas MySQL. Le guide utilise donc SQLite dans le répertoire persistant du compte, pour une démonstration légère seulement.

Les médias CEOBEF contiennent des documents, reçus et pièces jointes privés. Ne mappez jamais `/media/` vers `private-media/` dans l’onglet Web PythonAnywhere ; les téléchargements passent par les vues d’autorisation applicatives. La configuration statique mappe uniquement `/static/`.

PythonAnywhere restreint les connexions sortantes des comptes gratuits à une liste autorisée. Vérifiez que le SMTP Gmail est joignable depuis votre compte avant de compter sur la validation d’adresse, la récupération de compte ou les notifications par e-mail. N’utilisez jamais le mot de passe principal Google.
