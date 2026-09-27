from django.contrib import admin
from .models import Etudiant, Inscription, Note


@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ("matricule", "utilisateur", "filiere", "promotion", "est_actif")
    search_fields = ("matricule", "utilisateur__first_name", "utilisateur__last_name")


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "cours", "annee_academique", "date_inscription")
    list_filter = ("annee_academique", "cours")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "cours", "annee_academique", "valeur", "evaluee_par")
    list_filter = ("annee_academique", "cours")
