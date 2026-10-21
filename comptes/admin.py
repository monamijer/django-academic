from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError

from .models import JournalActivite, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "email", "role", "est_actif_compte")
    list_filter = ("role", "est_actif_compte")
    search_fields = ("username", "first_name", "last_name", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Rôle académique", {
            "fields": ("role", "telephone", "est_actif_compte"),
        }),
        ("Périmètres", {
            "fields": ("facultes_gerées", "departements_gérés"),
            "description": "Uniquement pour les rôles non-étudiant.",
        }),
    )
    filter_horizontal = ("facultes_gerées", "departements_gérés")

    def save_model(self, request, obj, form, change):
        # Un seul ADMIN_SYSTEME (garde serveur, en plus de clean())
        if obj.role == Utilisateur.Role.ADMIN_SYSTEME:
            existant = Utilisateur.objects.filter(role=Utilisateur.Role.ADMIN_SYSTEME)
            if change:
                existant = existant.exclude(pk=obj.pk)
            if existant.exists():
                messages.error(
                    request,
                    "Un administrateur système existe déjà — impossible d'en créer un second.",
                )
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
