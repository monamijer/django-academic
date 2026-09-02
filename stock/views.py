from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from comptes.models import enregistrer_activite

from .forms import CategorieForm, MouvementStockForm, ProduitForm
from .models import Categorie, MouvementStock, Produit


def a_droit(user, code):
    return user.is_authenticated and (user.est_administrateur or user.is_superuser or user.has_perm(code))


@login_required
def tableau_bord(request):
    produits = Produit.objects.filter(est_actif=True)
    contexte = {
        "nb_produits": produits.count(),
        "nb_alertes": sum(1 for p in produits if p.en_alerte),
        "nb_perimes": sum(1 for p in produits if p.est_perime),
        "nb_categories": Categorie.objects.filter(est_active=True).count(),
        "derniers_mouvements": MouvementStock.objects.select_related("produit", "utilisateur")[:8],
        "produits_alerte": [p for p in produits if p.en_alerte][:8],
    }
    return render(request, "stock/tableau_bord.html", contexte)


@login_required
def liste_produits(request):
    q = request.GET.get("q", "").strip()
    categorie_id = request.GET.get("categorie", "")
    produits = Produit.objects.select_related("categorie").all()
    if q:
        produits = produits.filter(Q(nom__icontains=q) | Q(reference__icontains=q))
        enregistrer_activite(request.user, "RECHERCHE", "Produit", details=f"Recherche: '{q}'")
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)

    paginator = Paginator(produits, 12)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "stock/liste_produits.html", {
        "page_obj": page, "q": q, "categories": Categorie.objects.all(), "categorie_id": categorie_id,
    })


@login_required
def detail_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    enregistrer_activite(request.user, "AFFICHAGE", "Produit", produit.pk, str(produit))
    mouvements = produit.mouvements.select_related("utilisateur")[:20]
    return render(request, "stock/detail_produit.html", {"produit": produit, "mouvements": mouvements})


@login_required
@permission_required("stock.add_produit", raise_exception=True)
def creer_produit(request):
    if request.method == "POST":
        form = ProduitForm(request.POST)
        if form.is_valid():
            produit = form.save(commit=False)
            produit.cree_par = request.user
            produit.save()
            messages.success(request, f"Produit « {produit} » ajouté.")
            return redirect("stock:liste_produits")
    else:
        form = ProduitForm()
    return render(request, "stock/formulaire_produit.html", {"form": form, "titre": "Ajouter un produit"})


@login_required
@permission_required("stock.change_produit", raise_exception=True)
def modifier_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == "POST":
        form = ProduitForm(request.POST, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, f"Produit « {produit} » mis à jour.")
            return redirect("stock:detail_produit", pk=produit.pk)
    else:
        form = ProduitForm(instance=produit)
    return render(request, "stock/formulaire_produit.html", {"form": form, "titre": f"Modifier {produit}"})


@login_required
@permission_required("stock.change_produit", raise_exception=True)
def basculer_activation_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    produit.est_actif = not produit.est_actif
    produit.save()
    enregistrer_activite(request.user, "DESACTIVATION", "Produit", produit.pk, str(produit),
                          details="Réactivé" if produit.est_actif else "Désactivé")
    messages.success(request, f"Produit « {produit} » {'réactivé' if produit.est_actif else 'désactivé'}.")
    return redirect("stock:liste_produits")


@login_required
@permission_required("stock.delete_produit", raise_exception=True)
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == "POST":
        repr_p = str(produit)
        produit.delete()
        messages.success(request, f"Produit « {repr_p} » supprimé.")
        return redirect("stock:liste_produits")
    return render(request, "stock/confirmer_suppression.html", {"objet": produit, "type_objet": "produit"})


@login_required
def liste_categories(request):
    categories = Categorie.objects.all()
    return render(request, "stock/liste_categories.html", {"categories": categories})


@login_required
@permission_required("stock.add_categorie", raise_exception=True)
def creer_categorie(request):
    if request.method == "POST":
        form = CategorieForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie ajoutée.")
            return redirect("stock:liste_categories")
    else:
        form = CategorieForm()
    return render(request, "stock/formulaire_categorie.html", {"form": form, "titre": "Ajouter une catégorie"})


@login_required
@permission_required("stock.change_categorie", raise_exception=True)
def modifier_categorie(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == "POST":
        form = CategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie mise à jour.")
            return redirect("stock:liste_categories")
    else:
        form = CategorieForm(instance=categorie)
    return render(request, "stock/formulaire_categorie.html", {"form": form, "titre": f"Modifier {categorie}"})


@login_required
@permission_required("stock.add_mouvementstock", raise_exception=True)
def enregistrer_mouvement(request):
    if request.method == "POST":
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            mouvement.utilisateur = request.user
            mouvement.save()
            messages.success(request, f"Mouvement de stock enregistré pour « {mouvement.produit} ».")
            return redirect("stock:liste_mouvements")
    else:
        form = MouvementStockForm(initial={"produit": request.GET.get("produit")})
    return render(request, "stock/formulaire_mouvement.html", {"form": form, "titre": "Enregistrer un mouvement"})


@login_required
def liste_mouvements(request):
    mouvements = MouvementStock.objects.select_related("produit", "utilisateur").all()
    q = request.GET.get("q", "")
    if q:
        mouvements = mouvements.filter(produit__nom__icontains=q)
    paginator = Paginator(mouvements, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "stock/liste_mouvements.html", {"page_obj": page, "q": q})
