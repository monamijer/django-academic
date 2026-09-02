from django.contrib import admin
from .models import Categorie, MouvementStock, Produit


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "couleur", "est_active")


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ("nom", "reference", "categorie", "quantite_stock", "seuil_alerte", "date_peremption", "est_actif")
    list_filter = ("categorie", "est_actif")
    search_fields = ("nom", "reference")


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ("produit", "type_mouvement", "quantite", "utilisateur", "date_mouvement")
    list_filter = ("type_mouvement",)
