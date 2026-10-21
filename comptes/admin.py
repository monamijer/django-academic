from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import JournalActivite, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "email", "role", "est_actif_compte")
    list_filter = ("role", "est_actif_compte")
    search_fields = ("username", "first_name", "last_name", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Rôle académique", {"fields": ("role", "telephone", "est_actif_compte")}),
        ("Périmètres", {
            "fields": (
                "facultes_gerees",
                "departements_diriges",
                "departements_enseignes",
            ),
            "description": "Renseignez uniquement le périmètre correspondant au rôle.",
        }),
    )
    filter_horizontal = (
        "facultes_gerees",
        "departements_diriges",
        "departements_enseignes",
    )

    def save_model(self, request, obj, form, change):
        if obj.role == Utilisateur.Role.ADMIN_SYSTEME:
            existant = Utilisateur.objects.filter(role=Utilisateur.Role.ADMIN_SYSTEME)
            if change:
                existant = existant.exclude(pk=obj.pk)
            if existant.exists():
                messages.error(request, "Un administrateur système existe déjà.")
                return
        super().save_model(request, obj, form, change)


    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))

        if obj and obj.role == Utilisateur.Role.ADMIN_SYSTEME:
            for field in ("role", "est_actif_compte", "is_active"):
                if field not in readonly:
                    readonly.append(field)

        return readonly

    def has_delete_permission(self, request, obj=None):
        if obj and obj.role == Utilisateur.Role.ADMIN_SYSTEME:
            return False
        return super().has_delete_permission(request, obj)

    def delete_model(self, request, obj):
        if obj.role == Utilisateur.Role.ADMIN_SYSTEME:
            messages.error(
                request,
                "Le compte administrateur système ne peut pas être supprimé ici.",
            )
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        protected = queryset.filter(role=Utilisateur.Role.ADMIN_SYSTEME)
        if protected.exists():
            messages.warning(
                request,
                "Les comptes administrateur système ont été exclus de la suppression.",
            )

        queryset.exclude(role=Utilisateur.Role.ADMIN_SYSTEME).delete()

    def save_model(self, request, obj, form, change):
        if change:
            original = Utilisateur.objects.filter(pk=obj.pk).first()

            if original and original.role == Utilisateur.Role.ADMIN_SYSTEME:
                # Empêche la rétrogradation ou la désactivation de cet administrateur.
                obj.role = Utilisateur.Role.ADMIN_SYSTEME
                obj.est_actif_compte = True

        if obj.role == Utilisateur.Role.ADMIN_SYSTEME:
            existant = Utilisateur.objects.filter(
                role=Utilisateur.Role.ADMIN_SYSTEME
            )
            if change:
                existant = existant.exclude(pk=obj.pk)

            if existant.exists():
                messages.error(request, "Un administrateur système existe déjà.")
                return

            obj.est_actif_compte = True

        super().save_model(request, obj, form, change)



@admin.register(JournalActivite)
class JournalActiviteAdmin(admin.ModelAdmin):
    list_display = ("horodatage", "utilisateur", "action", "type_objet", "objet_repr")
    list_filter = ("action", "type_objet")
    search_fields = ("objet_repr", "details")
    readonly_fields = [f.name for f in JournalActivite._meta.fields]

    def has_add_permission(self, request):
        return False
