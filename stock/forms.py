from django import forms

from .models import Categorie, MouvementStock, Produit


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = [
            "nom", "reference", "categorie", "unite", "quantite_stock",
            "seuil_alerte", "prix_unitaire", "date_peremption", "est_actif",
        ]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
            "categorie": forms.Select(attrs={"class": "form-select"}),
            "unite": forms.TextInput(attrs={"class": "form-control"}),
            "quantite_stock": forms.NumberInput(attrs={"class": "form-control"}),
            "seuil_alerte": forms.NumberInput(attrs={"class": "form-control"}),
            "prix_unitaire": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "date_peremption": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "est_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ["nom", "description", "couleur", "est_active"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "couleur": forms.TextInput(attrs={"class": "form-control form-control-color", "type": "color"}),
            "est_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class MouvementStockForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ["produit", "type_mouvement", "quantite", "note"]
        widgets = {
            "produit": forms.Select(attrs={"class": "form-select"}),
            "type_mouvement": forms.Select(attrs={"class": "form-select"}),
            "quantite": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "note": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        produit = cleaned.get("produit")
        type_mouvement = cleaned.get("type_mouvement")
        quantite = cleaned.get("quantite")
        if produit and type_mouvement == MouvementStock.Type.SORTIE and quantite and quantite > produit.quantite_stock:
            raise forms.ValidationError(
                f"Stock insuffisant : {produit} n'a que {produit.quantite_stock} {produit.unite}(s) en stock."
            )
        return cleaned
