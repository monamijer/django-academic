from django.core.management.base import BaseCommand
from django.core.management import call_command

from academique.models import AnneeAcademique, Cours, Departement, Faculte, Filiere
from comptes.models import Utilisateur
from etudiants.models import Etudiant, Inscription, Note


class Command(BaseCommand):
    help = "Crée les groupes de rôles et un jeu de données de démonstration couvrant chaque rôle académique."

    def handle(self, *args, **options):
        call_command("configurer_roles")

        # --- Structure académique ---
        annee, _ = AnneeAcademique.objects.get_or_create(libelle="2025-2026", defaults={"est_courante": True})

        fac_sciences, _ = Faculte.objects.get_or_create(nom="Faculté des Sciences", code="FSC", defaults={"couleur": "#16233F"})
        fac_lettres, _ = Faculte.objects.get_or_create(nom="Faculté des Lettres", code="FLE", defaults={"couleur": "#A9812F"})

        dep_info, _ = Departement.objects.get_or_create(faculte=fac_sciences, nom="Informatique", code="INFO")
        dep_maths, _ = Departement.objects.get_or_create(faculte=fac_sciences, nom="Mathématiques", code="MATH")
        dep_lettres, _ = Departement.objects.get_or_create(faculte=fac_lettres, nom="Lettres Modernes", code="LM")

        fil_info, _ = Filiere.objects.get_or_create(departement=dep_info, nom="Licence Informatique", code="L-INFO", duree_annees=3)
        fil_lettres, _ = Filiere.objects.get_or_create(departement=dep_lettres, nom="Licence Lettres", code="L-LET", duree_annees=3)

        # --- Comptes : un par rôle ---
        comptes_demo = [
            dict(username="admin", role=Utilisateur.Role.ADMIN_SYSTEME, first_name="Alice", last_name="Système",
                 password="AdminUniv2026!", superuser=True),
            dict(username="directeur", role=Utilisateur.Role.DIRECTEUR_ACADEMIQUE, first_name="Bernard", last_name="Nkurunziza",
                 password="Directeur2026!"),
            dict(username="doyen", role=Utilisateur.Role.DOYEN, first_name="Claudine", last_name="Havyarimana",
                 password="Doyen2026!", faculte=fac_sciences),
            dict(username="chef_dept", role=Utilisateur.Role.CHEF_DEPARTEMENT, first_name="David", last_name="Niyonzima",
                 password="ChefDept2026!", departement=dep_info),
            dict(username="professeur", role=Utilisateur.Role.PROFESSEUR, first_name="Emerance", last_name="Ndayishimiye",
                 password="Prof2026!", departement=dep_info),
            dict(username="secretaire", role=Utilisateur.Role.SECRETAIRE, first_name="Fabrice", last_name="Bigirimana",
                 password="Secretaire2026!", departement=dep_info),
        ]

        utilisateurs = {}
        for data in comptes_demo:
            username = data["username"]
            if Utilisateur.objects.filter(username=username).exists():
                utilisateurs[username] = Utilisateur.objects.get(username=username)
                continue
            superuser = data.pop("superuser", False)
            password = data.pop("password")
            if superuser:
                u = Utilisateur.objects.create_superuser(username, f"{username}@univpilot.local", password)
                for k, v in data.items():
                    if k != "username":
                        setattr(u, k, v)
                u.save()
            else:
                u = Utilisateur.objects.create_user(username, f"{username}@univpilot.local", password, **{
                    k: v for k, v in data.items() if k != "username"
                })
            groupe_par_role = {
                Utilisateur.Role.DIRECTEUR_ACADEMIQUE: "Directeur académique",
                Utilisateur.Role.DOYEN: "Doyen",
                Utilisateur.Role.CHEF_DEPARTEMENT: "Chef de département",
                Utilisateur.Role.PROFESSEUR: "Professeur",
                Utilisateur.Role.SECRETAIRE: "Secrétaire",
            }
            nom_groupe = groupe_par_role.get(u.role)
            if nom_groupe:
                from django.contrib.auth.models import Group
                u.groups.add(Group.objects.get(name=nom_groupe))
            utilisateurs[username] = u
            self.stdout.write(self.style.SUCCESS(f"Compte créé : {username} / {password} ({u.get_role_display()})"))

        professeur = utilisateurs["professeur"]

        # --- Cours, rattaché au professeur de démonstration ---
        cours_algo, _ = Cours.objects.get_or_create(
            departement=dep_info, nom="Algorithmique", code="INFO-101",
            defaults={"credits": 5, "capacite_max": 40},
        )
        cours_algo.professeurs.add(professeur)
        cours_bd, _ = Cours.objects.get_or_create(
            departement=dep_info, nom="Bases de données", code="INFO-201",
            defaults={"credits": 4, "capacite_max": 40},
        )
        cours_bd.professeurs.add(professeur)

        # --- Étudiants de démonstration ---
        etudiants_demo = [
            ("etudiant1", "Grace", "Iradukunda", "MAT-2024-001", fil_info, 2024, [(cours_algo, 15.5), (cours_bd, 9.0)]),
            ("etudiant2", "Hervé", "Ntahonkiriye", "MAT-2024-002", fil_info, 2024, [(cours_algo, 12.0)]),
            ("etudiant3", "Immaculée", "Nzeyimana", "MAT-2025-010", fil_lettres, 2025, []),
        ]
        for username, prenom, nom, matricule, filiere, promotion, notes in etudiants_demo:
            if Utilisateur.objects.filter(username=username).exists():
                continue
            u = Utilisateur.objects.create_user(
                username, f"{username}@univpilot.local", "Etudiant2026!",
                first_name=prenom, last_name=nom, role=Utilisateur.Role.ETUDIANT,
            )
            fiche = Etudiant.objects.create(utilisateur=u, matricule=matricule, filiere=filiere, promotion=promotion)
            for cours, valeur in notes:
                Inscription.objects.get_or_create(etudiant=fiche, cours=cours, annee_academique=annee)
                Note.objects.get_or_create(etudiant=fiche, cours=cours, annee_academique=annee,
                                            defaults={"valeur": valeur, "evaluee_par": professeur})
            self.stdout.write(self.style.SUCCESS(f"Étudiant créé : {username} / Etudiant2026! ({fiche})"))

        self.stdout.write(self.style.SUCCESS("Données de démonstration prêtes pour tous les rôles."))
