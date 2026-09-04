from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from comptes.models import enregistrer_activite

from .forms import CoursForm, DepartementForm, FaculteForm, FiliereForm
from .models import Cours, Departement, Faculte, Filiere


def a_acces_global(user):
    return user.is_authenticated and user.a_acces_global


# --- Facultés : réservé au périmètre global (admin système / directeur académique) ---

@login_required
def liste_facultes(request):
    if not request.user.a_acces_global:
        messages.error(request, "Accès réservé à la direction académique.")
        return redirect("comptes:tableau_bord")
    q = request.GET.get("q", "").strip()
    facultes = Faculte.objects.all()
    if q:
        facultes = facultes.filter(nom__icontains=q)
        enregistrer_activite(request.user, "RECHERCHE", "Faculté", details=f"Recherche: '{q}'")
    return render(request, "academique/liste_facultes.html", {"facultes": facultes, "q": q})


@login_required
def creer_faculte(request):
    if not request.user.a_acces_global:
        messages.error(request, "Accès réservé à la direction académique.")
        return redirect("comptes:tableau_bord")
    if request.method == "POST":
        form = FaculteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Faculté ajoutée.")
            return redirect("academique:liste_facultes")
    else:
        form = FaculteForm()
    return render(request, "academique/formulaire.html", {"form": form, "titre": "Ajouter une faculté"})


@login_required
def modifier_faculte(request, pk):
    if not request.user.a_acces_global:
        messages.error(request, "Accès réservé à la direction académique.")
        return redirect("comptes:tableau_bord")
    faculte = get_object_or_404(Faculte, pk=pk)
    if request.method == "POST":
        form = FaculteForm(request.POST, instance=faculte)
        if form.is_valid():
            form.save()
            messages.success(request, "Faculté mise à jour.")
            return redirect("academique:liste_facultes")
    else:
        form = FaculteForm(instance=faculte)
    return render(request, "academique/formulaire.html", {"form": form, "titre": f"Modifier {faculte}"})


# --- Départements : direction globale + Doyen de la faculté concernée ---

@login_required
def liste_departements(request):
    u = request.user
    departements = u.departements_geres().select_related("faculte")
    q = request.GET.get("q", "").strip()
    if q:
        departements = departements.filter(nom__icontains=q)
        enregistrer_activite(u, "RECHERCHE", "Département", details=f"Recherche: '{q}'")
    return render(request, "academique/liste_departements.html", {"departements": departements, "q": q})


@login_required
def creer_departement(request):
    u = request.user
    if not (u.a_acces_global or u.role == u.Role.DOYEN):
        messages.error(request, "Accès non autorisé.")
        return redirect("comptes:tableau_bord")
    if request.method == "POST":
        form = DepartementForm(request.POST, utilisateur=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Département ajouté.")
            return redirect("academique:liste_departements")
    else:
        form = DepartementForm(utilisateur=u)
    return render(request, "academique/formulaire.html", {"form": form, "titre": "Ajouter un département"})


@login_required
def modifier_departement(request, pk):
    u = request.user
    departement = get_object_or_404(u.departements_geres(), pk=pk)
    if request.method == "POST":
        form = DepartementForm(request.POST, instance=departement, utilisateur=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Département mis à jour.")
            return redirect("academique:liste_departements")
    else:
        form = DepartementForm(instance=departement, utilisateur=u)
    return render(request, "academique/formulaire.html", {"form": form, "titre": f"Modifier {departement}"})


# --- Filières : direction globale + doyen + chef de département ---

@login_required
def liste_filieres(request):
    u = request.user
    filieres = Filiere.objects.filter(departement__in=u.departements_geres()).select_related("departement")
    return render(request, "academique/liste_filieres.html", {"filieres": filieres})


@login_required
def creer_filiere(request):
    u = request.user
    if request.method == "POST":
        form = FiliereForm(request.POST, utilisateur=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Filière ajoutée.")
            return redirect("academique:liste_filieres")
    else:
        form = FiliereForm(utilisateur=u)
    return render(request, "academique/formulaire.html", {"form": form, "titre": "Ajouter une filière"})


@login_required
def modifier_filiere(request, pk):
    u = request.user
    filiere = get_object_or_404(Filiere, pk=pk, departement__in=u.departements_geres())
    if request.method == "POST":
        form = FiliereForm(request.POST, instance=filiere, utilisateur=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Filière mise à jour.")
            return redirect("academique:liste_filieres")
    else:
        form = FiliereForm(instance=filiere, utilisateur=u)
    return render(request, "academique/formulaire.html", {"form": form, "titre": f"Modifier {filiere}"})


# --- Cours : direction globale + doyen + chef de département (professeur = lecture seule via son tableau de bord) ---

@login_required
def liste_cours(request):
    u = request.user
    q = request.GET.get("q", "").strip()
    if u.role == u.Role.PROFESSEUR:
        cours = u.cours_enseignes.all()
    else:
        cours = Cours.objects.filter(departement__in=u.departements_geres()).select_related("departement")
    if q:
        cours = cours.filter(nom__icontains=q)
        enregistrer_activite(u, "RECHERCHE", "Cours", details=f"Recherche: '{q}'")
    paginator = Paginator(cours.distinct(), 12)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "academique/liste_cours.html", {"page_obj": page, "q": q})


@login_required
def creer_cours(request):
    u = request.user
    if u.role == u.Role.PROFESSEUR:
        messages.error(request, "Accès non autorisé.")
        return redirect("comptes:tableau_bord")
    if request.method == "POST":
        form = CoursForm(request.POST, utilisateur=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Cours ajouté.")
            return redirect("academique:liste_cours")
    else:
        form = CoursForm(utilisateur=u)
    return render(request, "academique/formulaire.html", {"form": form, "titre": "Ajouter un cours"})


@login_required
def modifier_cours(request, pk):
    u = request.user
    cours = get_object_or_404(Cours, pk=pk, departement__in=u.departements_geres())
    if request.method == "POST":
        form = CoursForm(request.POST, instance=cours, utilisateur=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Cours mis à jour.")
            return redirect("academique:liste_cours")
    else:
        form = CoursForm(instance=cours, utilisateur=u)
    return render(request, "academique/formulaire.html", {"form": form, "titre": f"Modifier {cours}"})
