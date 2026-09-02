from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.utils import timezone

from comptes.models import Utilisateur
from stock.models import Categorie, MouvementStock, Produit


class Command(BaseCommand):
    help = "Crée des groupes, des utilisateurs et des données de démonstration."

    def handle(self, *args, **options):
        # Groupe "Magasinier" = permissions limitées (pas de suppression, pas d'utilisateurs)
        groupe, _ = Group.objects.get_or_create(name="Magasinier")
        codes = [
            "add_produit", "change_produit", "view_produit",
            "add_mouvementstock", "view_mouvementstock",
            "view_categorie",
        ]
        perms = Permission.objects.filter(codename__in=codes)
        groupe.permissions.set(perms)

        if not Utilisateur.objects.filter(username="admin").exists():
            admin = Utilisateur.objects.create_superuser("admin", "admin@gestock.local", "AdminGestock2026!")
            admin.est_administrateur = True
            admin.first_name = "Alice"
            admin.last_name = "Admin"
            admin.save()
            self.stdout.write(self.style.SUCCESS("Admin créé : admin / AdminGestock2026!"))

        if not Utilisateur.objects.filter(username="magasinier").exists():
            u = Utilisateur.objects.create_user("magasinier", "magasinier@gestock.local", "Magasin2026!")
            u.first_name = "Bruno"
            u.last_name = "Magasinier"
            u.save()
            u.groups.add(groupe)
            self.stdout.write(self.style.SUCCESS("Utilisateur créé : magasinier / Magasin2026!"))

        cat_alim, _ = Categorie.objects.get_or_create(nom="Alimentation", defaults={"couleur": "#198754"})
        cat_hygiene, _ = Categorie.objects.get_or_create(nom="Hygiène", defaults={"couleur": "#0dcaf0"})
        cat_fourn, _ = Categorie.objects.get_or_create(nom="Fournitures de bureau", defaults={"couleur": "#6f42c1"})

        aujourdhui = timezone.now().date()
        produits_demo = [
            ("Riz 25kg", "ALM-001", cat_alim, "sac", 40, 10, 35000, aujourdhui + timedelta(days=200)),
            ("Huile de palme 5L", "ALM-002", cat_alim, "bidon", 6, 8, 22000, aujourdhui + timedelta(days=5)),
            ("Lait en poudre", "ALM-003", cat_alim, "boîte", 15, 10, 8000, aujourdhui - timedelta(days=3)),
            ("Savon de toilette", "HYG-001", cat_hygiene, "pièce", 120, 30, 1200, aujourdhui + timedelta(days=365)),
            ("Désinfectant 1L", "HYG-002", cat_hygiene, "bouteille", 3, 10, 4500, aujourdhui + timedelta(days=15)),
            ("Ramette papier A4", "BUR-001", cat_fourn, "ramette", 50, 15, 9000, None),
            ("Stylos bleus (boîte de 50)", "BUR-002", cat_fourn, "boîte", 8, 5, 15000, None),
        ]
        for nom, ref, cat, unite, qte, seuil, prix, peremption in produits_demo:
            Produit.objects.get_or_create(
                reference=ref,
                defaults=dict(nom=nom, categorie=cat, unite=unite, quantite_stock=qte,
                              seuil_alerte=seuil, prix_unitaire=prix, date_peremption=peremption),
            )

        for p in Produit.objects.all()[:3]:
            MouvementStock.objects.get_or_create(
                produit=p, type_mouvement=MouvementStock.Type.ENTREE, quantite=10,
                note="Approvisionnement initial",
            )

        self.stdout.write(self.style.SUCCESS("Données de démonstration prêtes."))
