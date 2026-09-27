from django.apps import AppConfig


class AcademiqueConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'academique'
    verbose_name = "Structure académique"

    def ready(self):
        import academique.signals  # noqa
