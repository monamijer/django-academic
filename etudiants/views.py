from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from academique.models import Cours
from comptes.models import enregistrer_activite

from .forms import EtudiantCreationForm, EtudiantForm, InscriptionForm, NoteForm
from .models import Etudiant, Inscription, Note


def _etudiants_visibles(user):
    if user.a_acces_global:
        return Etudiant.objects.all()
    return Etudiant.objects.filter(filiere__departement__in=user.departements_geres())


@login_required
def liste_etudiants(request):
    u = request.user
    q = request.GET.get("q", "").strip()
    etudiants = _etudiants_visibles(u).select_related("utilisateur", "filiere")
    if q:
        etudiants = etudiants.filter(matricule__icontains=q) | etudiants.filter(utilisateur__last_name__icontains=q)
        enregistrer_activite(u, "RECHERCHE", "Étudiant", details=f"Recherche: '{q}'")
    paginator = Paginator(etudiants.distinct(), 12)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "etudiants/liste_etudiants.html", {"page_obj": page, "q": q})


@login_required
def detail_etudiant(request, pk):
    etudiant = get_object_or_404(_etudiants_visibles(request.user), pk=pk)
    enregistrer_activite(request.user, "AFFICHAGE", "Étudiant", etudiant.pk, str(etudiant))
    notes = etudiant.notes.select_related("cours", "annee_academique")
    inscriptions = etudiant.inscriptions.select_related("cours", "annee_academique")
    return render(request, "etudiants/detail_etudiant.html", {
        "etudiant": etudiant, "notes": notes, "inscriptions": inscriptions,
    })


@login_required
def creer_etudiant(request):
    u = request.user
    if u.role not in (u.Role.ADMIN_SYSTEME, u.Role.DIRECTEUR_ACADEMIQUE, u.Role.DOYEN, u.Role.CHEF_DEPARTEMENT, u.Role.SECRETAIRE):
        messages.error(request, "Accès non autorisé.")
        return redirect("comptes:tableau_bord")
    if request.method == "POST":
        form = EtudiantCreationForm(request.POST, utilisateur=u)
        if form.is_valid():
            compte = form.save()
            enregistrer_activite(u, "AJOUT", "Étudiant", compte.pk, str(compte))
            messages.success(request, f"Étudiant « {compte} » inscrit.")
            return redirect("etudiants:liste_etudiants")
    else:
        form = EtudiantCreationForm(utilisateur=u)
    return render(request, "etudiants/formulaire_etudiant.html", {"form": form, "titre": "Ajouter un étudiant"})


@login_required
def modifier_etudiant(request, pk):
    u = request.user
    etudiant = get_object_or_404(_etudiants_visibles(u), pk=pk)
    if request.method == "POST":
        form = EtudiantForm(request.POST, instance=etudiant, utilisateur=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Fiche étudiant mise à jour.")
            return redirect("etudiants:detail_etudiant", pk=etudiant.pk)
    else:
        form = EtudiantForm(instance=etudiant, utilisateur=u)
    return render(request, "etudiants/formulaire_etudiant.html", {"form": form, "titre": f"Modifier {etudiant}"})


@login_required
def basculer_activation_etudiant(request, pk):
    etudiant = get_object_or_404(_etudiants_visibles(request.user), pk=pk)
    etudiant.est_actif = not etudiant.est_actif
    etudiant.save()
    enregistrer_activite(request.user, "DESACTIVATION", "Étudiant", etudiant.pk, str(etudiant))
    messages.success(request, f"Étudiant « {etudiant} » {'réactivé' if etudiant.est_actif else 'désactivé'}.")
    return redirect("etudiants:liste_etudiants")


# --- Inscriptions ---

@login_required
def liste_inscriptions(request):
    u = request.user
    inscriptions = Inscription.objects.filter(etudiant__in=_etudiants_visibles(u)).select_related("etudiant", "cours", "annee_academique")
    paginator = Paginator(inscriptions, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "etudiants/liste_inscriptions.html", {"page_obj": page})


@login_required
def creer_inscription(request):
    u = request.user
    if request.method == "POST":
        form = InscriptionForm(request.POST, utilisateur=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Inscription enregistrée.")
            return redirect("etudiants:liste_inscriptions")
    else:
        form = InscriptionForm(utilisateur=u)
    return render(request, "etudiants/formulaire_inscription.html", {"form": form, "titre": "Nouvelle inscription"})


# --- Cours du professeur + saisie de notes ---

@login_required
def mes_cours(request):
    if request.user.role != "PROFESSEUR":
        messages.error(request, "Accès réservé aux professeurs.")
        return redirect("comptes:tableau_bord")
    cours = request.user.cours_enseignes.all()
    return render(request, "etudiants/mes_cours.html", {"cours": cours})


@login_required
def notes_cours(request, cours_id):
    u = request.user
    cours = get_object_or_404(Cours, pk=cours_id)
    if u.role == "PROFESSEUR" and cours not in u.cours_enseignes.all():
        messages.error(request, "Vous n'enseignez pas ce cours.")
        return redirect("comptes:tableau_bord")
    notes = Note.objects.filter(cours=cours).select_related("etudiant", "annee_academique")
    return render(request, "etudiants/notes_cours.html", {"cours": cours, "notes": notes})


@login_required
def saisir_note(request, cours_id):
    u = request.user
    cours = get_object_or_404(Cours, pk=cours_id)
    if u.role == "PROFESSEUR" and cours not in u.cours_enseignes.all():
        messages.error(request, "Vous n'enseignez pas ce cours.")
        return redirect("comptes:tableau_bord")
    if request.method == "POST":
        form = NoteForm(request.POST, professeur=u if u.role == "PROFESSEUR" else None, cours_fige=cours)
        if form.is_valid():
            note = form.save(commit=False)
            note.cours = cours
            note.evaluee_par = u
            note.save()
            enregistrer_activite(u, "AJOUT", "Note", note.pk, str(note))
            messages.success(request, "Note enregistrée.")
            return redirect("etudiants:notes_cours", cours_id=cours.pk)
    else:
        form = NoteForm(professeur=u if u.role == "PROFESSEUR" else None, cours_fige=cours)
    return render(request, "etudiants/formulaire_note.html", {"form": form, "titre": f"Saisir une note — {cours}"})
