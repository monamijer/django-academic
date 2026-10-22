from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
import re
import unicodedata

from academique.models import AnneeAcademique, Cours, Departement, Faculte, Filiere, Niveau
from comptes.forms import UtilisateurCreationForm
from comptes.models import Utilisateur

from .models import Etudiant, Inscription, Note


def _add_attr(url_name, label="Ajouter"):
    try:
        url = reverse(url_name)
    except Exception:
        url = ""
    return {"data-add-url": url, "data-add-label": label}


# ═══════════════════════════════════════════════════════════════
# Générateurs (username + matricule)
# ═══════════════════════════════════════════════════════════════

def _slugify_username_part(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9.\-]+", "", value)
    return value.strip(".-").lower() or "user"


def generer_username(first_name, last_name):
    prenom = _slugify_username_part(first_name)
    nom = _slugify_username_part(last_name)
    base = f"{prenom}.{nom}" if (prenom != "user" or nom != "user") else "etudiant"
    base = base.strip(".-") or "etudiant"
    username = base
    suffixe = 1
    while Utilisateur.objects.filter(username=username).exists():
        suffixe += 1
        username = f"{base}{suffixe}"
    return username


def _annee_prefix():
    annee = AnneeAcademique.courante()
    return annee.libelle.split("-")[0] if annee else str(timezone.now().year)


def generer_matricule():
    prefix = f"ETU-{_annee_prefix()}-"
    dernier = (
        Etudiant.objects
        .filter(matricule__startswith=prefix)
        .order_by("-matricule")
        .values_list("matricule", flat=True)
        .first()
    )
    if dernier:
        try:
            numero = int(dernier.split("-")[-1]) + 1
        except (ValueError, IndexError):
            numero = 1
    else:
        numero = 1
    return f"{prefix}{numero:05d}"


def _filiere_pour_departement(departement):
    """Retourne la filière à utiliser pour un département.
    Si aucune filière active n'existe, en crée une 'Général' automatiquement.
    Ainsi l'étudiant peut toujours être créé — la notion de filière reste
    en base pour compatibilité mais n'est plus demandée à l'utilisateur."""
    filiere = (
        Filiere.objects.filter(departement=departement, est_active=True)
        .order_by("nom").first()
    )
    if filiere:
        return filiere

    # Création automatique d'une filière générique
    code_base = f"GEN-{departement.code}"
    code = code_base
    suffixe = 1
    while Filiere.objects.filter(code=code).exists():
        suffixe += 1
        code = f"{code_base}-{suffixe}"

    return Filiere.objects.create(
        departement=departement,
        nom=f"Général — {departement.nom}",
        code=code,
        duree_annees=3,
        est_active=True,
    )


# ═══════════════════════════════════════════════════════════════
# Création
# ═══════════════════════════════════════════════════════════════

class EtudiantCreationForm(UtilisateurCreationForm):
    """Création : l'utilisateur choisit Faculté → Département.
    La filière est résolue automatiquement (créée si absente).
    Username et matricule sont auto-générés, invisibles."""

    faculte = forms.ModelChoiceField(
        queryset=Faculte.objects.none(),
        empty_label="— Sélectionnez une faculté —",
        required=True,
        label="Faculté",
        widget=forms.Select(attrs={
            "class": "form-select",
            "data-cascade": "faculte",
            "data-target": "id_departement",
        }),
    )
    departement = forms.ModelChoiceField(
        queryset=Departement.objects.none(),
        empty_label="— Sélectionnez un département —",
        required=True,
        label="Département",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    promotion = forms.IntegerField(
        min_value=2020,
        max_value=2026,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Année d'entrée (2020 à 2026).",
    )
    niveau = forms.ChoiceField(
        choices=Niveau.choices,
        initial=Niveau.BAC1,
        label="Niveau d'études",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta(UtilisateurCreationForm.Meta):
        fields = ["first_name", "last_name", "email", "telephone"]

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Retirer les champs hérités inutiles
        for champ in (
            "username", "role", "faculte_admin", "departement_admin",
            "est_actif_compte", "filiere", "matricule",
        ):
            self.fields.pop(champ, None)

        # Périmètre
        if utilisateur and not utilisateur.a_acces_global:
            geres = utilisateur.departements_geres()
            facs_ids = geres.values_list("faculte_id", flat=True)
            self.fields["faculte"].queryset = (
                Faculte.objects.filter(pk__in=facs_ids, est_active=True).distinct()
            )
            self.fields["departement"].queryset = geres.filter(est_actif=True)
        else:
            self.fields["faculte"].queryset = Faculte.objects.filter(est_active=True)
            self.fields["departement"].queryset = Departement.objects.filter(est_actif=True)
            self.fields["departement"].widget.attrs.update(
                _add_attr("academique:creer_departement", "Ajouter un département")
            )
            self.fields["faculte"].widget.attrs.update(
                _add_attr("academique:creer_faculte", "Ajouter une faculté")
            )

        # Pré-remplissage édition
        if self.instance and self.instance.pk and self.instance.filiere_id:
            dep = self.instance.filiere.departement
            self.fields["departement"].initial = dep.pk
            self.fields["faculte"].initial = dep.faculte_id

    def clean(self):
        cleaned = super().clean()
        faculte = cleaned.get("faculte")
        departement = cleaned.get("departement")
        if faculte and departement and departement.faculte_id != faculte.pk:
            raise ValidationError({
                "departement": "Ce département n'appartient pas à la faculté choisie."
            })
        return cleaned

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)

        first_name = self.cleaned_data.get("first_name", "").strip()
        last_name = self.cleaned_data.get("last_name", "").strip()
        departement = self.cleaned_data["departement"]

        try:
            with transaction.atomic():
                # Filière auto-créée si absente
                filiere = _filiere_pour_departement(departement)

                utilisateur = super().save(commit=False)
                utilisateur.username = generer_username(first_name, last_name)
                utilisateur.role = Utilisateur.Role.ETUDIANT
                # On indique au signal post_save de NE PAS créer de fiche :
                # c'est cette méthode qui s'en charge juste après.
                utilisateur._skip_etudiant_signal = True
                utilisateur.save()

                Etudiant.objects.create(
                    utilisateur=utilisateur,
                    matricule=generer_matricule(),
                    filiere=filiere,
                    niveau=self.cleaned_data["niveau"],
                    promotion=self.cleaned_data["promotion"],
                )
                return utilisateur
        except IntegrityError as exc:
            raise ValidationError(
                f"Impossible de créer l'étudiant : {exc}. "
                "Vérifiez l'email et réessayez."
            )


# ═══════════════════════════════════════════════════════════════
# Édition
# ═══════════════════════════════════════════════════════════════

class EtudiantForm(forms.ModelForm):
    username = forms.CharField(
        required=False,
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "readonly": "readonly",
            "style": "background:#F7F8FA;",
        }),
        help_text="Identifiant de connexion — non modifiable.",
    )
    matricule = forms.CharField(
        required=False,
        label="Matricule",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "readonly": "readonly",
            "style": "background:#F7F8FA;",
        }),
    )
    faculte = forms.ModelChoiceField(
        queryset=Faculte.objects.none(),
        empty_label="— Sélectionnez une faculté —",
        required=True,
        label="Faculté",
        widget=forms.Select(attrs={
            "class": "form-select",
            "data-cascade": "faculte",
            "data-target": "id_departement",
        }),
    )
    departement = forms.ModelChoiceField(
        queryset=Departement.objects.none(),
        empty_label="— Sélectionnez un département —",
        required=True,
        label="Département",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Etudiant
        fields = ["niveau", "promotion", "est_actif"]
        widgets = {
            "niveau": forms.Select(attrs={"class": "form-select"}),
            "promotion": forms.NumberInput(attrs={
                "class": "form-control", "min": 2020, "max": 2026,
            }),
            "est_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)

        if utilisateur and not utilisateur.a_acces_global:
            geres = utilisateur.departements_geres()
            facs_ids = geres.values_list("faculte_id", flat=True)
            self.fields["faculte"].queryset = (
                Faculte.objects.filter(pk__in=facs_ids, est_active=True).distinct()
            )
            self.fields["departement"].queryset = geres.filter(est_actif=True)
        else:
            self.fields["faculte"].queryset = Faculte.objects.filter(est_active=True)
            self.fields["departement"].queryset = Departement.objects.filter(est_actif=True)
            self.fields["departement"].widget.attrs.update(
                _add_attr("academique:creer_departement", "Ajouter un département")
            )
            self.fields["faculte"].widget.attrs.update(
                _add_attr("academique:creer_faculte", "Ajouter une faculté")
            )

        if self.instance and self.instance.pk:
            self.fields["username"].initial = self.instance.utilisateur.username
            self.fields["matricule"].initial = self.instance.matricule
        if self.instance and self.instance.pk and self.instance.filiere_id:
            dep = self.instance.filiere.departement
            self.fields["departement"].initial = dep.pk
            self.fields["faculte"].initial = dep.faculte_id
            self.fields["departement"].widget.attrs["data-initial"] = str(dep.pk)

    def clean(self):
        cleaned = super().clean()
        faculte = cleaned.get("faculte")
        departement = cleaned.get("departement")
        if faculte and departement and departement.faculte_id != faculte.pk:
            raise ValidationError({
                "departement": "Ce département n'appartient pas à la faculté choisie."
            })
        return cleaned

    def save(self, commit=True):
        etudiant = super().save(commit=False)
        departement = self.cleaned_data["departement"]
        etudiant.filiere = _filiere_pour_departement(departement)
        if commit:
            etudiant.save()
        return etudiant


# ═══════════════════════════════════════════════════════════════
# Inscriptions et notes
# ═══════════════════════════════════════════════════════════════

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
            self.fields["cours"].queryset = professeur.cours_enseignes.all()
            if cours_fige is not None:
                self.fields["cours"].initial = cours_fige
                self.fields["cours"].widget = forms.HiddenInput()
                self.fields["etudiant"].queryset = Etudiant.objects.filter(
                    inscriptions__cours=cours_fige
                ).distinct()
