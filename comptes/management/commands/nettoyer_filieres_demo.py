from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from academique.models import Filiere
from etudiants.models import Etudiant


class Command(BaseCommand):
    help = (
        "Supprime les filières de démonstration (L-INFO, L-LET) après avoir "
        "réaffecté les étudiants qui y sont rattachés vers une filière cible."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--vers",
            type=str,
            required=True,
            help="Code de la filière cible qui recevra les étudiants réaffectés.",
        )
        parser.add_argument(
            "--codes-demo",
            type=str,
            default="L-INFO,L-LET",
            help="Codes des filières de démo à supprimer, séparés par virgule.",
        )
        parser.add_argument(
            "--supprimer-etudiants-demo",
            action="store_true",
            help="Supprime aussi les étudiants de démo (usernames etudiant1..3).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait fait sans rien modifier.",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        code_cible = options["vers"].strip()
        codes_demo = [c.strip() for c in options["codes_demo"].split(",") if c.strip()]

        # 1. Vérifier que la filière cible existe
        try:
            filiere_cible = Filiere.objects.get(code=code_cible)
        except Filiere.DoesNotExist:
            raise CommandError(
                f"La filière cible « {code_cible} » n'existe pas. "
                f"Crée-la d'abord depuis /academique/filieres/ajouter/."
            )

        self.stdout.write(
            f"Filière cible : {filiere_cible.nom} ({filiere_cible.code})"
        )

        # 2. Lister les filières de démo à supprimer
        filieres_demo = Filiere.objects.filter(code__in=codes_demo)
        if not filieres_demo.exists():
            self.stdout.write(self.style.WARNING(
                "Aucune filière de démo trouvée avec ces codes."
            ))
            return

        self.stdout.write("Filières de démo trouvées :")
        for f in filieres_demo:
            self.stdout.write(f"  - {f.nom} ({f.code})")

        if filiere_cible in filieres_demo:
            raise CommandError(
                f"La filière cible « {code_cible} » ne peut pas être "
                f"elle-même une filière de démo. Choisis une vraie filière."
            )

        # 3. Réaffecter + supprimer + optionnellement purger les étudiants
        with transaction.atomic():
            etudiants_impactes = Etudiant.objects.filter(filiere__in=filieres_demo)
            nb_impactes = etudiants_impactes.count()

            usernames_demo = {"etudiant1", "etudiant2", "etudiant3"}
            if options["supprimer_etudiants_demo"]:
                etudiants_demo_qs = etudiants_impactes.filter(
                    utilisateur__username__in=usernames_demo
                )
                nb_demo = etudiants_demo_qs.count()
                self.stdout.write(
                    f"Étudiants de démo à supprimer : {nb_demo}"
                )
                if not dry:
                    # Supprime d'abord les notes + inscriptions liées
                    etudiants_demo_qs.select_related("utilisateur").delete()
                etudiants_impactes = etudiants_impactes.exclude(
                    utilisateur__username__in=usernames_demo
                )
                nb_impactes = etudiants_impactes.count()

            self.stdout.write(
                f"Étudiants à réaffecter vers {filiere_cible.code} : {nb_impactes}"
            )
            if not dry and nb_impactes:
                etudiants_impactes.update(filiere=filiere_cible)

            self.stdout.write(f"Filières à supprimer : {filieres_demo.count()}")
            if not dry:
                filieres_demo.delete()

        if dry:
            self.stdout.write(self.style.WARNING("DRY-RUN — rien n'a été modifié."))
        else:
            self.stdout.write(self.style.SUCCESS("Opération terminée."))