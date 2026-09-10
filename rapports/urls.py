from django.urls import path
from . import views

app_name = "rapports"

urlpatterns = [
    path("", views.centre_rapports, name="centre_rapports"),
    path("mon-releve/", views.mon_releve, name="mon_releve"),
    path("releve-notes/<int:pk>/", views.releve_notes, name="releve_notes"),
    path("etudiants/", views.liste_etudiants_departement, name="liste_etudiants_departement"),
    path("personnel/", views.liste_personnel, name="liste_personnel"),
    path("cours/<int:cours_id>/performance/", views.performance_cours, name="performance_cours"),
]
