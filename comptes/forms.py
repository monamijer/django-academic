import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

from .models import Utilisateur

# Règles partagées avec static/js/profil.js, qui les lit via des attributs data-* :
# le navigateur ne fait que refléter ce que le serveur exige, jamais l'inverse.
TELEPHONE_CHIFFRES_MIN = 8    # ex. 79123456 (numéro local burundais)
TELEPHONE_CHIFFRES_MAX = 15   # plafond de la norme E.164
MOT_DE_PASSE_LONGUEUR_MIN = 8  # doit rester égal à MinimumLengthValidator (settings.py)

_FORMAT_TELEPHONE = re.compile(r"\+?[0-9][0-9 .\-]*")


def valider_telephone(valeur):
    """Un « + » optionnel, puis des chiffres séparés au besoin par espaces,
    points ou tirets ; entre 8 et 15 chiffres au total."""
    if not _FORMAT_TELEPHONE.fullmatch(valeur.strip()):
        raise ValidationError(
            "Chiffres, espaces, points ou tirets uniquement, avec un « + » optionnel au début."
        )
    nb_chiffres = len(re.sub(r"[^0-9]", "", valeur))
    if not TELEPHONE_CHIFFRES_MIN <= nb_chiffres <= TELEPHONE_CHIFFRES_MAX:
        raise ValidationError(
            f"Le numéro doit contenir entre {TELEPHONE_CHIFFRES_MIN} et {TELEPHONE_CHIFFRES_MAX} chiffres."
        )


class ConnexionForm(AuthenticationForm):
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )


class ProfilForm(forms.ModelForm):
    """Formulaire de libre-service : un utilisateur ne modifie que son
    téléphone, jamais son rôle, son périmètre, ni son identité officielle
    (nom, prénom, email) — celle-ci reste gérée par l'administration/le
    secrétariat, affichée ici en lecture seule pour référence."""

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
        # disabled=True (plutôt que readonly) : Django ignore toute valeur
        # postée pour ces champs et garde systématiquement la valeur en base,
        # même si quelqu'un retire l'attribut HTML depuis les outils du navigateur.
        for champ in ("first_name", "last_name", "email"):
            self.fields[champ].disabled = True
            self.fields[champ].help_text = "Géré par l'administration — non modifiable ici."

        telephone = self.fields["telephone"]
        telephone.required = True  # le modèle autorise le vide, pas ce formulaire
        telephone.label = "Téléphone"
        telephone.validators.append(valider_telephone)
        telephone.help_text = "Exemple : +257 79 123 456 (8 à 15 chiffres)."
        telephone.widget.attrs.update({
            "inputmode": "tel",
            "autocomplete": "tel",
            "data-garde-champ": "telephone",
            "data-min-chiffres": TELEPHONE_CHIFFRES_MIN,
            "data-max-chiffres": TELEPHONE_CHIFFRES_MAX,
        })


class ChangerMotDePasseForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        # Repères pour static/js/profil.js (garde du bouton d'envoi).
        self.fields["old_password"].widget.attrs["data-garde-champ"] = "ancien"
        self.fields["new_password1"].widget.attrs["data-garde-champ"] = "nouveau"
        self.fields["new_password1"].widget.attrs["data-min-longueur"] = MOT_DE_PASSE_LONGUEUR_MIN
        self.fields["new_password2"].widget.attrs["data-garde-champ"] = "confirmation"


class UtilisateurForm(forms.ModelForm):
    """Formulaire administratif complet : réservé à l'administrateur système."""

    class Meta:
        model = Utilisateur
        fields = [
            "username", "first_name", "last_name", "email", "telephone",
            "role", "faculte", "departement", "est_actif_compte",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "faculte": forms.Select(attrs={"class": "form-select"}),
            "departement": forms.Select(attrs={"class": "form-select"}),
            "est_actif_compte": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class UtilisateurCreationForm(UtilisateurForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password2 = forms.CharField(label="Confirmation", widget=forms.PasswordInput(attrs={"class": "form-control"}))

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
        return utilisateur
