from django.contrib import messages
from django.contrib.auth import login, views as auth_views
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView

from .forms import ConnexionForm, UtilisateurCreationForm, UtilisateurForm  # noqa: F401
from .models import JournalActivite, Utilisateur, enregistrer_activite


def est_admin(user):
    return user.is_authenticated and (user.est_administrateur or user.is_superuser)


class ConnexionView(auth_views.LoginView):
    template_name = "comptes/connexion.html"
    authentication_form = ConnexionForm
    redirect_authenticated_user = True


class DeconnexionView(auth_views.LogoutView):
    next_page = "comptes:connexion"


@login_required
@user_passes_test(est_admin)
def liste_utilisateurs(request):
    q = request.GET.get("q", "").strip()
    utilisateurs = Utilisateur.objects.all().order_by("username")
    if q:
        utilisateurs = utilisateurs.filter(username__icontains=q) | utilisateurs.filter(email__icontains=q)
        enregistrer_activite(request.user, "RECHERCHE", "Utilisateur", details=f"Recherche: '{q}'")
    return render(request, "comptes/liste_utilisateurs.html", {"utilisateurs": utilisateurs.distinct(), "q": q})


@login_required
@user_passes_test(est_admin)
def creer_utilisateur(request):
    if request.method == "POST":
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            u = form.save()
            enregistrer_activite(request.user, "AJOUT", "Utilisateur", u.pk, str(u))
            messages.success(request, f"Utilisateur « {u} » créé avec succès.")
            return redirect("comptes:liste_utilisateurs")
    else:
        form = UtilisateurCreationForm()
    return render(request, "comptes/formulaire_utilisateur.html", {"form": form, "titre": "Ajouter un utilisateur"})


@login_required
@user_passes_test(est_admin)
def modifier_utilisateur(request, pk):
    u = get_object_or_404(Utilisateur, pk=pk)
    if request.method == "POST":
        form = UtilisateurForm(request.POST, instance=u)
        if form.is_valid():
            form.save()
            enregistrer_activite(request.user, "MODIFICATION", "Utilisateur", u.pk, str(u))
            messages.success(request, f"Utilisateur « {u} » mis à jour.")
            return redirect("comptes:liste_utilisateurs")
    else:
        form = UtilisateurForm(instance=u)
    return render(request, "comptes/formulaire_utilisateur.html", {"form": form, "titre": f"Modifier {u}"})


@login_required
@user_passes_test(est_admin)
def basculer_activation_utilisateur(request, pk):
    u = get_object_or_404(Utilisateur, pk=pk)
    u.est_actif_compte = not u.est_actif_compte
    u.save()
    enregistrer_activite(request.user, "DESACTIVATION", "Utilisateur", u.pk, str(u),
                          details="Réactivé" if u.est_actif_compte else "Désactivé")
    messages.success(request, f"Compte « {u} » {'réactivé' if u.est_actif_compte else 'désactivé'}.")
    return redirect("comptes:liste_utilisateurs")


@login_required
@user_passes_test(est_admin)
def supprimer_utilisateur(request, pk):
    u = get_object_or_404(Utilisateur, pk=pk)
    if request.method == "POST":
        repr_u = str(u)
        enregistrer_activite(request.user, "SUPPRESSION", "Utilisateur", u.pk, repr_u)
        u.delete()
        messages.success(request, f"Utilisateur « {repr_u} » supprimé.")
        return redirect("comptes:liste_utilisateurs")
    return render(request, "comptes/confirmer_suppression.html", {"objet": u, "type_objet": "utilisateur"})


class HistoriqueActiviteView(LoginRequiredMixin, ListView):
    model = JournalActivite
    template_name = "comptes/historique.html"
    context_object_name = "activites"
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        if not est_admin(request.user):
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect("stock:tableau_bord")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().select_related("utilisateur")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(objet_repr__icontains=q) | qs.filter(type_objet__icontains=q)
        return qs
