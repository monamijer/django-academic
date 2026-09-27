from django.contrib import admin
from .models import AnneeAcademique, Cours, Departement, Faculte, Filiere


@admin.register(Faculte)
class FaculteAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "couleur", "est_active")


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "faculte", "est_actif")
    list_filter = ("faculte",)


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "departement", "duree_annees", "est_active")


@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "departement", "credits", "capacite_max", "est_actif")
    filter_horizontal = ("professeurs",)


@admin.register(AnneeAcademique)
class AnneeAcademiqueAdmin(admin.ModelAdmin):
    list_display = ("libelle", "est_courante")
