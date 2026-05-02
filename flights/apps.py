"""
Configuration de l'application Flights.
"""

from django.apps import AppConfig


class FlightsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "flights"
    verbose_name = "Vols"

    def ready(self):
        import flights.signals  # noqa: F401
