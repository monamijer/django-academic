from django.urls import path
from . import views

app_name = "academique"

urlpatterns = [
    path("facultes/", views.liste_facultes, name="liste_facultes"),
    path("facultes/ajouter/", views.creer_faculte, name="creer_faculte"),
    path("facultes/<int:pk>/modifier/", views.modifier_faculte, name="modifier_faculte"),

    path("departements/", views.liste_departements, name="liste_departements"),
    path("departements/ajouter/", views.creer_departement, name="creer_departement"),
    path("departements/<int:pk>/modifier/", views.modifier_departement, name="modifier_departement"),

    path("filieres/", views.liste_filieres, name="liste_filieres"),
    path("filieres/ajouter/", views.creer_filiere, name="creer_filiere"),
    path("filieres/<int:pk>/modifier/", views.modifier_filiere, name="modifier_filiere"),

    path("cours/", views.liste_cours, name="liste_cours"),
    path("cours/ajouter/", views.creer_cours, name="creer_cours"),
    path("cours/<int:pk>/modifier/", views.modifier_cours, name="modifier_cours"),
]
