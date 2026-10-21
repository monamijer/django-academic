from django import forms
from django.urls import reverse

from .models import AnneeAcademique, Cours, Departement, Faculte, Filiere, Niveau


def _add_attr(url_name, label="Ajouter"):
    try:
        url = reverse(url_name)
    except Exception:
        url = ""
    return {"data-add-url": url, "data-add-label": label}


class FaculteForm(forms.ModelForm):
    class Meta:
        model = Faculte
        fields = ["nom", "code", "couleur", "est_active"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "couleur": forms.TextInput(attrs={"class": "form-control form-control-color", "type": "color"}),
            "est_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class DepartementForm(forms.ModelForm):
    class Meta:
        model = Departement
        fields = ["faculte", "nom", "code", "est_actif"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "est_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        faculte_field = self.fields["faculte"]
        faculte_field.widget.attrs.update({"class": "form-select"})
        faculte_field.empty_label = "— Sélectionnez une faculté —"

        if utilisateur and not utilisateur.a_acces_global and utilisateur.faculte_id:
            faculte_field.queryset = Faculte.objects.filter(pk=utilisateur.faculte_id)
            faculte_field.initial = utilisateur.faculte_id
            faculte_field.disabled = True
        else:
            faculte_field.queryset = Faculte.objects.filter(est_active=True)
            faculte_field.widget.attrs.update(_add_attr("academique:creer_faculte", "Ajouter une faculté"))


class FiliereForm(forms.ModelForm):
    """Conservé pour compatibilité mais la filière n'apparaît plus
    dans les formulaires étudiant/cours."""
    class Meta:
        model = Filiere
        fields = ["departement", "nom", "code", "duree_annees", "est_active"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "duree_annees": forms.NumberInput(attrs={"class": "form-control"}),
            "est_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        dep_field = self.fields["departement"]
        dep_field.widget.attrs.update({"class": "form-select"})
        dep_field.empty_label = "— Sélectionnez un département —"

        if utilisateur and not utilisateur.a_acces_global:
            geres = utilisateur.departements_geres()
            dep_field.queryset = geres if geres.exists() else Departement.objects.none()
        else:
            dep_field.queryset = Departement.objects.filter(est_actif=True)


class CoursForm(forms.ModelForm):
    """Formulaire cours : un seul professeur principal sélectionnable,
    niveau parmi BAC1..MASTER2, capacité bornée."""

    professeur_principal = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="— Aucun professeur assigné —",
        label="Professeur",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Cours
        fields = [
            "departement", "nom", "code", "credits", "niveau",
            "capacite_max", "est_actif",
        ]
        widgets = {
            "departement": forms.Select(attrs={"class": "form-select"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "credits": forms.NumberInput(attrs={
                "class": "form-control", "min": 1, "max": 30, "step": 1,
            }),
            "niveau": forms.Select(attrs={"class": "form-select"}),
            "capacite_max": forms.NumberInput(attrs={
                "class": "form-control", "min": 5, "max": 500, "step": 5,
            }),
            "est_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        from comptes.models import Utilisateur

        # Département
        dep_field = self.fields["departement"]
        dep_field.empty_label = "— Sélectionnez un département —"
        if utilisateur and not utilisateur.a_acces_global:
            geres = utilisateur.departements_geres()
            dep_field.queryset = geres if geres.exists() else Departement.objects.none()
        else:
            dep_field.queryset = Departement.objects.filter(est_actif=True)
            dep_field.widget.attrs.update(_add_attr("academique:creer_departement", "Ajouter un département"))

        # Professeur (unique côté UI)
        prof_field = self.fields["professeur_principal"]
        prof_field.queryset = Utilisateur.objects.filter(
            role__in=[Utilisateur.Role.PROFESSEUR, Utilisateur.Role.CHEF_DEPARTEMENT]
        ).order_by("last_name", "first_name")

        # En édition, pré-remplir avec le premier prof actuel
        if self.instance and self.instance.pk:
            prof_field.initial = self.instance.professeurs.first()

        # Valeurs par défaut utiles
        if not self.instance or not self.instance.pk:
            self.fields["niveau"].initial = Niveau.BAC1
            self.fields["capacite_max"].initial = 60
            self.fields["credits"].initial = 3

    def save(self, commit=True):
        cours = super().save(commit=False)
        if commit:
            cours.save()
            # Resynchronise la M2M : un seul prof affiché = un seul prof en base
            prof = self.cleaned_data.get("professeur_principal")
            if prof:
                cours.professeurs.set([prof])
            else:
                cours.professeurs.clear()
        return cours
