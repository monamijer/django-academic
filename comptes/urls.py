from django.urls import path
from . import views

app_name = "comptes"

urlpatterns = [
    path("connexion/", views.ConnexionView.as_view(), name="connexion"),
    path("deconnexion/", views.DeconnexionView.as_view(), name="deconnexion"),
    path("utilisateurs/", views.liste_utilisateurs, name="liste_utilisateurs"),
    path("utilisateurs/ajouter/", views.creer_utilisateur, name="creer_utilisateur"),
    path("utilisateurs/<int:pk>/modifier/", views.modifier_utilisateur, name="modifier_utilisateur"),
    path("utilisateurs/<int:pk>/activer-desactiver/", views.basculer_activation_utilisateur, name="basculer_activation"),
    path("utilisateurs/<int:pk>/supprimer/", views.supprimer_utilisateur, name="supprimer_utilisateur"),
    path("historique/", views.HistoriqueActiviteView.as_view(), name="historique"),
]
