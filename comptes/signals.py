from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import enregistrer_activite


@receiver(user_logged_in)
def log_connexion(sender, request, user, **kwargs):
    enregistrer_activite(user, "CONNEXION", "Utilisateur", user.pk, str(user), ip=request.META.get("REMOTE_ADDR"))


@receiver(user_logged_out)
def log_deconnexion(sender, request, user, **kwargs):
    if user:
        enregistrer_activite(user, "DECONNEXION", "Utilisateur", user.pk, str(user), ip=request.META.get("REMOTE_ADDR"))
