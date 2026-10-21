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


def _creer_fiche_provisoire(instance):
    """Crée une fiche Etudiant provisoire si elle n'existe pas déjà.
    Exécutée APRÈS le commit de la transaction courante."""
    from etudiants.models import Etudiant

    # Re-vérifie au moment du commit : si le form a déjà créé la fiche,
    # on ne fait rien.
    if Etudiant.objects.filter(utilisateur=instance).exists():
        return

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


@receiver(post_save, sender=Utilisateur)
def creer_fiche_etudiant_si_manquante(sender, instance, created, **kwargs):
    """Crée une fiche Etudiant provisoire pour tout Utilisateur
    role=ETUDIANT créé en dehors du formulaire dédié.

    On diffère la création à `transaction.on_commit` : quand le formulaire
    EtudiantCreationForm est utilisé, sa propre transaction inclut la
    création de la fiche, donc au moment du commit, la fiche existe déjà
    et on ne fait rien.
    """
    if not created:
        return
    if instance.role != Utilisateur.Role.ETUDIANT:
        return

    transaction.on_commit(lambda: _creer_fiche_provisoire(instance))