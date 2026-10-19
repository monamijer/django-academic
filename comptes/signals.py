from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Utilisateur, enregistrer_activite


@receiver(user_logged_in)
def log_connexion(sender, request, user, **kwargs):
    enregistrer_activite(
        user, "CONNEXION", type_objet="Utilisateur", objet_id=user.pk,
        objet_repr=str(user), ip=request.META.get("REMOTE_ADDR")
    )


@receiver(user_logged_out)
def log_deconnexion(sender, request, user, **kwargs):
    if user:
        enregistrer_activite(
            user, "DECONNEXION", type_objet="Utilisateur", objet_id=user.pk,
            objet_repr=str(user), ip=request.META.get("REMOTE_ADDR")
        )


@receiver(post_save, sender=Utilisateur)
def creer_fiche_etudiant_si_manquante(sender, instance, created, **kwargs):
    """Filet de sécurité : toute création (ou promotion) d'un Utilisateur
    avec role=ETUDIANT doit s'accompagner d'une fiche Etudiant, même si le
    compte a été créé par un chemin qui ignore EtudiantCreationForm
    (admin Django, script, import, futur endpoint API).

    La fiche est créée avec un matricule provisoire « AUTO-xxx » et une
    filière null-able — elle est à compléter par un secrétaire.
    """
    if instance.role != Utilisateur.Role.ETUDIANT:
        return

    # Import différé pour éviter une dépendance circulaire au démarrage.
    from etudiants.models import Etudiant

    if hasattr(instance, "fiche_etudiant"):
        return  # Fiche déjà présente (créée par le form dédié).

    with transaction.atomic():
        # Matricule provisoire unique ; remplacé dès qu'un secrétaire édite.
        base = f"AUTO-{instance.pk}"
        matricule = base
        suffixe = 1
        while Etudiant.objects.filter(matricule=matricule).exists():
            suffixe += 1
            matricule = f"{base}-{suffixe}"

        # etudiants/models.py — remplace la ligne filiere = ...
        filiere = models.ForeignKey(
            Filiere, on_delete=models.PROTECT, related_name="etudiants",
            null=True, blank=True,
            help_text="Null tant qu'un secrétaire n'a pas complété la fiche provisoire."
        )

        Etudiant.objects.create(
            utilisateur=instance,
            matricule=matricule,
            filiere=filiere,  # voir note ci-dessous
            promotion = models.PositiveSmallIntegerField(
                null=True, blank=True,
                help_text="Année d'entrée, ex: 2024."
)
        )