import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

from academique.models import Departement, Faculte
from .models import Utilisateur

TELEPHONE_CHIFFRES_MIN = 8
TELEPHONE_CHIFFRES_MAX = 15
MOT_DE_PASSE_LONGUEUR_MIN = 8

_FORMAT_TELEPHONE = re.compile(r"\+?[0-9][0-9 .\-]*")


def valider_telephone(valeur):
    if not _FORMAT_TELEPHONE.fullmatch(valeur.strip()):
        raise ValidationError(
            "Chiffres, espaces, points ou tirets uniquement, avec un « + » optionnel au début."
        )
    nb_chiffres = len(re.sub(r"[^0-9]", "", valeur))
    if not TELEPHONE_CHIFFRES_MIN <= nb_chiffres <= TELEPHONE_CHIFFRES_MAX:
        raise ValidationError(
            f"Le numéro doit contenir entre {TELEPHONE_CHIFFRES_MIN} et {TELEPHONE_CHIFFRES_MAX} chiffres."
        )


_ADMIN_AUTOCOMPLETE = {"autocomplete": "off", "spellcheck": "false"}


class ConnexionForm(AuthenticationForm):
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={
            "class": "form-control", "autofocus": True,
            "autocomplete": "username",
        }),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            "class": "form-control", "autocomplete": "current-password",
        }),
    )


class ProfilForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ["first_name", "last_name", "email", "telephone"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for champ in ("first_name", "last_name", "email"):
            self.fields[champ].disabled = True
            self.fields[champ].help_text = "Géré par l'administration — non modifiable ici."

        telephone = self.fields["telephone"]
        telephone.required = True
        telephone.label = "Téléphone"
        telephone.validators.append(valider_telephone)
        telephone.help_text = "Exemple : +257 79 123 456 (8 à 15 chiffres)."
        telephone.widget.attrs.update({
            "inputmode": "tel", "autocomplete": "tel",
            "data-garde-champ": "telephone",
            "data-min-chiffres": TELEPHONE_CHIFFRES_MIN,
            "data-max-chiffres": TELEPHONE_CHIFFRES_MAX,
        })


class ChangerMotDePasseForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["old_password"].widget.attrs["data-garde-champ"] = "ancien"
        self.fields["new_password1"].widget.attrs["data-garde-champ"] = "nouveau"
        self.fields["new_password1"].widget.attrs["data-min-longueur"] = MOT_DE_PASSE_LONGUEUR_MIN
        self.fields["new_password2"].widget.attrs["data-garde-champ"] = "confirmation"


class UtilisateurForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = [
            "username", "first_name", "last_name", "email", "telephone",
            "role", "facultes_gerées", "departements_gérés", "est_actif_compte",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", **_ADMIN_AUTOCOMPLETE}),
            "first_name": forms.TextInput(attrs={"class": "form-control", **_ADMIN_AUTOCOMPLETE}),
            "last_name": forms.TextInput(attrs={"class": "form-control", **_ADMIN_AUTOCOMPLETE}),
            "email": forms.EmailInput(attrs={"class": "form-control", **_ADMIN_AUTOCOMPLETE}),
            "telephone": forms.TextInput(attrs={"class": "form-control", **_ADMIN_AUTOCOMPLETE}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "facultes_gerées": forms.CheckboxSelectMultiple(),
            "departements_gérés": forms.CheckboxSelectMultiple(),
            "est_actif_compte": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["facultes_gerées"].queryset = Faculte.objects.filter(est_active=True).order_by("nom")
        self.fields["departements_gérés"].queryset = Departement.objects.filter(est_actif=True).select_related("faculte").order_by("faculte__nom", "nom")
        self.fields["facultes_gerées"].required = False
        self.fields["departements_gérés"].required = False

        if "role" in self.fields:
            self.fields["role"].choices = [
                (code, label) for code, label in self.fields["role"].choices
                if code != Utilisateur.Role.ADMIN_SYSTEME
            ]

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        facs = cleaned.get("facultes_gerées") or []
        deps = cleaned.get("departements_gérés") or []

        if role == Utilisateur.Role.ADMIN_SYSTEME:
            existant = Utilisateur.objects.filter(role=Utilisateur.Role.ADMIN_SYSTEME)
            if self.instance.pk:
                existant = existant.exclude(pk=self.instance.pk)
            if existant.exists():
                raise ValidationError({
                    "role": "Un administrateur système existe déjà."
                })

        if role == Utilisateur.Role.DOYEN and not facs:
            raise ValidationError({
                "facultes_gerées": "Un Doyen doit gérer au moins une faculté."
            })
        if role in (
            Utilisateur.Role.CHEF_DEPARTEMENT,
            Utilisateur.Role.PROFESSEUR,
            Utilisateur.Role.SECRETAIRE,
        ) and not deps:
            raise ValidationError({
                "departements_gérés": "Ce rôle nécessite au moins un département."
            })

        if role == Utilisateur.Role.ETUDIANT:
            raise ValidationError({
                "role": "Utilisez le formulaire dédié « Ajouter un étudiant »."
            })
        return cleaned


class UtilisateurCreationForm(UtilisateurForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirmation",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        return cleaned

    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        utilisateur.set_password(self.cleaned_data["password1"])
        if commit:
            utilisateur.save()
            self.save_m2m()
        return utilisateur
