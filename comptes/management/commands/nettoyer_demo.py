from django.core.management.base import BaseCommand
from django.db import transaction

from academique.models import Cours, Departement, Faculte, Filiere, Seance
from comptes.models import Utilisateur
from etudiants.models import Etudiant, Inscription, Note


class Command(BaseCommand):
    help = (
        "Supprime les données de démonstration créées par donnees_demo.py "
        "(filières L-INFO / L-LET, cours INFO-101 / INFO-201, comptes demo1, "
        "etudiant1..3, admin, directeur, doyen, chef_dept, professeur, secretaire)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait supprimé sans rien supprimer.",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]

        usernames_demo = [
            "admin", "directeur", "doyen",
            "chef_dept", "professeur", "secretaire",
            "etudiant1", "etudiant2", "etudiant3",
        ]
        codes_filieres_demo = ["L-INFO", "L-LET"]
        codes_cours_demo = ["INFO-101", "INFO-201"]
        codes_dept_demo = ["INFO", "MATH", "LM"]
        codes_fac_demo = ["FSC", "FLE"]

        with transaction.atomic():
            # 1. Notes et inscriptions liées aux étudiants de démo
            etudiants_demo = Etudiant.objects.filter(
                utilisateur__username__in=usernames_demo
            )
            notes = Note.objects.filter(etudiant__in=etudiants_demo)
            inscriptions = Inscription.objects.filter(etudiant__in=etudiants_demo)
            self._say(dry, f"Notes: {notes.count()}")
            self._say(dry, f"Inscriptions: {inscriptions.count()}")
            if not dry:
                notes.delete()
                inscriptions.delete()

            # 2. Fiches Etudiant
            self._say(dry, f"Fiches étudiant: {etudiants_demo.count()}")
            if not dry:
                etudiants_demo.delete()

            # 3. Comptes de démo (sauf superuser courant pour ne pas se
            #    verrouiller hors de l'admin)
            comptes = Utilisateur.objects.filter(
                username__in=usernames_demo
            ).exclude(is_superuser=True)
            self._say(dry, f"Comptes (hors superuser): {comptes.count()}")
            if not dry:
                comptes.delete()

            # 4. Cours de démo et leurs séances
            cours_demo = Cours.objects.filter(code__in=codes_cours_demo)
            self._say(dry, f"Cours: {cours_demo.count()}")
            if not dry:
                cours_demo.delete()

            # 5. Filières de démo
            filieres_demo = Filiere.objects.filter(code__in=codes_filieres_demo)
            self._say(dry, f"Filières: {filieres_demo.count()}")
            if not dry:
                filieres_demo.delete()

            # 6. Départements de démo (seulement s'ils n'ont plus
            #    ni filières ni cours)
            depts_demo = Departement.objects.filter(
                code__in=codes_dept_demo,
                filieres__isnull=True,
                cours__isnull=True,
            )
            self._say(dry, f"Départements orphelins: {depts_demo.count()}")
            if not dry:
                depts_demo.delete()

            # 7. Facultés de démo (seulement si plus de départements)
            facs_demo = Faculte.objects.filter(
                code__in=codes_fac_demo,
                departements__isnull=True,
            )
            self._say(dry, f"Facultés orphelines: {facs_demo.count()}")
            if not dry:
                facs_demo.delete()

        if dry:
            self.stdout.write(self.style.WARNING("DRY-RUN — rien n'a été supprimé."))
        else:
            self.stdout.write(self.style.SUCCESS("Données de démo supprimées."))

    def _say(self, dry, label):
        prefix = "[dry-run]" if dry else "[suppr]"
        self.stdout.write(f"{prefix} {label}")