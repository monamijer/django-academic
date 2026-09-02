from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from comptes.models import enregistrer_activite
from stock.models import MouvementStock, Produit


@login_required
def rapport_mouvements(request):
    """Rapport imprimable des entrées/sorties sur une période (7 jours par défaut)."""
    jours = int(request.GET.get("jours", 7))
    date_fin = timezone.now()
    date_debut = date_fin - timedelta(days=jours)

    mouvements = MouvementStock.objects.select_related("produit", "utilisateur").filter(
        date_mouvement__range=(date_debut, date_fin)
    )
    total_entrees = sum(m.quantite for m in mouvements if m.type_mouvement == "ENTREE")
    total_sorties = sum(m.quantite for m in mouvements if m.type_mouvement == "SORTIE")

    par_produit = {}
    for m in mouvements:
        stats = par_produit.setdefault(m.produit, {"entrees": 0, "sorties": 0})
        if m.type_mouvement == "ENTREE":
            stats["entrees"] += m.quantite
        else:
            stats["sorties"] += m.quantite

    enregistrer_activite(request.user, "IMPRESSION", "Rapport", details=f"Mouvements sur {jours} jours")
    return render(request, "rapports/rapport_mouvements.html", {
        "mouvements": mouvements.order_by("-date_mouvement"),
        "par_produit": par_produit,
        "total_entrees": total_entrees,
        "total_sorties": total_sorties,
        "jours": jours,
        "date_debut": date_debut,
        "date_fin": date_fin,
    })


@login_required
def rapport_peremption(request):
    """Rapport imprimable des produits périmés et bientôt périmés."""
    produits = Produit.objects.filter(date_peremption__isnull=False).select_related("categorie")
    perimes = [p for p in produits if p.est_perime]
    bientot = [p for p in produits if p.bientot_perime]

    enregistrer_activite(request.user, "IMPRESSION", "Rapport", details="Rapport de péremption")
    return render(request, "rapports/rapport_peremption.html", {
        "perimes": perimes, "bientot": bientot, "aujourdhui": timezone.now().date(),
    })


@login_required
def rapport_stock_actuel(request):
    """Rapport imprimable de l'état complet du stock, avec alertes de seuil."""
    produits = Produit.objects.filter(est_actif=True).select_related("categorie").order_by("categorie__nom", "nom")
    valeur_totale = sum(p.quantite_stock * p.prix_unitaire for p in produits)

    enregistrer_activite(request.user, "IMPRESSION", "Rapport", details="État du stock")
    return render(request, "rapports/rapport_stock.html", {
        "produits": produits, "valeur_totale": valeur_totale,
    })


@login_required
def centre_rapports(request):
    return render(request, "rapports/centre_rapports.html")
