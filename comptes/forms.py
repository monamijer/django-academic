from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from .models import Utilisateur


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
    """Formulaire de libre-service : un utilisateur ne modifie que ses propres
    informations personnelles, jamais son rôle ni son périmètre."""

    class Meta:
        model = Utilisateur
        fields = ["first_name", "last_name", "email", "telephone"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
        }


class ChangerMotDePasseForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


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
