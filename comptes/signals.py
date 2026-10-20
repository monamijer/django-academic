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
    """Filet de sécurité : tout Utilisateur role=ETUDIANT doit avoir une
    fiche Etudiant. Créée provisoirement si aucun autre code ne s'en charge
    (admin Django, script, import).

    Si EtudiantCreationForm crée la fiche manuellement, il pose le flag
    `_skip_etudiant_signal=True` sur l'instance AVANT save() pour que ce
    signal ne double pas la création.
    """
    if instance.role != Utilisateur.Role.ETUDIANT:
        return

    # Respecte le flag posé par EtudiantCreationForm.save().
    if getattr(instance, "_skip_etudiant_signal", False):
        return

    # Import différé pour éviter une dépendance circulaire au démarrage.
    from etudiants.models import Etudiant

    # Si une fiche existe déjà, ne rien faire (ex: instance rechargée).
    if Etudiant.objects.filter(utilisateur=instance).exists():
        return

    with transaction.atomic():
        base = f"AUTO-{instance.pk}"
        matricule = base
        suffixe = 1
        while Etudiant.objects.filter(matricule=matricule).exists():
            suffixe += 1
            matricule = f"{base}-{suffixe}"

        filiere_defaut = None
        if instance.departement_id:
            from academique.models import Filiere
            filiere_defaut = (
                Filiere.objects
                .filter(departement=instance.departement, est_active=True)
                .first()
            )

        Etudiant.objects.create(
            utilisateur=instance,
            matricule=matricule,
            filiere=filiere_defaut,
            promotion=None,
        )