from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Crée un groupe Django par rôle académique avec un jeu de permissions
    cohérent avec la matrice de rôles du projet. Ces groupes complètent
    (sans le remplacer) le filtrage par périmètre fait dans les vues :
    le groupe dit CE qu'un rôle peut faire, le périmètre dit SUR QUOI."""

    help = "Crée les groupes de permissions correspondant à chaque rôle académique."

    MATRICE = {
        "Directeur académique": [
            "view_faculte", "view_departement", "view_filiere", "view_cours",
            "view_etudiant", "view_inscription", "view_note",
        ],
        "Doyen": [
            "view_departement", "change_departement",
            "view_filiere", "add_filiere", "change_filiere",
            "view_cours", "add_cours", "change_cours",
            "view_etudiant", "view_inscription", "view_note",
        ],
        "Chef de département": [
            "view_cours", "add_cours", "change_cours",
            "view_etudiant", "add_etudiant", "change_etudiant",
            "view_inscription", "add_inscription", "change_inscription", "delete_inscription",
            "view_note",
        ],
        "Professeur": [
            "view_cours",
            "view_etudiant",
            "view_note", "add_note", "change_note",
        ],
        "Secrétaire": [
            "view_etudiant", "add_etudiant", "change_etudiant",
            "view_inscription", "add_inscription", "change_inscription",
            "view_filiere",
        ],
        "Étudiant": [
            "view_note",
        ],
    }

    def handle(self, *args, **options):
        for nom_groupe, codenames in self.MATRICE.items():
            groupe, _ = Group.objects.get_or_create(name=nom_groupe)
            permissions = Permission.objects.filter(codename__in=codenames)
            groupe.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(
                f"Groupe « {nom_groupe} » configuré avec {permissions.count()} permission(s)."
            ))
