from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="comptes:tableau_bord", permanent=False)),
    path("comptes/", include("comptes.urls")),
    path("academique/", include("academique.urls")),
    path("etudiants/", include("etudiants.urls")),
    path("rapports/", include("rapports.urls")),
]
