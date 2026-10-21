from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from academique.models import AnneeAcademique, Cours, Departement, Faculte, Filiere
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
# GÉNÉRATEURS DE VALEURS UNIQUES (username, matricule)
# ═══════════════════════════════════════════════════════════════

def _slugify_username_part(value):
    """Transforme un prénom/nom en fragment de username :
    accents retirés, espaces → point, minuscules, caractères sûrs."""
    import re
    import unicodedata

    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9.\-]+", "", value)
    value = value.strip(".-").lower()
    return value or "user"


def generer_username(first_name, last_name):
    """Construit un username unique : prenom.nom, prenom.nom2, prenom.nom3...
    Si prénom/nom vides, retombe sur 'etudiant'."""
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


def generer_matricule():
    """Format : ETU-<annee courante>-<compteur 5 chiffres>
    Ex: ETU-2026-00001, ETU-2026-00002...
    Basé sur le plus grand matricule existant pour l'année courante."""
    annee = AnneeAcademique.courante()
    annee_label = (annee.libelle.split("-")[0] if annee else str(timezone.now().year))
    prefix = f"ETU-{annee_label}-"

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


# ═══════════════════════════════════════════════════════════════
# CRÉATION D'ÉTUDIANT
# ═══════════════════════════════════════════════════════════════

class EtudiantCreationForm(UtilisateurCreationForm):
    """Crée en une seule transaction :
    - un Utilisateur (role=ETUDIANT), username auto-généré
    - une fiche Etudiant, matricule auto-généré

    Cascade faculté → département (la filière n'est plus demandée :
    elle sera déduite automatiquement de la première filière active
    du département choisi).
    """

    # ─── Cascade ───
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

    # ─── Identité (username dérivé automatiquement) ───
    # On garde first_name, last_name, email, telephone du parent,
    # mais on retire username et on le calcule côté serveur.

    promotion = forms.IntegerField(
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Année d'entrée, ex: 2024.",
    )

    class Meta(UtilisateurCreationForm.Meta):
        # Plus de username ni de filiere dans le formulaire
        fields = ["first_name", "last_name", "email", "telephone"]

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Retirer les champs hérités inutiles
        for champ in (
            "username", "role", "faculte_admin", "departement_admin",
            "est_actif_compte", "filiere",
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

        # Pré-remplissage à l'édition
        if self.instance and self.instance.pk and self.instance.filiere_id:
            dep = self.instance.filiere.departement
            self.fields["departement"].initial = dep.pk
            self.fields["faculte"].initial = dep.faculte_id

    def clean(self):
        cleaned = super().clean()
        # Cohérence faculté ↔ département
        faculte = cleaned.get("faculte")
        departement = cleaned.get("departement")
        if faculte and departement and departement.faculte_id != faculte.pk:
            raise ValidationError({
                "departement": "Ce département n'appartient pas à la faculté choisie."
            })

        # Vérifie qu'il existe au moins une filière active pour ce département
        if departement and not Filiere.objects.filter(
            departement=departement, est_active=True
        ).exists():
            raise ValidationError({
                "departement": (
                    f"Le département « {departement.nom} » n'a aucune filière active. "
                    "Créez-en une avant d'inscrire un étudiant."
                )
            })
        return cleaned

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)

        first_name = self.cleaned_data.get("first_name", "").strip()
        last_name = self.cleaned_data.get("last_name", "").strip()
        departement = self.cleaned_data["departement"]

        # Filière par défaut = première filière active du département
        filiere_defaut = (
            Filiere.objects.filter(departement=departement, est_active=True)
            .order_by("nom")
            .first()
        )
        if filiere_defaut is None:
            raise ValidationError(
                "Impossible de créer l'étudiant : aucune filière active "
                f"n'existe dans le département « {departement.nom} »."
            )

        try:
            with transaction.atomic():
                # 1. Créer l'utilisateur avec username auto-généré
                utilisateur = super().save(commit=False)
                utilisateur.username = generer_username(first_name, last_name)
                utilisateur.role = Utilisateur.Role.ETUDIANT
                utilisateur.save()

                # 2. Créer la fiche Etudiant avec matricule auto-généré
                Etudiant.objects.create(
                    utilisateur=utilisateur,
                    matricule=generer_matricule(),
                    filiere=filiere_defaut,
                    promotion=self.cleaned_data["promotion"],
                )
                return utilisateur
        except IntegrityError as exc:
            raise ValidationError(
                f"Impossible de créer l'étudiant : {exc}. "
                "Vérifiez l'email et réessayez."
            )


# ═══════════════════════════════════════════════════════════════
# ÉDITION D'UNE FICHE EXISTANTE
# ═══════════════════════════════════════════════════════════════

class EtudiantForm(forms.ModelForm):
    """Édition : cascade faculté → département (filière déduite automatiquement)."""

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
        fields = ["promotion", "est_actif"]
        widgets = {
            "promotion": forms.NumberInput(attrs={"class": "form-control"}),
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
        if departement and not Filiere.objects.filter(
            departement=departement, est_active=True
        ).exists():
            raise ValidationError({
                "departement": (
                    f"Le département « {departement.nom} » n'a aucune filière active."
                )
            })
        return cleaned

    def save(self, commit=True):
        etudiant = super().save(commit=False)
        departement = self.cleaned_data["departement"]

        filiere_defaut = (
            Filiere.objects.filter(departement=departement, est_active=True)
            .order_by("nom").first()
        )
        if filiere_defaut is None:
            raise ValidationError(
                "Aucune filière active dans le département choisi."
            )
        etudiant.filiere = filiere_defaut

        if commit:
            etudiant.save()
        return etudiant


# ═══════════════════════════════════════════════════════════════
# INSCRIPTIONS ET NOTES (inchangés)
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
