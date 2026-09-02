from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from comptes.middleware import utilisateur_courant, ip_courante
from comptes.models import enregistrer_activite

from .models import Categorie, MouvementStock, Produit


@receiver(post_save, sender=Produit)
def log_produit_save(sender, instance, created, **kwargs):
    enregistrer_activite(
        utilisateur_courant(), "AJOUT" if created else "MODIFICATION",
        "Produit", instance.pk, str(instance), ip=ip_courante()
    )


@receiver(post_delete, sender=Produit)
def log_produit_delete(sender, instance, **kwargs):
    enregistrer_activite(utilisateur_courant(), "SUPPRESSION", "Produit", instance.pk, str(instance), ip=ip_courante())


@receiver(post_save, sender=Categorie)
def log_categorie_save(sender, instance, created, **kwargs):
    enregistrer_activite(
        utilisateur_courant(), "AJOUT" if created else "MODIFICATION",
        "Catégorie", instance.pk, str(instance), ip=ip_courante()
    )


@receiver(post_save, sender=MouvementStock)
def log_mouvement_save(sender, instance, created, **kwargs):
    if created:
        enregistrer_activite(
            utilisateur_courant(), "AJOUT", "Mouvement de stock", instance.pk, str(instance),
            details=f"Produit: {instance.produit} | {instance.get_type_mouvement_display()}: {instance.quantite}",
            ip=ip_courante(),
        )
