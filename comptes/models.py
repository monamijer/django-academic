from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    """Utilisateur de l'application. is_admin donne toutes les autorisations,
    les autres utilisateurs sont limités par des groupes/permissions Django."""
    telephone = models.CharField(max_length=30, blank=True)
    est_administrateur = models.BooleanField(
        default=False,
        help_text="Un administrateur a toutes les autorisations, quels que soient ses groupes."
    )
    est_actif_compte = models.BooleanField(
        default=True,
        verbose_name="Compte activé",
        help_text="Décochez pour désactiver ce compte sans le supprimer."
    )

    def a_permission(self, code_permission):
        if self.est_administrateur or self.is_superuser:
            return True
        return self.has_perm(code_permission)

    def save(self, *args, **kwargs):
        # is_active piloté par est_actif_compte pour permettre la désactivation
        self.is_active = self.est_actif_compte
        if self.est_administrateur:
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username


class JournalActivite(models.Model):
    """Historique : conserve qui a fait quoi, sur quel objet, et quand."""

    class Action(models.TextChoices):
        AJOUT = "AJOUT", "Ajout"
        MODIFICATION = "MODIFICATION", "Modification"
        AFFICHAGE = "AFFICHAGE", "Affichage"
        SUPPRESSION = "SUPPRESSION", "Suppression"
        DESACTIVATION = "DESACTIVATION", "Désactivation / Réactivation"
        RECHERCHE = "RECHERCHE", "Recherche"
        CONNEXION = "CONNEXION", "Connexion"
        DECONNEXION = "DECONNEXION", "Déconnexion"
        IMPRESSION = "IMPRESSION", "Génération de rapport"

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, related_name="activites"
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    type_objet = models.CharField(max_length=100, blank=True, help_text="Ex: Produit, Utilisateur, Catégorie")
    objet_id = models.CharField(max_length=50, blank=True)
    objet_repr = models.CharField(max_length=255, blank=True, help_text="Représentation lisible de l'objet concerné")
    details = models.TextField(blank=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    horodatage = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-horodatage"]
        verbose_name = "Activité"
        verbose_name_plural = "Historique des activités"

    def __str__(self):
        return f"{self.utilisateur} — {self.get_action_display()} — {self.type_objet} ({self.horodatage:%d/%m/%Y %H:%M})"


def enregistrer_activite(utilisateur, action, type_objet="", objet_id="", objet_repr="", details="", ip=None):
    JournalActivite.objects.create(
        utilisateur=utilisateur if (utilisateur and utilisateur.is_authenticated) else None,
        action=action,
        type_objet=type_objet,
        objet_id=str(objet_id) if objet_id else "",
        objet_repr=objet_repr[:255],
        details=details,
        adresse_ip=ip,
    )
