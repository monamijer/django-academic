from django.urls import path
from . import views

app_name = "rapports"

urlpatterns = [
    path("", views.centre_rapports, name="centre_rapports"),
    path("mouvements/", views.rapport_mouvements, name="rapport_mouvements"),
    path("peremption/", views.rapport_peremption, name="rapport_peremption"),
    path("stock/", views.rapport_stock_actuel, name="rapport_stock"),
]
