from django.apps import AppConfig


class EtudiantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'etudiants'
    verbose_name = "Étudiants, inscriptions et notes"

    def ready(self):
        import etudiants.signals  # noqa
