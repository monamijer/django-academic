from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

from academique.models import Cours, Departement, Faculte, Filiere
from comptes.forms import UtilisateurCreationForm
from comptes.models import Utilisateur

from .models import Etudiant, Inscription, Note


def _add_attr(url_name, label="Ajouter"):
    try:
        url = reverse(url_name)
    except Exception:
        url = ""
    return {"data-add-url": url, "data-add-label": label}


class EtudiantCreationForm(UtilisateurCreationForm):
    """Crée simultanément le compte Utilisateur (role=ETUDIANT) et la fiche
    Etudiant. La création est atomique.

    Cascade : faculte → departement → filiere.
    Les champs `faculte` et `departement` ne servent qu'à filtrer côté client
    (et à pré-remplir en édition), ils ne sont pas sauvegardés tels quels :
    seule `filiere` est persistée sur la fiche Etudiant.
    """

    # ─── Cascade (facultatif mais recommandé pour l'UX) ───
    faculte = forms.ModelChoiceField(
        queryset=Faculte.objects.none(),
        empty_label="— Sélectionnez une faculté —",
        required=False,
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
        required=False,
        label="Département",
        widget=forms.Select(attrs={
            "class": "form-select",
            "data-cascade": "departement",
            "data-target": "id_filiere",
        }),
    )

    # ─── Fiche étudiant ───
    matricule = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
        help_text="Identifiant unique de l'étudiant, ex: MAT-2025-042.",
    )
    filiere = forms.ModelChoiceField(
        queryset=Filiere.objects.none(),
        empty_label="— Sélectionnez une filière —",
        label="Filière",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    promotion = forms.IntegerField(
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        help_text="Année d'entrée, ex: 2024.",
    )

    class Meta(UtilisateurCreationForm.Meta):
        fields = ["username", "first_name", "last_name", "email", "telephone"]

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Champs hérités inutiles pour un étudiant
        for champ in ("role", "faculte_admin", "departement_admin", "est_actif_compte"):
            self.fields.pop(champ, None)
        # `faculte` et `departement` du parent peuvent exister si Meta a été
        # modifié ailleurs : on les écrase par nos versions cascade.
        # (Rien à pop ici : nos champs locaux ont déjà pris le dessus.)

        # ─── Périmètre ───
        if utilisateur and not utilisateur.a_acces_global:
            geres = utilisateur.departements_geres()
            facs_ids = geres.values_list("faculte_id", flat=True)
            self.fields["faculte"].queryset = (
                Faculte.objects.filter(pk__in=facs_ids, est_active=True).distinct()
            )
            self.fields["departement"].queryset = geres.filter(est_actif=True)
            self.fields["filiere"].queryset = (
                Filiere.objects.filter(departement__in=geres, est_active=True)
                .select_related("departement")
            )
        else:
            self.fields["faculte"].queryset = Faculte.objects.filter(est_active=True)
            self.fields["departement"].queryset = Departement.objects.filter(est_actif=True)
            self.fields["filiere"].queryset = (
                Filiere.objects.filter(est_active=True).select_related("departement")
            )
            self.fields["filiere"].widget.attrs.update(
                _add_attr("academique:creer_filiere", "Ajouter une filière")
            )

        # ─── Pré-remplissage en édition ───
        if self.instance and self.instance.pk and self.instance.filiere_id:
            dep = self.instance.filiere.departement
            self.fields["departement"].initial = dep.pk
            self.fields["faculte"].initial = dep.faculte_id

    def clean_matricule(self):
        matricule = self.cleaned_data["matricule"].strip()
        if Etudiant.objects.filter(matricule__iexact=matricule).exists():
            raise ValidationError("Ce matricule est déjà utilisé.")
        return matricule

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("filiere"):
            raise ValidationError({"filiere": "Vous devez choisir une filière."})
        return cleaned

    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)

        try:
            with transaction.atomic():
                utilisateur = super().save(commit=False)
                utilisateur.role = Utilisateur.Role.ETUDIANT
                utilisateur.save()
                Etudiant.objects.create(
                    utilisateur=utilisateur,
                    matricule=self.cleaned_data["matricule"],
                    filiere=self.cleaned_data["filiere"],
                    promotion=self.cleaned_data["promotion"],
                )
                return utilisateur
        except IntegrityError as exc:
            raise ValidationError(
                f"Impossible de créer l'étudiant : {exc}. "
                "Vérifiez que le matricule et le nom d'utilisateur ne sont pas déjà pris."
            )


class EtudiantForm(forms.ModelForm):
    """Formulaire d'édition d'une fiche étudiant existante (utilisé par
    modifier_etudiant). Cascade identique à la création."""

    faculte = forms.ModelChoiceField(
        queryset=Faculte.objects.none(),
        empty_label="— Sélectionnez une faculté —",
        required=False,
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
        required=False,
        label="Département",
        widget=forms.Select(attrs={
            "class": "form-select",
            "data-cascade": "departement",
            "data-target": "id_filiere",
        }),
    )

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
        self.fields["filiere"].empty_label = "— Sélectionnez une filière —"

        if utilisateur and not utilisateur.a_acces_global:
            geres = utilisateur.departements_geres()
            facs_ids = geres.values_list("faculte_id", flat=True)
            self.fields["faculte"].queryset = (
                Faculte.objects.filter(pk__in=facs_ids, est_active=True).distinct()
            )
            self.fields["departement"].queryset = geres.filter(est_actif=True)
            self.fields["filiere"].queryset = Filiere.objects.filter(
                departement__in=geres, est_active=True
            )
        else:
            self.fields["faculte"].queryset = Faculte.objects.filter(est_active=True)
            self.fields["departement"].queryset = Departement.objects.filter(est_actif=True)
            self.fields["filiere"].queryset = Filiere.objects.filter(est_active=True)

        # Pré-remplir la cascade
        if self.instance and self.instance.pk and self.instance.filiere_id:
            dep = self.instance.filiere.departement
            self.fields["departement"].initial = dep.pk
            self.fields["faculte"].initial = dep.faculte_id


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