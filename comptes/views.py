from datetime import timedelta
from functools import wraps
from django.db.models import Q

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView

from academique.models import AnneeAcademique, Cours, Departement, Faculte, Seance
from etudiants.models import Etudiant, Note

from .forms import ChangerMotDePasseForm, ConnexionForm, ProfilForm, UtilisateurCreationForm, UtilisateurForm
from .models import JournalActivite, Utilisateur, enregistrer_activite


def est_admin_systeme(user):
    return user.is_authenticated and user.est_admin_systeme


def exiger_admin_systeme(vue):
    """Comme @user_passes_test, mais redirige un utilisateur déjà connecté vers
    son tableau de bord (avec un message) plutôt que vers la page de connexion.
    Passer par LOGIN_URL bouclerait indéfiniment : redirect_authenticated_user
    sur la vue de connexion renverrait l'utilisateur droit vers la page bloquée."""
    @wraps(vue)
    def wrapper(request, *args, **kwargs):
        if not est_admin_systeme(request.user):
            messages.error(request, "Accès réservé à l'administrateur système.")
            return redirect("comptes:tableau_bord")
        return vue(request, *args, **kwargs)
    return login_required(wrapper)


class ConnexionView(auth_views.LoginView):
    template_name = "comptes/connexion.html"
    authentication_form = ConnexionForm
    redirect_authenticated_user = True


class DeconnexionView(auth_views.LogoutView):
    next_page = "comptes:connexion"


SEUIL_REUSSITE = 10
JOURS_AFFICHES = 6  # lundi -> samedi


def _contexte_etudiant(utilisateur):
    """Données du tableau de bord étudiant : identité, semaine en cours
    (séances des cours auxquels il est inscrit cette année) et dernières notes."""
    fiche = getattr(utilisateur, "fiche_etudiant", None)
    if fiche is None:
        return {"fiche": None}

    aujourdhui = timezone.localdate()
    lundi = aujourdhui - timedelta(days=aujourdhui.weekday())
    annee = AnneeAcademique.objects.filter(est_courante=True).first()

    seances = Seance.objects.none()
    if annee:
        # Un seul filter() : les deux conditions portent sur la MEME inscription.
        seances = (Seance.objects
                   .filter(cours__inscriptions__etudiant=fiche,
                           cours__inscriptions__annee_academique=annee)
                   .select_related("cours").distinct())

    semaine = []
    for indice in range(JOURS_AFFICHES):
        date_jour = lundi + timedelta(days=indice)
        semaine.append({
            "date": date_jour,
            "libelle": Seance.Jour(indice).label,
            "est_aujourdhui": date_jour == aujourdhui,
            "seances": [s for s in seances if s.jour == indice],
        })

    notes = list(fiche.notes.select_related("cours", "annee_academique")
                 .order_by("-date_evaluation")[:8])
    for note in notes:
        note.insuffisante = note.valeur < SEUIL_REUSSITE

    return {
        "fiche": fiche,
        "annee": annee,
        "aujourdhui": aujourdhui,
        "semaine": semaine,
        "nb_seances": sum(len(j["seances"]) for j in semaine),
        "notes": notes,
        "moyenne": fiche.moyenne_generale(),
        "mention": fiche.mention(),
        "seuil": SEUIL_REUSSITE,
    }

def _contexte_professeur(utilisateur):
    """Données du gradebook : un professeur ne gère que ses propres cours,
    chacun avec son effectif réel et un aperçu des étudiants inscrits."""
    cours_qs = (utilisateur.cours_enseignes.filter(est_actif=True)
                .select_related("departement")
                .prefetch_related("inscriptions__etudiant__utilisateur"))

    lignes = []
    for cours in cours_qs:
        inscriptions = list(cours.inscriptions.select_related("etudiant__utilisateur")
                            .order_by("etudiant__matricule")[:5])
        nb_inscrits = cours.inscriptions.count()
        lignes.append({
            "cours": cours,
            "nb_inscrits": nb_inscrits,
            "nb_notes": cours.notes.count(),
            "apercu": inscriptions,
            "nb_restants": max(nb_inscrits - len(inscriptions), 0),
        })

    return {
        "lignes_cours": lignes,
        "nb_cours": len(lignes),
        "nb_etudiants_total": Etudiant.objects.filter(inscriptions__cours__in=cours_qs).distinct().count(),
    }

@login_required
def tableau_bord(request):
    """Un seul point d'entrée après connexion ; le contenu affiché dépend du
    rôle, chacun ne voyant que les indicateurs de son périmètre."""
    u = request.user
    contexte = {"role_label": u.get_role_display()}

    if u.a_acces_global:
        contexte.update({
            "nb_facultes": Faculte.objects.filter(est_active=True).count(),
            "nb_departements": Departement.objects.filter(est_actif=True).count(),
            "nb_etudiants": Etudiant.objects.filter(est_actif=True).count(),
            "nb_personnel": Utilisateur.objects.exclude(role=Utilisateur.Role.ETUDIANT).count(),
            "activites_recentes": JournalActivite.objects.select_related("utilisateur")[:6],
        })
        template = "comptes/tableau_bord_direction.html"

    elif u.role == Utilisateur.Role.DOYEN:
        departements = u.departements_geres()
        contexte.update({
            "facultes_liste": u.facultes_geres(),
            "departements_liste": departements,
            "nb_departements": departements.count(),
            "nb_etudiants": Etudiant.objects.filter(filiere__departement__in=departements, est_actif=True).count(),
            "nb_cours": Cours.objects.filter(departement__in=departements, est_actif=True).count(),
        })
        template = "comptes/tableau_bord_doyen.html"

    elif u.role == Utilisateur.Role.CHEF_DEPARTEMENT:
        departements = u.departements_geres()
        etudiants = Etudiant.objects.filter(filiere__departement__in=departements, est_actif=True)
        contexte.update({
            "departements_liste": u.departements_geres(),
            "nb_etudiants": etudiants.count(),
            "nb_cours": Cours.objects.filter(departement__in=departements, est_actif=True).count(),
            "etudiants_en_difficulte": [e for e in etudiants if e.en_difficulte][:8],
        })
        template = "comptes/tableau_bord_chef_departement.html"

    elif u.role == Utilisateur.Role.PROFESSEUR:
        contexte.update(_contexte_professeur(u))
        template = "comptes/tableau_bord_professeur.html"


    elif u.role == Utilisateur.Role.SECRETAIRE:
        departements = u.departements_geres()
        etudiants_dept = Etudiant.objects.filter(filiere__departement__in=departements)
        contexte.update({
            "departements_liste": u.departements_geres(),
            "nb_etudiants": etudiants_dept.count(),
            "derniers_etudiants": etudiants_dept.select_related("utilisateur", "filiere").order_by("-pk")[:6],
        })
        template = "comptes/tableau_bord_secretaire.html"

    elif u.role == Utilisateur.Role.ETUDIANT:
        contexte.update(_contexte_etudiant(u))
        template = "comptes/tableau_bord_etudiant.html"

    else:
        template = "comptes/tableau_bord_direction.html"

    return render(request, template, contexte)


@login_required
def mon_profil(request):
    if request.method == "POST" and request.POST.get("form") == "infos":
        form = ProfilForm(request.POST, instance=request.user)
        mdp_form = ChangerMotDePasseForm(request.user)
        if form.is_valid():
            form.save()
            enregistrer_activite(request.user, "MODIFICATION", "Profil", request.user.pk, str(request.user),
                                  details="Mise à jour des informations personnelles")
            messages.success(request, "Vos informations ont été mises à jour.")
            return redirect("comptes:mon_profil")
    elif request.method == "POST" and request.POST.get("form") == "mot_de_passe":
        form = ProfilForm(instance=request.user)
        mdp_form = ChangerMotDePasseForm(request.user, request.POST)
        if mdp_form.is_valid():
            utilisateur = mdp_form.save()
            update_session_auth_hash(request, utilisateur)
            enregistrer_activite(request.user, "MODIFICATION", "Profil", request.user.pk, str(request.user),
                                  details="Changement de mot de passe")
            messages.success(request, "Mot de passe modifié avec succès.")
            return redirect("comptes:mon_profil")
    else:
        form = ProfilForm(instance=request.user)
        mdp_form = ChangerMotDePasseForm(request.user)

    return render(request, "comptes/mon_profil.html", {"form": form, "mdp_form": mdp_form})


# --- Gestion administrative des comptes (réservée à l'administrateur système) ---

@exiger_admin_systeme
def liste_utilisateurs(request):
    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "")
    utilisateurs = Utilisateur.objects.all().order_by("role", "username")
    if q:
        utilisateurs = utilisateurs.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )
        enregistrer_activite(request.user, "RECHERCHE", "Utilisateur", details=f"Recherche: '{q}'")
    if role:
        utilisateurs = utilisateurs.filter(role=role)
    return render(request, "comptes/liste_utilisateurs.html", {
        "utilisateurs": utilisateurs, "q": q, "role": role, "roles": Utilisateur.Role.choices,
    })

@exiger_admin_systeme
def creer_utilisateur(request):
    if request.method == "POST":
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            role_choisi = form.cleaned_data.get("role")
            if role_choisi == Utilisateur.Role.ETUDIANT:
                messages.info(
                    request,
                    "Pour créer un compte étudiant, utilisez le formulaire « Ajouter un étudiant » "
                    "afin que la fiche académique (matricule, filière, promotion) soit créée en même temps.",
                )
                return redirect("etudiants:creer_etudiant")
            u = form.save()
            enregistrer_activite(request.user, "AJOUT", "Utilisateur", u.pk, str(u))
            messages.success(request, f"Compte « {u} » créé.")
            return redirect("comptes:liste_utilisateurs")
    else:
        form = UtilisateurCreationForm()
    return render(request, "comptes/formulaire_utilisateur.html", {
        "form": form, "titre": "Ajouter un compte", "creation": True,
    })



@exiger_admin_systeme
def modifier_utilisateur(request, pk):
    u = get_object_or_404(Utilisateur, pk=pk)

    # Les comptes étudiants se modifient via leur fiche dédiée.
    if u.role == Utilisateur.Role.ETUDIANT and hasattr(u, "fiche_etudiant"):
        messages.info(
            request,
            "Ce compte est un étudiant. Modifiez la fiche étudiant pour changer "
            "son niveau, son département ou ses informations académiques.",
        )
        return redirect("etudiants:modifier_etudiant", pk=u.fiche_etudiant.pk)

    if request.method == "POST":
        form = UtilisateurForm(request.POST, instance=u)
    else:
        form = UtilisateurForm(instance=u)

    # Empêche de modifier le statut du compte administrateur ou son propre statut.
    if u.role == Utilisateur.Role.ADMIN_SYSTEME:
        form.fields["est_actif_compte"].disabled = True
        form.initial["est_actif_compte"] = True
    elif u.pk == request.user.pk:
        form.fields["est_actif_compte"].disabled = True
        form.initial["est_actif_compte"] = u.est_actif_compte

    if request.method == "POST" and form.is_valid():
        if u.role == Utilisateur.Role.ADMIN_SYSTEME:
            form.instance.est_actif_compte = True

        form.save()
        enregistrer_activite(
            request.user, "MODIFICATION", "Utilisateur", u.pk, str(u)
        )
        messages.success(request, f"Compte « {u} » mis à jour.")
        return redirect("comptes:liste_utilisateurs")

    return render(request, "comptes/formulaire_utilisateur.html", {
        "form": form,
        "titre": f"Modifier {u}",
        "creation": False,
    })


@exiger_admin_systeme
def basculer_activation_utilisateur(request, pk):
    u = get_object_or_404(Utilisateur, pk=pk)

    if u.role == Utilisateur.Role.ADMIN_SYSTEME:
        messages.error(
            request,
            "Le compte administrateur système ne peut pas être désactivé.",
        )
        return redirect("comptes:liste_utilisateurs")

    if u.pk == request.user.pk:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect("comptes:liste_utilisateurs")

    u.est_actif_compte = not u.est_actif_compte
    u.save()

    enregistrer_activite(
        request.user,
        "DESACTIVATION",
        "Utilisateur",
        u.pk,
        str(u),
        details="Réactivé" if u.est_actif_compte else "Désactivé",
    )
    messages.success(
        request,
        f"Compte « {u} » {'réactivé' if u.est_actif_compte else 'désactivé'}.",
    )
    return redirect("comptes:liste_utilisateurs")


@exiger_admin_systeme
def supprimer_utilisateur(request, pk):
    u = get_object_or_404(Utilisateur, pk=pk)

    if u.role == Utilisateur.Role.ADMIN_SYSTEME:
        messages.error(
            request,
            "Le compte administrateur système ne peut pas être supprimé ici.",
        )
        return redirect("comptes:liste_utilisateurs")

    if u.pk == request.user.pk:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect("comptes:liste_utilisateurs")

    if request.method == "POST":
        repr_u = str(u)
        enregistrer_activite(
            request.user, "SUPPRESSION", "Utilisateur", u.pk, repr_u
        )
        u.delete()
        messages.success(request, f"Compte « {repr_u} » supprimé.")
        return redirect("comptes:liste_utilisateurs")

    return render(request, "comptes/confirmer_suppression.html", {
        "objet": u,
        "type_objet": "le compte",
    })


class HistoriqueActiviteView(LoginRequiredMixin, ListView):
    model = JournalActivite
    template_name = "comptes/historique.html"
    context_object_name = "activites"
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        if not est_admin_systeme(request.user) and request.user.role != Utilisateur.Role.DIRECTEUR_ACADEMIQUE:
            messages.error(request, "Accès réservé à l'administration.")
            return redirect("comptes:tableau_bord")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().select_related("utilisateur")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(objet_repr__icontains=q) | Q(type_objet__icontains=q))
        return qs