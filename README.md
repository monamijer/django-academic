# GESTOCK — Application web de gestion de stock

Projet Django (Python) réalisé pour l'examen : application web avec authentification,
autorisations différenciées, historique des activités, opérations CRUD sur plusieurs
types d'articles (produits, catégories, mouvements de stock, utilisateurs), recherche,
et rapports imprimables.

## Fonctionnalités couvertes

- **Authentification** : connexion/déconnexion (`comptes` app), comptes activables/désactivables.
- **Autorisations différenciées** :
  - Administrateurs (`est_administrateur=True`) → toutes les autorisations.
  - Autres utilisateurs → permissions Django standard, assignées via des **groupes**
    (ex. groupe "Magasinier" : peut ajouter/modifier des produits et enregistrer des
    mouvements, mais ne peut ni supprimer ni gérer les comptes).
- **Historique des activités** (`JournalActivite`) : chaque ajout, modification, affichage,
  suppression, désactivation, recherche, connexion/déconnexion et impression de rapport
  est journalisé avec l'utilisateur, la date/heure et l'objet concerné — consultable dans
  "Historique" (réservé aux administrateurs).
- **CRUD complet** sur :
  - Produits (plusieurs catégories/types), avec activation/désactivation, recherche, alertes de stock bas.
  - Catégories de produits (avec couleur associée, utilisée dans toute l'interface).
  - Mouvements de stock (entrées/sorties), qui mettent à jour automatiquement les quantités.
  - Utilisateurs (réservé aux administrateurs), avec gestion des groupes/rôles.
- **Rapports imprimables** (bouton Imprimer → mise en page dédiée à l'impression) :
  - Entrées/sorties sur une période (7 ou 30 jours, personnalisable).
  - Produits périmés et bientôt périmés.
  - État actuel du stock avec valeur totale.
- **Interface** : Bootstrap 5 + Bootstrap Icons, boutons avec icônes, couleur dédiée par
  section (utilisateurs = violet, produits = bleu, mouvements = vert, rapports = orange,
  actions destructrices = rouge), badges de couleur par catégorie de produit.
- **Données partagées** : toutes les données (produits, mouvements...) sont visibles par
  tous les utilisateurs connectés dont les permissions le permettent — ce n'est pas un
  silo par utilisateur.

## Installation locale

```bash
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # puis éditez .env si besoin

python manage.py migrate
python manage.py donnees_demo   # crée les comptes et données de démonstration
python manage.py runserver
```

Ouvrez http://127.0.0.1:8000/

### Comptes de démonstration

| Rôle          | Identifiant  | Mot de passe        | Droits                                   |
|---------------|--------------|----------------------|-------------------------------------------|
| Administrateur| `admin`      | `AdminGestock2026!`  | Toutes les autorisations                  |
| Magasinier    | `magasinier` | `Magasin2026!`       | Produits/mouvements uniquement, pas de suppression, pas de gestion des utilisateurs |

**Changez ces mots de passe avant tout déploiement réel.**

## Utiliser PostgreSQL (au lieu de SQLite)

1. Créez une base PostgreSQL et un utilisateur.
2. Dans `.env`, définissez :
   `DATABASE_URL=postgres://utilisateur:motdepasse@localhost:5432/gestock`
3. Relancez `python manage.py migrate`.

## Structure du projet

```
gestock/        # paramètres et routes globales du projet Django
comptes/        # utilisateurs, connexion, groupes/permissions, historique des activités
stock/          # catégories, produits, mouvements de stock (CRUD, recherche)
rapports/       # rapports imprimables (mouvements, péremption, état du stock)
templates/      # gabarit de base partagé (base.html) + pagination
```

## Créer un compte administrateur supplémentaire

```bash
python manage.py createsuperuser
```
Puis, dans l'interface "Utilisateurs" (ou l'admin Django `/admin/`), cochez
« est_administrateur » pour lui donner toutes les autorisations.

## Pistes pour aller plus loin (bonus pour la soutenance)

- Générer les rapports en PDF téléchargeable (ex. avec `weasyprint`) en plus de l'impression navigateur.
- Ajouter un export CSV/Excel des listes.
- Ajouter un éditeur WYSIWYG si des descriptions longues sont nécessaires.
- Ajouter des tests automatisés (`python manage.py test`).
