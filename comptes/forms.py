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

# ─── Quels rôles utilisent quels périmètres ───
ROLES_AVEC_FACULTES = {Utilisateur.Role.DOYEN}
ROLES_AVEC_DEPARTEMENTS = {
    Utilisateur.Role.CHEF_DEPARTEMENT,
    Utilisateur.Role.PROFESSEUR,
    Utilisateur.Role.SECRETAIRE,
}


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
            "role": forms.Select(attrs={"class": "form-select", "id": "id_role"}),
            "facultes_gerées": forms.CheckboxSelectMultiple(),
            "departements_gérés": forms.CheckboxSelectMultiple(),
            "est_actif_compte": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["facultes_gerées"].queryset = (
            Faculte.objects.filter(est_active=True).order_by("nom")
        )
        self.fields["departements_gérés"].queryset = (
            Departement.objects.filter(est_actif=True)
            .select_related("faculte").order_by("faculte__nom", "nom")
        )
        self.fields["facultes_gerées"].required = False
        self.fields["departements_gérés"].required = False

        # Masque ADMIN_SYSTEME (rôle unique, créé via createsuperuser)
        self.fields["role"].choices = [
            (code, label) for code, label in self.fields["role"].choices
            if code != Utilisateur.Role.ADMIN_SYSTEME
        ]

        # Rôle courant : instance en édition, sinon premier choix
        role_actif = (
            self.instance.role
            if self.instance and self.instance.pk
            else self.fields["role"].choices[0][0]
        )

        # Si l'instance est un étudiant : le formulaire ne doit pas être utilisé
        # (la vue creer/modifier doit rediriger en amont), mais on s'assure
        # que l'UI ne casse pas : on enlève les périmètres.
        if role_actif == Utilisateur.Role.ETUDIANT:
            self.fields["role"].choices = [
                (code, label) for code, label in self.fields["role"].choices
                if code != Utilisateur.Role.ETUDIANT
            ]

        # Pré-remplissage M2M en édition
        if self.instance and self.instance.pk:
            if self.instance.facultes_gerées.exists():
                self.fields["facultes_gerées"].initial = (
                    self.instance.facultes_gerées.values_list("pk", flat=True)
                )
            elif self.instance.faculte_id:
                self.fields["facultes_gerées"].initial = [self.instance.faculte_id]

            if self.instance.departements_gérés.exists():
                self.fields["departements_gérés"].initial = (
                    self.instance.departements_gérés.values_list("pk", flat=True)
                )
            elif self.instance.departement_id:
                self.fields["departements_gérés"].initial = [self.instance.departement_id]

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        facs = cleaned.get("facultes_gerées") or []
        deps = cleaned.get("departements_gérés") or []

        # Un seul ADMIN_SYSTEME au monde
        if role == Utilisateur.Role.ADMIN_SYSTEME:
            existant = Utilisateur.objects.filter(role=Utilisateur.Role.ADMIN_SYSTEME)
            if self.instance.pk:
                existant = existant.exclude(pk=self.instance.pk)
            if existant.exists():
                raise ValidationError({
                    "role": "Un administrateur système existe déjà."
                })

        # Interdiction de créer un ETUDIANT ici
        if role == Utilisateur.Role.ETUDIANT:
            raise ValidationError({
                "role": "Les comptes étudiants doivent être créés via "
                        "« Étudiants → Ajouter » pour générer la fiche académique."
            })

        # Périmètres obligatoires par rôle
        if role in ROLES_AVEC_FACULTES and not facs:
            raise ValidationError({
                "facultes_gerées": "Un Doyen doit gérer au moins une faculté."
            })
        if role in ROLES_AVEC_DEPARTEMENTS and not deps:
            raise ValidationError({
                "departements_gérés": "Ce rôle nécessite au moins un département."
            })

        # Nettoyage : un rôle qui n'utilise pas un périmètre ne doit pas le conserver
        if role not in ROLES_AVEC_FACULTES and facs:
            cleaned["facultes_gerées"] = Faculte.objects.none()
        if role not in ROLES_AVEC_DEPARTEMENTS and deps:
            cleaned["departements_gérés"] = Departement.objects.none()

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
