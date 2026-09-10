from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from academique.models import Cours, Departement
from comptes.models import enregistrer_activite
from etudiants.models import Etudiant


def _etudiants_visibles(user):
    if user.a_acces_global:
        return Etudiant.objects.all()
    return Etudiant.objects.filter(filiere__departement__in=user.departements_geres())


@login_required
def centre_rapports(request):
    return render(request, "rapports/centre_rapports.html")


@login_required
def mon_releve(request):
    """Un étudiant imprime son propre relevé — indépendant du filtrage par
    périmètre de gestion, qui ne le couvre pas puisqu'il gère seulement ses
    propres données, pas celles d'un département."""
    etudiant = getattr(request.user, "fiche_etudiant", None)
    if etudiant is None:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Aucune fiche étudiant associée à ce compte.")
        return redirect("comptes:tableau_bord")
    notes = etudiant.notes.select_related("cours", "annee_academique")
    enregistrer_activite(request.user, "IMPRESSION", "Rapport", details="Mon relevé de notes")
    return render(request, "rapports/releve_notes.html", {
        "etudiant": etudiant, "notes": notes,
        "moyenne": etudiant.moyenne_generale(), "mention": etudiant.mention(),
    })


@login_required
def releve_notes(request, pk):
    """Relevé de notes imprimable d'un étudiant, avec calcul de moyenne."""
    etudiant = get_object_or_404(_etudiants_visibles(request.user), pk=pk)
    notes = etudiant.notes.select_related("cours", "annee_academique")
    enregistrer_activite(request.user, "IMPRESSION", "Rapport", details=f"Relevé de notes — {etudiant}")
    return render(request, "rapports/releve_notes.html", {
        "etudiant": etudiant, "notes": notes,
        "moyenne": etudiant.moyenne_generale(), "mention": etudiant.mention(),
    })


@login_required
def liste_etudiants_departement(request):
    """Liste imprimable des étudiants, avec effectifs par filière, pour le périmètre de l'utilisateur."""
    departements = request.user.departements_geres()
    etudiants = _etudiants_visibles(request.user).select_related("filiere", "utilisateur").order_by("filiere__nom", "matricule")
    enregistrer_activite(request.user, "IMPRESSION", "Rapport", details="Liste des étudiants")
    return render(request, "rapports/liste_etudiants.html", {"etudiants": etudiants, "departements": departements})


@login_required
def liste_personnel(request):
    """Liste imprimable du personnel par département/faculté, pour le périmètre de l'utilisateur."""
    from comptes.models import Utilisateur
    if request.user.a_acces_global:
        personnel = Utilisateur.objects.exclude(role=Utilisateur.Role.ETUDIANT)
    else:
        personnel = Utilisateur.objects.filter(departement__in=request.user.departements_geres()).exclude(role=Utilisateur.Role.ETUDIANT)
    enregistrer_activite(request.user, "IMPRESSION", "Rapport", details="Liste du personnel")
    return render(request, "rapports/liste_personnel.html", {"personnel": personnel.order_by("role", "last_name")})


@login_required
def performance_cours(request, cours_id):
    """Rapport de performance d'un cours : moyenne et distribution des notes."""
    u = request.user
    cours = get_object_or_404(Cours, pk=cours_id)
    if u.role == "PROFESSEUR" and cours not in u.cours_enseignes.all():
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Vous n'enseignez pas ce cours.")
        return redirect("comptes:tableau_bord")

    notes = list(cours.notes.select_related("etudiant").all())
    moyenne = round(sum(n.valeur for n in notes) / len(notes), 2) if notes else None
    tranches = {"0-9": 0, "10-11": 0, "12-13": 0, "14-15": 0, "16-20": 0}
    for n in notes:
        v = float(n.valeur)
        if v < 10:
            tranches["0-9"] += 1
        elif v < 12:
            tranches["10-11"] += 1
        elif v < 14:
            tranches["12-13"] += 1
        elif v < 16:
            tranches["14-15"] += 1
        else:
            tranches["16-20"] += 1

    enregistrer_activite(u, "IMPRESSION", "Rapport", details=f"Performance — {cours}")
    return render(request, "rapports/performance_cours.html", {
        "cours": cours, "notes": notes, "moyenne": moyenne, "tranches": tranches,
    })
