from django.core.management.base import BaseCommand, CommandError

from academique.models import Departement, Filiere


class Command(BaseCommand):
    help = "Crée une filière (idempotent : ne plante pas si elle existe déjà)."

    def add_arguments(self, parser):
        parser.add_argument("--code", required=True, help="Code unique, ex: MED-01")
        parser.add_argument("--nom", required=True, help="Nom complet, ex: Médecine")
        parser.add_argument("--departement", required=True, help="Code du département (ex: INFO)")
        parser.add_argument("--duree", type=int, default=3, help="Durée en années (défaut 3)")

    def handle(self, *args, **options):
        code = options["code"].strip()
        nom = options["nom"].strip()
        dep_code = options["departement"].strip()

        try:
            dept = Departement.objects.get(code=dep_code)
        except Departement.DoesNotExist:
            raise CommandError(
                f"Département « {dep_code} » introuvable. "
                f"Codes existants : {list(Departement.objects.values_list('code', flat=True))}"
            )

        filiere, created = Filiere.objects.get_or_create(
            code=code,
            defaults={"nom": nom, "departement": dept, "duree_annees": options["duree"]},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Filière créée : {filiere}"))
        else:
            self.stdout.write(self.style.WARNING(f"Filière déjà existante : {filiere}"))