"""
Signaux pour l'application Flights.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Flight  # noqa: F401


@receiver(post_save, sender=Flight)
def set_initial_seats(sender, instance, created, **kwargs):
    """Définit les sièges disponibles à la création du vol."""
    if created and instance.aircraft:
        if instance.available_seats_economy == 0:
            instance.available_seats_economy = instance.aircraft.economy_seats
        if instance.available_seats_business == 0:
            instance.available_seats_business = instance.aircraft.business_seats
        instance.save(update_fields=['available_seats_economy', 'available_seats_business'])
