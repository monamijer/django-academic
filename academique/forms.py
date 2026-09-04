from django import forms
from .models import AnneeAcademique, Cours, Departement, Faculte, Filiere


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
            "faculte": forms.Select(attrs={"class": "form-select"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "est_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        if utilisateur and not utilisateur.a_acces_global:
            self.fields["faculte"].queryset = Faculte.objects.filter(pk=utilisateur.faculte_id)
            self.fields["faculte"].initial = utilisateur.faculte_id


class FiliereForm(forms.ModelForm):
    class Meta:
        model = Filiere
        fields = ["departement", "nom", "code", "duree_annees", "est_active"]
        widgets = {
            "departement": forms.Select(attrs={"class": "form-select"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "duree_annees": forms.NumberInput(attrs={"class": "form-control"}),
            "est_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        if utilisateur and not utilisateur.a_acces_global:
            self.fields["departement"].queryset = utilisateur.departements_geres()


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ["departement", "nom", "code", "credits", "capacite_max", "professeurs", "est_actif"]
        widgets = {
            "departement": forms.Select(attrs={"class": "form-select"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "credits": forms.NumberInput(attrs={"class": "form-control"}),
            "capacite_max": forms.NumberInput(attrs={"class": "form-control"}),
            "professeurs": forms.SelectMultiple(attrs={"class": "form-select"}),
            "est_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        if utilisateur and not utilisateur.a_acces_global:
            self.fields["departement"].queryset = utilisateur.departements_geres()
            from comptes.models import Utilisateur
            self.fields["professeurs"].queryset = Utilisateur.objects.filter(
                role=Utilisateur.Role.PROFESSEUR, departement__in=utilisateur.departements_geres()
            )
