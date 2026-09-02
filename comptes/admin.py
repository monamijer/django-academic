from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import JournalActivite, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "email", "est_administrateur", "est_actif_compte", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Rôles GESTOCK", {"fields": ("telephone", "est_administrateur", "est_actif_compte")}),
    )


@admin.register(JournalActivite)
class JournalActiviteAdmin(admin.ModelAdmin):
    list_display = ("horodatage", "utilisateur", "action", "type_objet", "objet_repr")
    list_filter = ("action", "type_objet")
    search_fields = ("objet_repr", "details")
    readonly_fields = [f.name for f in JournalActivite._meta.fields]

    def has_add_permission(self, request):
        return False
