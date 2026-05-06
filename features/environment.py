"""
environment.py — Configuration Behave-Django pour les tests BDD.
================================================================

Ce fichier configure l'environnement d'exécution de Behave avec
l'intégration Django (behave-django).

Hooks :
    before_all        — Initialise Django avant tous les scénarios
    after_all         — Nettoyage final après tous les scénarios
    before_scenario   — Réinitialise la BDD et crée les données de test
    after_scenario    — Nettoie les données après chaque scénario
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nouvelair.settings")

import django

django.setup()

from behave import fixture, use_fixture
from django.test.utils import setup_test_environment, teardown_test_environment
from django.db import connection
from django.core.management import call_command

from datetime import timedelta
from django.utils import timezone


# ── Fixtures de données de test ───────────────────────────────────────────────


def _create_base_airports():
    """Crée les aéroports de base utilisés dans les scénarios."""
    airports = {}
    airport_data = [
        ("TUN", "Aéroport International Tunis-Carthage", "Tunis", "Tunisie",
         36.851000, 10.227000),
        ("CDG", "Aéroport Charles de Gaulle", "Paris", "France",
         49.009700, 2.547900),
        ("MRS", "Aéroport de Marseille Provence", "Marseille", "France",
         43.436400, 5.215700),
        ("CMN", "Aéroport Mohammed V", "Casablanca", "Maroc",
         33.367500, -7.589800),
        ("ALG", "Aéroport Houari Boumediene", "Alger", "Algérie",
         36.694000, 3.215300),
        ("JFK", "Aéroport John F. Kennedy", "New York", "États-Unis",
         40.641300, -73.778100),
        ("FCO", "Aéroport Léonard de Vinci", "Rome", "Italie",
         41.800300, 12.238900),
        ("LHR", "Aéroport de Heathrow", "Londres", "Royaume-Uni",
         51.470000, -0.454300),
    ]
    for code, name, city, country, lat, lon in airport_data:
        airports[code], _ = Airport.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "city": city,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "is_active": True,
            },
        )
    return airports


def _create_aircraft():
    """Crée un aéronef de test."""
    aircraft, _ = Aircraft.objects.get_or_create(
        registration="TS-ABC",
        defaults={
            "model_name": "Airbus A320",
            "total_seats": 180,
            "economy_seats": 150,
            "business_seats": 30,
            "is_active": True,
        },
    )
    return aircraft


def _create_test_flights(airports, aircraft):
    """Crée les vols de test pour les scénarios."""
    flights = {}
    now = timezone.now()
    flight_data = [
        ("BJ101", "TUN", "CDG", 7, 8, 0, 11, 30, 250.00, 600.00),
        ("BJ102", "TUN", "MRS", 7, 14, 0, 16, 30, 180.00, 450.00),
        ("BJ103", "CDG", "TUN", 14, 12, 0, 15, 30, 230.00, 550.00),
        ("BJ520", "TUN", "CDG", 10, 6, 30, 10, 0, 199.00, 520.00),
        ("BJ201", "TUN", "CMN", 12, 9, 0, 11, 30, 160.00, 400.00),
        ("BJ301", "TUN", "ALG", 8, 16, 0, 17, 30, 140.00, 350.00),
        ("BJ601", "TUN", "JFK", 15, 22, 0, 6, 0, 890.00, 2200.00),
        ("BJ401", "TUN", "FCO", 9, 7, 0, 9, 30, 210.00, 500.00),
        ("BJ501", "TUN", "LHR", 11, 10, 0, 13, 0, 280.00, 650.00),
    ]
    for fn, origin_code, dest_code, days, dh, dm, ah, am, pe, pb in flight_data:
        future_dep = now + timedelta(days=days, hours=dh, minutes=dm)
        future_arr = now + timedelta(days=days, hours=ah, minutes=am)
        # Si l'heure d'arrivée est avant le départ, ajouter un jour
        if future_arr <= future_dep:
            future_arr += timedelta(days=1)
        flights[fn], _ = Flight.objects.get_or_create(
            flight_number=fn,
            defaults={
                "origin": airports[origin_code],
                "destination": airports[dest_code],
                "aircraft": aircraft,
                "departure_time": future_dep,
                "arrival_time": future_arr,
                "status": "scheduled",
                "base_price_economy": pe,
                "base_price_business": pb,
                "available_seats_economy": 150,
                "available_seats_business": 30,
                "is_active": True,
            },
        )
    return flights


def _create_test_user():
    """Crée l'utilisateur de test 'testuser' avec profil."""
    user, created = User.objects.get_or_create(
        username="testuser",
        defaults={
            "email": "test@example.com",
            "first_name": "Jean",
            "last_name": "Dupont",
            "is_active": True,
        },
    )
    if created:
        user.set_password("TestPassword123!")
        user.save()
        UserProfile.objects.create(user=user, phone="+21612345678")
    return user


def _create_test_promotions(flights):
    """Crée les promotions de test."""
    promos = {}
    now = timezone.now()

    # Promo active
    promos["NOUVEL25"], _ = Promotion.objects.get_or_create(
        code="NOUVEL25",
        defaults={
            "name": "Réduction 25% NouvelAir",
            "description": "25% de réduction sur tous les vols",
            "promo_type": "percentage",
            "discount_percentage": 25.00,
            "discount_amount": 0,
            "start_date": now - timedelta(days=1),
            "end_date": now + timedelta(days=30),
            "max_uses": 100,
            "current_uses": 0,
            "min_purchase_amount": 0,
            "is_active": True,
            "is_featured": True,
        },
    )
    if created := not promos["NOUVEL25"].flights.exists():
        for flight in flights.values():
            promos["NOUVEL25"].flights.add(flight)

    # Promo expirée
    promos["EXPIRED10"], _ = Promotion.objects.get_or_create(
        code="EXPIRED10",
        defaults={
            "name": "Promo Expirée",
            "description": "Promotion expirée",
            "promo_type": "percentage",
            "discount_percentage": 10.00,
            "discount_amount": 0,
            "start_date": now - timedelta(days=60),
            "end_date": now - timedelta(days=30),
            "max_uses": 100,
            "current_uses": 50,
            "min_purchase_amount": 0,
            "is_active": False,
            "is_featured": False,
        },
    )

    return promos


def _populate_test_data():
    """Peuple la base avec toutes les données de test nécessaires."""
    airports = _create_base_airports()
    aircraft = _create_aircraft()
    flights = _create_test_flights(airports, aircraft)
    user = _create_test_user()
    promotions = _create_test_promotions(flights)

    return {
        "airports": airports,
        "aircraft": aircraft,
        "flights": flights,
        "user": user,
        "promotions": promotions,
    }


# ── Hooks Behave ──────────────────────────────────────────────────────────────


def before_all(context):
    """
    Initialisation globale avant l'exécution de tous les scénarios.

    - Initialise l'environnement de test Django
    """
    # Import Django models after settings are configured
    from django.contrib.auth.models import User
    from flights.models import Airport, Aircraft, Flight
    from accounts.models import UserProfile
    from bookings.models import Booking, Passenger, Payment
    from promotions.models import Promotion, NewsletterSubscription
    from destinations.models import Destination

    setup_test_environment()


def after_all(context):
    """
    Nettoyage global après l'exécution de tous les scénarios.

    - Détruit l'environnement de test Django
    """
    teardown_test_environment()


def before_scenario(context, scenario):
    """
    Préparation avant chaque scénario.

    - Vide toutes les tables de la base de données
    - Crée les données de test de référence
    - Initialise le client de test Django
    """
    # Réinitialise la base de données
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    tables = connection.introspection.table_names()
    for table in tables:
        cursor.execute(f'DELETE FROM "{table}";')
    # Réinitialise les auto-incréments (SQLite)
    for table in tables:
        cursor.execute(f'DELETE FROM sqlite_sequence WHERE name = "{table}";')
    cursor.execute("PRAGMA foreign_keys = ON;")
    connection.commit()

    # Peuple les données de test
    context.test_data = _populate_test_data()

    # Rend les données accessibles directement sur le contexte
    context.airports = context.test_data["airports"]
    context.aircraft = context.test_data["aircraft"]
    context.flights = context.test_data["flights"]
    context.test_user = context.test_data["user"]
    context.promotions = context.test_data["promotions"]

    # Initialise le client de test Django (comme dans les tests unitaires)
    from django.test import Client
    context.test = type('TestClient', (), {})()
    context.test.client = Client()


def after_scenario(context, scenario):
    """
    Nettoyage après chaque scénario.

    - Ferme les connexions à la base de données
    - Nettoie le contexte
    """
    # Ferme les connexions DB pour éviter les fuites
    for conn in connection._connections.values():
        conn.close_if_unusable_or_obsolete()

    # Nettoie le contexte
    if hasattr(context, "test_data"):
        del context.test_data
    if hasattr(context, "airports"):
        del context.airports
    if hasattr(context, "aircraft"):
        del context.aircraft
    if hasattr(context, "flights"):
        del context.flights
    if hasattr(context, "test_user"):
        del context.test_user
    if hasattr(context, "promotions"):
        del context.promotions
    if hasattr(context, "response"):
        del context.response
