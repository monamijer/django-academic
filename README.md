# UNIVPILOT — Gestion universitaire (étudiants & personnel)

Projet Django réalisé pour l'examen : application web de gestion universitaire
avec authentification, une hiérarchie de rôles complète (étudiants et
personnel), historique des activités, CRUD scopé par périmètre, et rapports
imprimables.

## Rôles et matrice de permissions

| Rôle | Périmètre | Peut faire |
|---|---|---|
| Administrateur système | Global (technique) | Gère tous les comptes, configure l'application, consulte tout l'historique |
| Directeur académique | Toute l'université | Vision et rapports transversaux sur toutes les facultés |
| Doyen | Une faculté | Gère les départements, filières et cours de sa faculté |
| Chef de département | Un département | Gère les cours, étudiants et inscriptions de son département |
| Professeur | Ses cours | Saisit/modifie les notes des étudiants inscrits à ses cours uniquement |
| Secrétaire | Un département | Gère les dossiers étudiants et les inscriptions, sans accès aux notes |
| Étudiant | Lui-même | Consulte son profil, ses notes, sa moyenne et sa mention |

Le principe : chaque rôle ne voit et ne modifie que son périmètre
(établissement > faculté > département > cours), jamais l'ensemble par
défaut. Implémenté via les groupes Django (`configurer_roles`, ce que le rôle
peut faire) combinés à un filtrage de queryset par périmètre sur le modèle
`Utilisateur` (`departements_geres()`, `a_acces_global`, sur quoi il agit).

## Fonctionnalités

- **Authentification** + **page "Mon profil"** en libre-service pour tous
  les rôles (infos personnelles, changement de mot de passe avec vérification
  de l'ancien, périmètre en lecture seule) — distincte de la gestion
  administrative des comptes (réservée à l'administrateur système).
- **Historique des activités** automatique (signaux Django), consultable par
  l'administrateur système et le directeur académique.
- **CRUD scopé** : facultés (global), départements/filières/cours (doyen/chef
  de département), étudiants/inscriptions (chef de département/secrétaire),
  notes (professeur, uniquement pour ses propres cours et étudiants inscrits).
- **Logique métier automatique** : calcul de moyenne et de mention par
  étudiant, détection des étudiants en difficulté (moyenne < 10) affichée sur
  le tableau de bord du chef de département, vérification de la capacité
  maximale d'un cours à l'inscription.
- **Rapports imprimables** (CSS dédié à l'impression) : relevé de notes d'un
  étudiant, liste des étudiants par périmètre, liste du personnel par
  périmètre, rapport de performance d'un cours (moyenne + distribution des
  notes).
- **Tableau de bord différent par rôle** : un seul point d'entrée après
  connexion, dont le contenu change entièrement selon le rôle connecté.
- **Identité visuelle académique** : bleu "Oxford" + or, typographie Fraunces
  (titres) / Work Sans (interface), grille de fiches pour les listes de
  personnes/cours, tableaux denses pour les vues administratives.

## Installation locale (SQLite, par défaut)

```bash
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env

python manage.py migrate
python manage.py donnees_demo   # crée les groupes de rôles + un compte par rôle + données réalistes
python manage.py runserver
```

Ouvrez http://127.0.0.1:8000/

### Comptes de démonstration

| Rôle | Identifiant | Mot de passe |
|---|---|---|
| Administrateur système | `admin` | `AdminUniv2026!` |
| Directeur académique | `directeur` | `Directeur2026!` |
| Doyen (Faculté des Sciences) | `doyen` | `Doyen2026!` |
| Chef de département (Informatique) | `chef_dept` | `ChefDept2026!` |
| Professeur (Informatique) | `professeur` | `Prof2026!` |
| Secrétaire (Informatique) | `secretaire` | `Secretaire2026!` |
| Étudiant | `etudiant1` | `Etudiant2026!` |

**Changez ces mots de passe avant tout déploiement réel.**

## Utiliser MySQL via XAMPP (au lieu de SQLite)

1. Démarrez **Apache** et **MySQL** depuis le panneau de contrôle XAMPP.
2. Ouvrez phpMyAdmin (http://localhost/phpmyadmin) et créez une base nommée
   `gestion_universite` (utf8mb4_unicode_ci).
3. Dans `.env`, définissez :
   ```
   USE_MYSQL=True
   MYSQL_DATABASE=gestion_universite
   MYSQL_USER=root
   MYSQL_PASSWORD=
   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3306
   ```
4. Relancez `python manage.py migrate` puis `python manage.py donnees_demo`.

Le projet utilise PyMySQL (installé comme driver MySQLdb dans
`settings.py`) plutôt que `mysqlclient`, pour éviter les problèmes de
compilation native sur certains systèmes.

## Structure du projet

```
universite/     # paramètres et routes globales du projet Django
comptes/        # utilisateurs, rôles, connexion, profil, historique des activités
academique/     # facultés, départements, filières, cours, années académiques
etudiants/      # fiches étudiants, inscriptions, notes, saisie de notes par le professeur
rapports/       # rapports imprimables (relevés, listes, performance de cours)
templates/      # gabarit de base partagé (base.html) + pagination
```

## Historique Git

Le projet a été développé par étapes, chacune correspondant à un commit
atomique et testé (`git log --oneline` pour le détail) : scaffold → config
BDD → modèle utilisateur/rôles → structure académique → étudiants/notes →
migrations → permissions → auth/profil/dashboards → CRUD académique → CRUD
étudiants/notes → rapports → données de démo → correctif d'un bug de
redirection découvert en testant l'accès non autorisé.

## Pistes pour aller plus loin

- Export PDF des rapports (ex. `weasyprint`) en plus de l'impression navigateur.
- Notifications pour un étudiant qui passe sous le seuil de réussite.
- Tests automatisés (`python manage.py test`) pour figer le comportement du
  filtrage par périmètre.
