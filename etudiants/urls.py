from django.urls import path
from . import views

app_name = "etudiants"

urlpatterns = [
    path("", views.liste_etudiants, name="liste_etudiants"),
    path("ajouter/", views.creer_etudiant, name="creer_etudiant"),
    path("<int:pk>/", views.detail_etudiant, name="detail_etudiant"),
    path("<int:pk>/modifier/", views.modifier_etudiant, name="modifier_etudiant"),
    path("<int:pk>/activer-desactiver/", views.basculer_activation_etudiant, name="basculer_activation_etudiant"),

    path("inscriptions/", views.liste_inscriptions, name="liste_inscriptions"),
    path("inscriptions/ajouter/", views.creer_inscription, name="creer_inscription"),

    path("mes-cours/", views.mes_cours, name="mes_cours"),
    path("cours/<int:cours_id>/notes/", views.notes_cours, name="notes_cours"),
    path("cours/<int:cours_id>/notes/saisir/", views.saisir_note, name="saisir_note"),
]
