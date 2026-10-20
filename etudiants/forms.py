from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

from academique.models import Cours, Filiere
from comptes.forms import UtilisateurCreationForm
from comptes.models import Utilisateur

from .models import Etudiant, Inscription, Note


def _add_attr(url_name, label="Ajouter"):
    try:
        url = reverse(url_name)
    except Exception:
        url = ""
    return {"data-add-url": url, "data-add-label": label}


class EtudiantCreationForm(UtilisateurCreationForm):
    """Crée simultanément le compte Utilisateur (role=ETUDIANT) et la fiche
    Etudiant. La création est atomique : si la fiche échoue, le compte n'est
    pas persisté non plus."""

    matricule = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
        help_text="Identifiant unique de l'étudiant, ex: MAT-2025-042.",
    )
    filiere = forms.ModelChoiceField(
        queryset=Filiere.objects.none(),
        empty_label="— Sélectionnez une filière —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    promotion = forms.IntegerField(
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Année d'entrée, ex: 2024.",
    )

    class Meta(UtilisateurCreationForm.Meta):
        fields = ["username", "first_name", "last_name", "email", "telephone"]

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Ces champs ne font pas partie de Meta.fields, donc ils n'existent
        # déjà plus dans self.fields. On utilise .pop() défensif au cas où
        # une sous-classe réintroduirait un champ via Meta.
        for champ in ("role", "faculte", "departement", "est_actif_compte"):
            self.fields.pop(champ, None)

        filiere_field = self.fields["filiere"]
        if utilisateur and not utilisateur.a_acces_global:
            geres = utilisateur.departements_geres()
            if geres.exists():
                filiere_field.queryset = (
                    Filiere.objects
                    .filter(departement__in=geres, est_active=True)
                    .select_related("departement")
                )
            else:
                filiere_field.help_text = (
                    "Votre compte n'est rattaché à aucun département. "
                    "Contactez un administrateur."
                )
        else:
            filiere_field.queryset = (
                Filiere.objects
                .filter(est_active=True)
                .select_related("departement")
            )
            filiere_field.widget.attrs.update(_add_attr("academique:creer_filiere", "Ajouter une filière"))

    def clean_matricule(self):
        matricule = self.cleaned_data["matricule"].strip()
        if Etudiant.objects.filter(matricule__iexact=matricule).exists():
            raise ValidationError("Ce matricule est déjà utilisé.")
        return matricule

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("filiere"):
            raise ValidationError({"filiere": "Vous devez choisir une filière."})
        return cleaned

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)

        try:
            with transaction.atomic():
                utilisateur = super().save(commit=False)
                utilisateur.role = Utilisateur.Role.ETUDIANT
                utilisateur.save()
                Etudiant.objects.create(
                    utilisateur=utilisateur,
                    matricule=self.cleaned_data["matricule"],
                    filiere=self.cleaned_data["filiere"],
                    promotion=self.cleaned_data["promotion"],
                )
                return utilisateur
        except IntegrityError as exc:
            raise ValidationError(
                f"Impossible de créer l'étudiant : {exc}. "
                "Vérifiez que le matricule et le nom d'utilisateur ne sont pas déjà pris."
            )


class EtudiantForm(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = ["filiere", "promotion", "est_actif"]
        widgets = {
            "promotion": forms.NumberInput(attrs={"class": "form-control"}),
            "est_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        filiere_field = self.fields["filiere"]
        filiere_field.widget.attrs.update({"class": "form-select"})
        filiere_field.empty_label = "— Sélectionnez une filière —"

        if utilisateur and not utilisateur.a_acces_global:
            geres = utilisateur.departements_geres()
            if geres.exists():
                filiere_field.queryset = Filiere.objects.filter(departement__in=geres)
            else:
                filiere_field.queryset = Filiere.objects.none()
                filiere_field.help_text = "Aucun département rattaché à votre compte."
        else:
            filiere_field.queryset = Filiere.objects.filter(est_active=True)
            filiere_field.widget.attrs.update(_add_attr("academique:creer_filiere", "Ajouter une filière"))


class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = ["etudiant", "cours", "annee_academique"]
        widgets = {
            "etudiant": forms.Select(attrs={"class": "form-select"}),
            "cours": forms.Select(attrs={"class": "form-select"}),
            "annee_academique": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["etudiant"].empty_label = "— Sélectionnez un étudiant —"
        self.fields["cours"].empty_label = "— Sélectionnez un cours —"
        self.fields["annee_academique"].empty_label = "— Sélectionnez une année —"

        if utilisateur and not utilisateur.a_acces_global:
            departements = utilisateur.departements_geres()
            self.fields["etudiant"].queryset = Etudiant.objects.filter(
                filiere__departement__in=departements
            ).select_related("utilisateur", "filiere")
            self.fields["cours"].queryset = Cours.objects.filter(departement__in=departements)

    def clean(self):
        cleaned = super().clean()
        instance = Inscription(**{
            k: v for k, v in cleaned.items()
            if k in ["etudiant", "cours", "annee_academique"]
        })
        instance.pk = self.instance.pk
        instance.clean()
        return cleaned


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["etudiant", "cours", "annee_academique", "valeur"]
        widgets = {
            "etudiant": forms.Select(attrs={"class": "form-select"}),
            "cours": forms.Select(attrs={"class": "form-select"}),
            "annee_academique": forms.Select(attrs={"class": "form-select"}),
            "valeur": forms.NumberInput(attrs={
                "class": "form-control", "step": "0.25", "min": 0, "max": 20,
            }),
        }

    def __init__(self, *args, professeur=None, cours_fige=None, **kwargs):
        super().__init__(*args, **kwargs)
        if professeur is not None:
            cours_du_prof = professeur.cours_enseignes.all()
            self.fields["cours"].queryset = cours_du_prof
            if cours_fige is not None:
                self.fields["cours"].initial = cours_fige
                self.fields["cours"].widget = forms.HiddenInput()
                self.fields["etudiant"].queryset = Etudiant.objects.filter(
                    inscriptions__cours=cours_fige
                ).distinct()