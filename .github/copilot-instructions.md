# Instructions du workspace CEOBEF

- Projet Django 6 et Python 3.14 ; utiliser l’interpréteur `.venv` du workspace.
- Les noms d’URL et le contenu visible sont en français ; conserver l’architecture des apps Django existantes.
- Le frontend utilise templates Django, HTML sémantique, CSS natif modulaire et JavaScript Vanilla. Ne pas introduire de framework sans demande explicite.
- Ne jamais exposer `private-media/` directement. Les documents, reçus et pièces jointes doivent rester derrière une vue d’autorisation.
- Utiliser les groupes et permissions Django pour les actions réservées. Ne pas se fier uniquement à un rôle affiché dans le frontend.
- Pour les changements de modèle, créer et valider une migration. Ajouter des tests HTTP ou WebSocket couvrant le comportement modifié.
- Exécuter `python manage.py check`, `python manage.py test` et `python manage.py makemigrations --check --dry-run` avant livraison.
- Les paramètres sensibles viennent de l’environnement ; ne pas committer `.env`, mots de passe, clés ou données étudiantes.
- En production, PostgreSQL, HTTPS, SMTP sécurisé et Redis pour Channels sont requis.