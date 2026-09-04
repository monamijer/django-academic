from functools import wraps

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from academique.models import Cours, Departement, Faculte
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
        })
        template = "comptes/tableau_bord_direction.html"

    elif u.role == Utilisateur.Role.DOYEN:
        departements = u.departements_geres()
        contexte.update({
            "faculte": u.faculte,
            "nb_departements": departements.count(),
            "nb_etudiants": Etudiant.objects.filter(filiere__departement__in=departements, est_actif=True).count(),
            "nb_cours": Cours.objects.filter(departement__in=departements, est_actif=True).count(),
        })
        template = "comptes/tableau_bord_doyen.html"

    elif u.role == Utilisateur.Role.CHEF_DEPARTEMENT:
        departements = u.departements_geres()
        etudiants = Etudiant.objects.filter(filiere__departement__in=departements, est_actif=True)
        contexte.update({
            "departement": u.departement,
            "nb_etudiants": etudiants.count(),
            "nb_cours": Cours.objects.filter(departement__in=departements, est_actif=True).count(),
            "etudiants_en_difficulte": [e for e in etudiants if e.en_difficulte][:8],
        })
        template = "comptes/tableau_bord_chef_departement.html"

    elif u.role == Utilisateur.Role.PROFESSEUR:
        cours = u.cours_enseignes.filter(est_actif=True)
        contexte.update({
            "cours": cours,
            "nb_etudiants": Etudiant.objects.filter(inscriptions__cours__in=cours).distinct().count(),
        })
        template = "comptes/tableau_bord_professeur.html"

    elif u.role == Utilisateur.Role.SECRETAIRE:
        departements = u.departements_geres()
        contexte.update({
            "departement": u.departement,
            "nb_etudiants": Etudiant.objects.filter(filiere__departement__in=departements).count(),
        })
        template = "comptes/tableau_bord_secretaire.html"

    elif u.role == Utilisateur.Role.ETUDIANT:
        fiche = getattr(u, "fiche_etudiant", None)
        contexte.update({
            "fiche": fiche,
            "notes": fiche.notes.select_related("cours").all() if fiche else [],
            "moyenne": fiche.moyenne_generale() if fiche else None,
            "mention": fiche.mention() if fiche else "—",
        })
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
        utilisateurs = utilisateurs.filter(username__icontains=q) | utilisateurs.filter(email__icontains=q)
        enregistrer_activite(request.user, "RECHERCHE", "Utilisateur", details=f"Recherche: '{q}'")
    if role:
        utilisateurs = utilisateurs.filter(role=role)
    return render(request, "comptes/liste_utilisateurs.html", {
        "utilisateurs": utilisateurs.distinct(), "q": q, "role": role, "roles": Utilisateur.Role.choices,
    })


@exiger_admin_systeme
def creer_utilisateur(request):
    if request.method == "POST":
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            u = form.save()
            enregistrer_activite(request.user, "AJOUT", "Utilisateur", u.pk, str(u))
            messages.success(request, f"Compte « {u} » créé.")
            return redirect("comptes:liste_utilisateurs")
    else:
        form = UtilisateurCreationForm()
    return render(request, "comptes/formulaire_utilisateur.html", {"form": form, "titre": "Ajouter un compte", "creation": True})


@exiger_admin_systeme
def modifier_utilisateur(request, pk):
    u = get_object_or_404(Utilisateur, pk=pk)
    if request.method == "POST":
        form = UtilisateurForm(request.POST, instance=u)
        if form.is_valid():
            form.save()
            enregistrer_activite(request.user, "MODIFICATION", "Utilisateur", u.pk, str(u))
            messages.success(request, f"Compte « {u} » mis à jour.")
            return redirect("comptes:liste_utilisateurs")
    else:
        form = UtilisateurForm(instance=u)
    return render(request, "comptes/formulaire_utilisateur.html", {"form": form, "titre": f"Modifier {u}", "creation": False})


@exiger_admin_systeme
def basculer_activation_utilisateur(request, pk):
    u = get_object_or_404(Utilisateur, pk=pk)
    u.est_actif_compte = not u.est_actif_compte
    u.save()
    enregistrer_activite(request.user, "DESACTIVATION", "Utilisateur", u.pk, str(u),
                          details="Réactivé" if u.est_actif_compte else "Désactivé")
    messages.success(request, f"Compte « {u} » {'réactivé' if u.est_actif_compte else 'désactivé'}.")
    return redirect("comptes:liste_utilisateurs")


@exiger_admin_systeme
def supprimer_utilisateur(request, pk):
    u = get_object_or_404(Utilisateur, pk=pk)
    if request.method == "POST":
        repr_u = str(u)
        enregistrer_activite(request.user, "SUPPRESSION", "Utilisateur", u.pk, repr_u)
        u.delete()
        messages.success(request, f"Compte « {repr_u} » supprimé.")
        return redirect("comptes:liste_utilisateurs")
    return render(request, "comptes/confirmer_suppression.html", {"objet": u, "type_objet": "le compte"})


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
            qs = qs.filter(objet_repr__icontains=q) | qs.filter(type_objet__icontains=q)
        return qs
