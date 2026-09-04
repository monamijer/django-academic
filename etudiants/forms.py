from django import forms

from academique.models import AnneeAcademique, Cours, Filiere
from comptes.forms import UtilisateurCreationForm
from comptes.models import Utilisateur

from .models import Etudiant, Inscription, Note


class EtudiantCreationForm(UtilisateurCreationForm):
    """Crée en une fois le compte Utilisateur (role=ETUDIANT) et sa fiche Etudiant."""
    matricule = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"class": "form-control"}))
    filiere = forms.ModelChoiceField(queryset=Filiere.objects.none(), widget=forms.Select(attrs={"class": "form-select"}))
    promotion = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))

    class Meta(UtilisateurCreationForm.Meta):
        fields = ["username", "first_name", "last_name", "email", "telephone"]

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("role", None)
        self.fields.pop("faculte", None)
        self.fields.pop("departement", None)
        self.fields.pop("est_actif_compte", None)
        if utilisateur and not utilisateur.a_acces_global:
            self.fields["filiere"].queryset = Filiere.objects.filter(departement__in=utilisateur.departements_geres())
        else:
            self.fields["filiere"].queryset = Filiere.objects.all()

    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        utilisateur.role = Utilisateur.Role.ETUDIANT
        if commit:
            utilisateur.save()
            Etudiant.objects.create(
                utilisateur=utilisateur,
                matricule=self.cleaned_data["matricule"],
                filiere=self.cleaned_data["filiere"],
                promotion=self.cleaned_data["promotion"],
            )
        return utilisateur


class EtudiantForm(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = ["filiere", "promotion", "est_actif"]
        widgets = {
            "filiere": forms.Select(attrs={"class": "form-select"}),
            "promotion": forms.NumberInput(attrs={"class": "form-control"}),
            "est_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        if utilisateur and not utilisateur.a_acces_global:
            self.fields["filiere"].queryset = Filiere.objects.filter(departement__in=utilisateur.departements_geres())


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
        if utilisateur and not utilisateur.a_acces_global:
            departements = utilisateur.departements_geres()
            self.fields["etudiant"].queryset = Etudiant.objects.filter(filiere__departement__in=departements)
            self.fields["cours"].queryset = Cours.objects.filter(departement__in=departements)

    def clean(self):
        cleaned = super().clean()
        instance = Inscription(**{k: v for k, v in cleaned.items() if k in ["etudiant", "cours", "annee_academique"]})
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
            "valeur": forms.NumberInput(attrs={"class": "form-control", "step": "0.25", "min": 0, "max": 20}),
        }

    def __init__(self, *args, professeur=None, cours_fige=None, **kwargs):
        super().__init__(*args, **kwargs)
        if professeur is not None:
            cours_du_prof = professeur.cours_enseignes.all()
            self.fields["cours"].queryset = cours_du_prof
            if cours_fige is not None:
                self.fields["cours"].initial = cours_fige
                self.fields["cours"].widget = forms.HiddenInput()
                self.fields["etudiant"].queryset = Etudiant.objects.filter(inscriptions__cours=cours_fige).distinct()
