from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

from .models import Utilisateur


class ConnexionForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={"class": "form-control"}))


class UtilisateurForm(forms.ModelForm):
    groupes = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(), required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        label="Groupes / rôles"
    )

    class Meta:
        model = Utilisateur
        fields = [
            "username", "first_name", "last_name", "email", "telephone",
            "est_administrateur", "est_actif_compte", "groupes",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "est_administrateur": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "est_actif_compte": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["groupes"].initial = self.instance.groups.all()

    def save(self, commit=True):
        utilisateur = super().save(commit=commit)
        if commit:
            utilisateur.groups.set(self.cleaned_data["groupes"])
        return utilisateur


class UtilisateurCreationForm(UserCreationForm):
    groupes = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(), required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        label="Groupes / rôles"
    )

    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ["username", "first_name", "last_name", "email", "telephone", "est_administrateur"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["username", "first_name", "last_name", "email", "telephone"]:
            self.fields[name].widget.attrs["class"] = "form-control"
        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["class"] = "form-control"
        self.fields["est_administrateur"].widget.attrs["class"] = "form-check-input"

    def save(self, commit=True):
        utilisateur = super().save(commit=commit)
        if commit:
            utilisateur.groups.set(self.cleaned_data["groupes"])
        return utilisateur
