from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect

from .models import JournalActivite, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "email", "role", "faculte", "departement", "est_actif_compte")
    list_filter = ("role", "faculte", "departement", "est_actif_compte")
    search_fields = ("username", "first_name", "last_name", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Rôle académique", {"fields": ("role", "faculte", "departement", "telephone", "est_actif_compte")}),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        # En création, on empêche de sélectionner ETUDIANT : le rôle doit
        # être créé via etudiants:creer_etudiant pour garantir la fiche.
        if obj is None and "role" in form.base_fields:
            form.base_fields["role"].choices = [
                (v, label) for v, label in Utilisateur.Role.choices
                if v != Utilisateur.Role.ETUDIANT
            ]
        return form

    def save_model(self, request, obj, form, change):
        if not change and obj.role == Utilisateur.Role.ETUDIANT:
            messages.error(
                request,
                "Les comptes étudiants doivent être créés depuis "
                "« Étudiants → Ajouter » pour générer la fiche académique.",
            )
            # On ne persiste pas : la vue redirigera vers le bon formulaire.
            return
        super().save_model(request, obj, form, change)


@admin.register(JournalActivite)
class JournalActiviteAdmin(admin.ModelAdmin):
    list_display = ("horodatage", "utilisateur", "action", "type_objet", "objet_repr")
    list_filter = ("action", "type_objet")
    search_fields = ("objet_repr", "details")
    readonly_fields = [f.name for f in JournalActivite._meta.fields]

    def has_add_permission(self, request):
        return False