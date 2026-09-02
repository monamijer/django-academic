from django.urls import path
from . import views

app_name = "stock"

urlpatterns = [
    path("", views.tableau_bord, name="tableau_bord"),
    path("produits/", views.liste_produits, name="liste_produits"),
    path("produits/ajouter/", views.creer_produit, name="creer_produit"),
    path("produits/<int:pk>/", views.detail_produit, name="detail_produit"),
    path("produits/<int:pk>/modifier/", views.modifier_produit, name="modifier_produit"),
    path("produits/<int:pk>/activer-desactiver/", views.basculer_activation_produit, name="basculer_activation_produit"),
    path("produits/<int:pk>/supprimer/", views.supprimer_produit, name="supprimer_produit"),
    path("categories/", views.liste_categories, name="liste_categories"),
    path("categories/ajouter/", views.creer_categorie, name="creer_categorie"),
    path("categories/<int:pk>/modifier/", views.modifier_categorie, name="modifier_categorie"),
    path("mouvements/", views.liste_mouvements, name="liste_mouvements"),
    path("mouvements/ajouter/", views.enregistrer_mouvement, name="enregistrer_mouvement"),
]
