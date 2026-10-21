from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    """Utilisateur de l'application.

    Périmètres : un utilisateur peut superviser PLUSIEURS facultés et/ou
    départements. Les anciens champs FK `faculte` / `departement` sont
    conservés pour compatibilité mais ne sont plus utilisés par l'UI ni
    par `departements_geres()`.
    """

    class Role(models.TextChoices):
        ADMIN_SYSTEME = "ADMIN_SYSTEME", "Administrateur système"
        DIRECTEUR_ACADEMIQUE = "DIRECTEUR_ACADEMIQUE", "Directeur académique"
        DOYEN = "DOYEN", "Doyen"
        CHEF_DEPARTEMENT = "CHEF_DEPARTEMENT", "Chef de département"
        PROFESSEUR = "PROFESSEUR", "Professeur"
        SECRETAIRE = "SECRETAIRE", "Secrétaire"
        ETUDIANT = "ETUDIANT", "Étudiant"

    role = models.CharField(max_length=25, choices=Role.choices, default=Role.ETUDIANT)
    telephone = models.CharField(max_length=30, blank=True)
    est_actif_compte = models.BooleanField(
        default=True, verbose_name="Compte activé",
        help_text="Décochez pour désactiver ce compte sans le supprimer."
    )

    # ─── Ancien périmètre (conservé pour compatibilité uniquement) ───
    faculte = models.ForeignKey(
        "academique.Faculte", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="doyens",
    )
    departement = models.ForeignKey(
        "academique.Departement", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="membres",
    )

    # ─── Nouveaux périmètres multi-valués ───
    facultes_gerées = models.ManyToManyField(
        "academique.Faculte", blank=True,
        related_name="utilisateurs_gerants",
        verbose_name="Facultés gérées",
        help_text="Facultés supervisées (Doyen).",
    )
    departements_gérés = models.ManyToManyField(
        "academique.Departement", blank=True,
        related_name="utilisateurs_gerants",
        verbose_name="Départements gérés",
        help_text="Départements supervisés ou enseignés "
                  "(Chef de département, Professeur, Secrétaire).",
    )

    def save(self, *args, **kwargs):
        self.is_active = self.est_actif_compte
        self.is_staff = (
            self.is_superuser
            or self.role in (self.Role.ADMIN_SYSTEME, self.Role.DIRECTEUR_ACADEMIQUE)
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def est_admin_systeme(self):
        return self.role == self.Role.ADMIN_SYSTEME or self.is_superuser

    @property
    def a_acces_global(self):
        return self.est_admin_systeme or self.role == self.Role.DIRECTEUR_ACADEMIQUE

    def departements_geres(self):
        """Queryset des départements visibles pour cet utilisateur."""
        from academique.models import Departement
        if self.a_acces_global:
            return Departement.objects.all()
        if self.role == self.Role.DOYEN:
            facs = self.facultes_gerées.all()
            if facs.exists():
                return Departement.objects.filter(faculte__in=facs)
            # fallback compat : ancien FK
            if self.faculte_id:
                return Departement.objects.filter(faculte_id=self.faculte_id)
            return Departement.objects.none()
        if self.role in (
            self.Role.CHEF_DEPARTEMENT,
            self.Role.PROFESSEUR,
            self.Role.SECRETAIRE,
        ):
            deps = self.departements_gérés.all()
            if deps.exists():
                return deps
            if self.departement_id:
                return Departement.objects.filter(pk=self.departement_id)
            return Departement.objects.none()
        return Departement.objects.none()

    def facultes_geres(self):
        """Queryset des facultés visibles pour cet utilisateur."""
        from academique.models import Faculte
        if self.a_acces_global:
            return Faculte.objects.all()
        if self.role == self.Role.DOYEN:
            facs = self.facultes_gerées.all()
            if facs.exists():
                return facs
            if self.faculte_id:
                return Faculte.objects.filter(pk=self.faculte_id)
            return Faculte.objects.none()
        return Faculte.objects.filter(
            pk__in=self.departements_geres().values_list("faculte_id", flat=True)
        ).distinct()


class JournalActivite(models.Model):
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
    type_objet = models.CharField(max_length=100, blank=True)
    objet_id = models.CharField(max_length=50, blank=True)
    objet_repr = models.CharField(max_length=255, blank=True)
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
