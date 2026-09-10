from django.urls import path
from .views import SignUpView, LoginView, LogoutView, MeView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="api-signup"),
    path("login/", LoginView.as_view(), name="api-login"),
    path("logout/", LogoutView.as_view(), name="api-logout"),
    path("me/", MeView.as_view(), name="api-me"),
]