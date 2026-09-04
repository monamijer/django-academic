from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from comptes.middleware import ip_courante, utilisateur_courant
from comptes.models import enregistrer_activite

from .models import Etudiant, Inscription, Note


def _log(sender_label):
    def handler(sender, instance, created=None, **kwargs):
        action = "SUPPRESSION" if created is None else ("AJOUT" if created else "MODIFICATION")
        enregistrer_activite(utilisateur_courant(), action, sender_label, instance.pk, str(instance), ip=ip_courante())
    return handler


for model, label in [(Etudiant, "Étudiant"), (Inscription, "Inscription"), (Note, "Note")]:
    post_save.connect(_log(label), sender=model, weak=False)
    post_delete.connect(_log(label), sender=model, weak=False)
