from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from academique.models import AnneeAcademique, Cours, Filiere


class Etudiant(models.Model):
    """Extension du compte Utilisateur (role=ETUDIANT) avec les informations
    propres à un étudiant : matricule, filière, promotion."""

    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="fiche_etudiant")
    matricule = models.CharField(max_length=30, unique=True)
    filiere = models.ForeignKey(Filiere, on_delete=models.PROTECT, related_name="etudiants")
    promotion = models.PositiveSmallIntegerField(help_text="Année d'entrée, ex: 2024")
    est_actif = models.BooleanField(default=True, help_text="Décochez pour désactiver sans supprimer (ex: abandon).")

    class Meta:
        ordering = ["matricule"]

    def __str__(self):
        return f"{self.utilisateur.get_full_name() or self.utilisateur.username} ({self.matricule})"

    @property
    def departement(self):
        return self.filiere.departement

    def moyenne_generale(self):
        notes = self.notes.all()
        if not notes:
            return None
        return round(sum(n.valeur for n in notes) / notes.count(), 2)

    def mention(self):
        moyenne = self.moyenne_generale()
        if moyenne is None:
            return "—"
        if moyenne >= 16:
            return "Excellent"
        if moyenne >= 14:
            return "Très bien"
        if moyenne >= 12:
            return "Bien"
        if moyenne >= 10:
            return "Passable"
        return "Insuffisant"

    @property
    def en_difficulte(self):
        """Signale un étudiant dont la moyenne passe sous le seuil de réussite."""
        moyenne = self.moyenne_generale()
        return moyenne is not None and moyenne < 10


class Inscription(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name="inscriptions")
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name="inscriptions")
    annee_academique = models.ForeignKey(AnneeAcademique, on_delete=models.PROTECT, related_name="inscriptions")
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("etudiant", "cours", "annee_academique")]
        ordering = ["-date_inscription"]

    def __str__(self):
        return f"{self.etudiant} → {self.cours} ({self.annee_academique})"

    def clean(self):
        # Empêche de dépasser la capacité maximale du cours (hors mise à jour d'une inscription existante).
        if self.cours_id and self.pk is None:
            if self.cours.places_restantes <= 0:
                raise ValidationError(f"Le cours « {self.cours} » a atteint sa capacité maximale.")


class Note(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name="notes")
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name="notes")
    annee_academique = models.ForeignKey(AnneeAcademique, on_delete=models.PROTECT, related_name="notes")
    valeur = models.DecimalField(max_digits=4, decimal_places=2, help_text="Note sur 20.")
    evaluee_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    date_evaluation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("etudiant", "cours", "annee_academique")]
        ordering = ["-date_evaluation"]

    def __str__(self):
        return f"{self.etudiant} — {self.cours} : {self.valeur}/20"
