from django import forms
from django.urls import reverse

from .models import AnneeAcademique, Cours, Departement, Faculte, Filiere


def _add_attr(url_name, label="Ajouter"):
    """Renvoie les attributs HTML du select pour afficher un bouton
    '+ Ajouter' qui pointe vers une URL RÉSOLUE (pas un nom Django)."""
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
            if geres.exists():
                dep_field.queryset = geres
            else:
                dep_field.queryset = Departement.objects.none()
                dep_field.help_text = (
                    "Votre compte n'est rattaché à aucun département. "
                    "Contactez un administrateur."
                )
        else:
            dep_field.queryset = Departement.objects.filter(est_actif=True)
            dep_field.widget.attrs.update(_add_attr("academique:creer_departement", "Ajouter un département"))


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ["departement", "nom", "code", "credits", "capacite_max", "professeurs", "est_actif"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "credits": forms.NumberInput(attrs={"class": "form-control"}),
            "capacite_max": forms.NumberInput(attrs={"class": "form-control"}),
            "professeurs": forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
            "est_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        from comptes.models import Utilisateur

        dep_field = self.fields["departement"]
        dep_field.widget.attrs.update({"class": "form-select"})
        dep_field.empty_label = "— Sélectionnez un département —"

        prof_field = self.fields["professeurs"]
        prof_field.empty_label = None
        prof_field.help_text = "Astuce : Ctrl (Cmd) pour sélectionner plusieurs professeurs."
        prof_field.queryset = Utilisateur.objects.filter(
            role__in=[
                Utilisateur.Role.PROFESSEUR,
                Utilisateur.Role.CHEF_DEPARTEMENT,
            ]
        ).order_by("last_name", "first_name")

        if utilisateur and not utilisateur.a_acces_global:
            geres = utilisateur.departements_geres()
            if geres.exists():
                dep_field.queryset = geres
                prof_field.queryset = prof_field.queryset.filter(departement__in=geres)
            else:
                dep_field.queryset = Departement.objects.none()
                dep_field.help_text = (
                    "Votre compte n'est rattaché à aucun département. "
                    "Contactez un administrateur."
                )
        else:
            dep_field.queryset = Departement.objects.filter(est_actif=True)
            dep_field.widget.attrs.update(_add_attr("academique:creer_departement", "Ajouter un département"))