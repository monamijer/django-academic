from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    couleur = models.CharField(
        max_length=7, default="#0d6efd",
        help_text="Couleur (hex) utilisée pour repérer ce type de produit dans l'interface."
    )
    est_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Catégorie / type de produit"
        verbose_name_plural = "Catégories / types de produits"

    def __str__(self):
        return self.nom


class Produit(models.Model):
    nom = models.CharField(max_length=150)
    reference = models.CharField("Référence (SKU)", max_length=50, unique=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name="produits")
    unite = models.CharField(max_length=20, default="pièce", help_text="Ex: pièce, carton, litre, kg")
    quantite_stock = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField(default=5, help_text="En dessous de ce seuil, le produit est en alerte.")
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_peremption = models.DateField(null=True, blank=True)
    est_actif = models.BooleanField(default=True, help_text="Décochez pour désactiver sans supprimer.")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.reference})"

    def get_absolute_url(self):
        return reverse("stock:detail_produit", args=[self.pk])

    @property
    def en_alerte(self):
        return self.quantite_stock <= self.seuil_alerte

    @property
    def est_perime(self):
        return bool(self.date_peremption and self.date_peremption <= timezone.now().date())

    @property
    def bientot_perime(self):
        if not self.date_peremption:
            return False
        return timezone.now().date() < self.date_peremption <= timezone.now().date() + timedelta(days=30)


class MouvementStock(models.Model):
    class Type(models.TextChoices):
        ENTREE = "ENTREE", "Entrée"
        SORTIE = "SORTIE", "Sortie"

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="mouvements")
    type_mouvement = models.CharField(max_length=10, choices=Type.choices)
    quantite = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    date_mouvement = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date_mouvement"]

    def __str__(self):
        return f"{self.get_type_mouvement_display()} — {self.produit} ({self.quantite})"

    def save(self, *args, **kwargs):
        creation = self._state.adding
        super().save(*args, **kwargs)
        if creation:
            delta = self.quantite if self.type_mouvement == self.Type.ENTREE else -self.quantite
            Produit.objects.filter(pk=self.produit_id).update(
                quantite_stock=models.F("quantite_stock") + delta
            )
