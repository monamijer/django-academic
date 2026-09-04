from threading import local

_etat = local()


def utilisateur_courant():
    return getattr(_etat, "utilisateur", None)


def ip_courante():
    return getattr(_etat, "ip", None)


class JournalisationMiddleware:
    """Rend l'utilisateur et l'IP de la requête courante disponibles
    partout (signaux inclus) pour tracer automatiquement qui a fait quoi."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _etat.utilisateur = getattr(request, "user", None)
        _etat.ip = request.META.get("REMOTE_ADDR")
        return self.get_response(request)
