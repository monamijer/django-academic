from django.conf import settings
from django.db import models


class Faculte(models.Model):
    nom = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=15, unique=True)
    couleur = models.CharField(max_length=7, default="#0d6efd", help_text="Couleur d'identification dans l'interface.")
    est_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Departement(models.Model):
    faculte = models.ForeignKey(Faculte, on_delete=models.CASCADE, related_name="departements")
    nom = models.CharField(max_length=150)
    code = models.CharField(max_length=15, unique=True)
    est_actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]
        unique_together = [("faculte", "nom")]

    def __str__(self):
        return f"{self.nom} ({self.faculte.code})"


class Filiere(models.Model):
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name="filieres")
    nom = models.CharField(max_length=150)
    code = models.CharField(max_length=15, unique=True)
    duree_annees = models.PositiveSmallIntegerField(default=3)
    est_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class AnneeAcademique(models.Model):
    libelle = models.CharField(max_length=20, unique=True, help_text="Ex: 2025-2026")
    est_courante = models.BooleanField(default=False)

    class Meta:
        ordering = ["-libelle"]

    def __str__(self):
        return self.libelle

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.est_courante:
            AnneeAcademique.objects.exclude(pk=self.pk).update(est_courante=False)


class Cours(models.Model):
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name="cours")
    nom = models.CharField(max_length=150)
    code = models.CharField(max_length=15, unique=True)
    credits = models.PositiveSmallIntegerField(default=3)
    professeurs = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="cours_enseignes", blank=True,
        limit_choices_to={"role": "PROFESSEUR"},
    )
    capacite_max = models.PositiveIntegerField(default=60)
    est_actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.code})"

    @property
    def places_restantes(self):
        return max(self.capacite_max - self.inscriptions.count(), 0)
