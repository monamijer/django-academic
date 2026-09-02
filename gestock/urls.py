from django.contrib import admin
from django.urls import include, path
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="stock:tableau_bord", permanent=False)),
    path("comptes/", include("comptes.urls")),
    path("stock/", include("stock.urls")),
    path("rapports/", include("rapports.urls")),
]
