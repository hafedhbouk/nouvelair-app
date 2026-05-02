"""
Modèle Flight - Application de gestion des vols.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class Airport(models.Model):
    """Modèle représentant un aéroport."""

    code = models.CharField(max_length=3, unique=True, verbose_name="Code IATA")
    name = models.CharField(max_length=200, verbose_name="Nom de l'aéroport")
    city = models.CharField(max_length=100, verbose_name="Ville")
    country = models.CharField(max_length=100, verbose_name="Pays")
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        verbose_name="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        verbose_name="Longitude"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Aéroport"
        verbose_name_plural = "Aéroports"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.city} ({self.country})"


class Aircraft(models.Model):
    """Modèle représentant un aéronef."""

    model_name = models.CharField(max_length=100, verbose_name="Modèle")
    registration = models.CharField(max_length=20, unique=True, verbose_name="Immatriculation")
    total_seats = models.PositiveIntegerField(verbose_name="Nombre total de sièges")
    economy_seats = models.PositiveIntegerField(verbose_name="Sièges classe Économie")
    business_seats = models.PositiveIntegerField(verbose_name="Sièges classe Affaires")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Aéronef"
        verbose_name_plural = "Aéronefs"
        ordering = ['model_name']

    def __str__(self):
        return f"{self.model_name} ({self.registration})"

    def available_economy_seats(self):
        """Retourne le nombre de sièges économiques disponibles."""
        booked = sum(
            p.quantity for p in self.flight_set.filter(
                departure_time__gt=timezone.now()
            ).values_list('passengers__quantity', flat=True)
        )
        return max(0, self.economy_seats - booked)

    def available_business_seats(self):
        """Retourne le nombre de sièges affaires disponibles."""
        booked = sum(
            p.quantity for p in self.flight_set.filter(
                departure_time__gt=timezone.now(),
                passengers__travel_class='business'
            ).values_list('passengers__quantity', flat=True)
        )
        return max(0, self.business_seats - booked)


class Flight(models.Model):
    """Modèle représentant un vol."""

    FLIGHT_STATUS_CHOICES = [
        ('scheduled', 'Programmé'),
        ('boarding', 'Embarquement'),
        ('in_flight', 'En vol'),
        ('arrived', 'Arrivé'),
        ('delayed', 'Retardé'),
        ('cancelled', 'Annulé'),
    ]

    flight_number = models.CharField(max_length=10, unique=True, verbose_name="Numéro de vol")
    origin = models.ForeignKey(
        Airport, on_delete=models.PROTECT,
        related_name='departures', verbose_name="Aéroport de départ"
    )
    destination = models.ForeignKey(
        Airport, on_delete=models.PROTECT,
        related_name='arrivals', verbose_name="Aéroport d'arrivée"
    )
    aircraft = models.ForeignKey(
        Aircraft, on_delete=models.PROTECT,
        verbose_name="Aéronef"
    )
    departure_time = models.DateTimeField(verbose_name="Heure de départ")
    arrival_time = models.DateTimeField(verbose_name="Heure d'arrivée")
    duration = models.DurationField(verbose_name="Durée", null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=FLIGHT_STATUS_CHOICES,
        default='scheduled', verbose_name="Statut"
    )
    base_price_economy = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix de base Économie (TND)"
    )
    base_price_business = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Prix de base Affaires (TND)"
    )
    available_seats_economy = models.PositiveIntegerField(
        default=0, verbose_name="Sièges économiques disponibles"
    )
    available_seats_business = models.PositiveIntegerField(
        default=0, verbose_name="Sièges affaires disponibles"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_duration_display(self):

        if self.arrival_time and self.departure_time:
            diff = self.arrival_time - self.departure_time
            total_minutes = int(diff.total_seconds() / 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if hours > 0 and minutes > 0:
                return '%dh %dmin' % (hours, minutes)
            elif hours > 0:
                return '%dh' % hours
            else:
                return '%dmin' % minutes
        return ''

    def get_durations_display(self):
        """Calcule et formate la durée du vol."""
        delta = self.arrival_time - self.departure_time
        total_minutes = int(delta.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes:02d}min"

    class Meta:
        verbose_name = "Vol"
        verbose_name_plural = "Vols"
        ordering = ['departure_time']
        indexes = [
            models.Index(fields=['origin', 'destination']),
            models.Index(fields=['departure_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.flight_number}: {self.origin.code} → {self.destination.code} ({self.departure_time.strftime('%d/%m/%Y %H:%M')})"

    def save(self, *args, **kwargs):
        if self.arrival_time and self.departure_time:
            self.duration = self.arrival_time - self.departure_time
        super().save(*args, **kwargs)

    def get_current_price_economy(self):
        """Retourne le prix actuel en économie avec éventuelle majoration."""
        from promotions.models import Promotion
        price = self.base_price_economy
        active_promos = Promotion.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now(),
            flights__id=self.id
        )
        for promo in active_promos:
            price = price * (1 - promo.discount_percentage / 100)
        return round(price, 2)

    def get_current_price_business(self):
        """Retourne le prix actuel en affaires avec éventuelle majoration."""
        from promotions.models import Promotion
        price = self.base_price_business
        active_promos = Promotion.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now(),
            flights__id=self.id
        )
        for promo in active_promos:
            price = price * (1 - promo.discount_percentage / 100)
        return round(price, 2)

    @classmethod
    def search_flights(cls, origin_code, destination_code, departure_date, passengers=1, travel_class='economy'):
        """
        Recherche de vols disponibles selon les critères.
        Retourne un queryset de vols filtrés.
        """
        flights = cls.objects.filter(
            origin__code=origin_code,
            destination__code=destination_code,
            departure_time__date=departure_date,
            is_active=True,
            status='scheduled'
        )

        if travel_class == 'business':
            flights = flights.filter(available_seats_business__gte=passengers)
        else:
            flights = flights.filter(available_seats_economy__gte=passengers)

        return flights.select_related('origin', 'destination', 'aircraft')
