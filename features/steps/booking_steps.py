"""
booking_steps.py — Définitions d'étapes Behave pour la gestion des réservations.
================================================================================

Scénarios couverts :
    - US-008 : Création de réservation connecté
    - US-009 : Consultation de réservation
    - US-010 : Annulation de réservation pending
    - Recherche par référence et nom de famille
    - Réservation nécessite une connexion
"""

from behave import given, when, then
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date

from django.contrib.auth.models import User
from flights.models import Flight
from bookings.models import Booking, Passenger, Payment


# ── GIVEN : Préconditions ────────────────────────────────────────────────────


@given(r'un vol est disponible pour la réservation')
def step_flight_available(context):
    """Récupère un vol disponible pour la réservation."""
    flight = Flight.objects.filter(
        status="scheduled",
        is_active=True,
        available_seats_economy__gte=1,
        departure_time__gt=timezone.now(),
    ).first()
    assert flight is not None, "Aucun vol disponible pour la réservation"
    context.booking_flight = flight

    # Prépare la session avec les paramètres de recherche
    session = context.test.client.session
    session["search_params"] = {
        "origin": flight.origin.code,
        "destination": flight.destination.code,
        "departure_date": flight.departure_time.strftime("%Y-%m-%d"),
        "return_date": None,
        "passengers": "1",
        "travel_class": "economy",
        "trip_type": "oneway",
    }
    session["booking_flight_id"] = flight.pk
    session.save()


@given(r'une réservation "([^"]+)" existe pour mon compte')
def step_booking_exists_for_account(context, reference_label):
    """Crée une réservation pour l'utilisateur connecté."""
    user = context.logged_in_user
    flight = Flight.objects.filter(status="scheduled").first()
    assert flight is not None, "Aucun vol disponible"

    booking = Booking.objects.create(
        user=user,
        contact_email=user.email,
        contact_phone="+21612345678",
        status="confirmed",
        total_amount=flight.base_price_economy,
    )
    Passenger.objects.create(
        booking=booking,
        flight=flight,
        title="mr",
        first_name=user.first_name,
        last_name=user.last_name,
        date_of_birth=date(1990, 1, 15),
        nationality="Tunisienne",
        travel_class="economy",
        price=flight.base_price_economy,
    )
    Payment.objects.create(
        booking=booking,
        amount=flight.base_price_economy,
        method="credit_card",
        status="completed",
        transaction_id=f"SIM-{booking.short_reference}",
    )
    context.booking = booking
    context.booking_reference = booking.reference


@given(r'une réservation avec le statut "([^"]+)" existe')
def step_booking_with_status(context, status):
    """Crée une réservation avec un statut spécifique."""
    user = context.logged_in_user
    flight = Flight.objects.filter(status="scheduled").first()

    booking = Booking.objects.create(
        user=user,
        contact_email=user.email,
        contact_phone="+21612345678",
        status=status,
        total_amount=250.00,
    )
    Passenger.objects.create(
        booking=booking,
        flight=flight,
        title="mr",
        first_name=user.first_name,
        last_name=user.last_name,
        date_of_birth=date(1990, 1, 15),
        nationality="Tunisienne",
        travel_class="economy",
        price=250.00,
    )
    context.booking = booking
    context.booking_reference = booking.reference


@given(r'une réservation pour "([^"]+)" avec la référence "([^"]+)" existe')
def step_booking_for_lastname(context, last_name, ref_label):
    """Crée une réservation pour un nom de famille spécifique."""
    user = User.objects.get(username="testuser")
    flight = Flight.objects.filter(status="scheduled").first()

    booking = Booking.objects.create(
        user=user,
        contact_email=user.email,
        contact_phone="+21612345678",
        status="confirmed",
        total_amount=250.00,
    )
    Passenger.objects.create(
        booking=booking,
        flight=flight,
        title="mr",
        first_name="Jean",
        last_name=last_name,
        date_of_birth=date(1990, 1, 15),
        nationality="Française",
        travel_class="economy",
        price=250.00,
    )
    context.booking = booking
    context.booking_reference = booking.reference
    context.booking_last_name = last_name


# ── WHEN : Actions ───────────────────────────────────────────────────────────


@when(r'je réserve le vol avec les informations passager valides')
def step_create_booking(context):
    """Crée une réservation avec des données de passager valides."""
    flight = getattr(context, "booking_flight", None)
    if not flight:
        flight = Flight.objects.filter(status="scheduled").first()

    # S'assurer que la session est bien configurée
    session = context.test.client.session
    session["search_params"] = {
        "origin": flight.origin.code,
        "destination": flight.destination.code,
        "departure_date": flight.departure_time.strftime("%Y-%m-%d"),
        "return_date": None,
        "passengers": "1",
        "travel_class": "economy",
        "trip_type": "oneway",
    }
    session["booking_flight_id"] = flight.pk
    session.save()

    booking_count_before = Booking.objects.count()

    form_data = {
        "0-title": "mr",
        "0-first_name": "Jean",
        "0-last_name": "Dupont",
        "0-date_of_birth": "1990-01-15",
        "0-nationality": "Française",
        "0-passport_number": "AB123456",
        "0-passport_expiry": "2030-01-15",
        "0-special_assistance": "",
        "0-meal_preference": "",
        "contact_email": "jean.dupont@example.com",
        "contact_phone": "+33612345678",
        "special_requests": "",
    }

    context.response = context.test.client.post(
        reverse("bookings:create"), data=form_data
    )
    context.booking_count_before = booking_count_before


@when(r'je réserve le vol')
def step_create_booking_simple(context):
    """Tente de créer une réservation (sans données complètes)."""
    context.response = context.test.client.get(
        reverse("bookings:create")
    )


@when(r'j\'annule la réservation')
def step_cancel_booking(context):
    """Annule la réservation en cours."""
    booking = context.booking
    context.response = context.test.client.post(
        reverse("bookings:cancel", kwargs={"reference": booking.reference})
    )


@when(r'j\'essaie d\'annuler la réservation')
def step_try_cancel_booking(context):
    """Tente d'annuler la réservation (peut échouer)."""
    booking = context.booking
    context.response = context.test.client.post(
        reverse("bookings:cancel", kwargs={"reference": booking.reference})
    )


@when(
    r'je recherche la réservation avec la référence "([^"]+)" '
    r'et le nom "([^"]+)"'
)
def step_lookup_booking(context, ref_label, last_name):
    """Recherche une réservation par référence et nom de famille."""
    booking = context.booking
    short_ref = booking.short_reference

    form_data = {
        "reference": short_ref,
        "email": booking.contact_email,
    }
    context.response = context.test.client.post(
        reverse("bookings:lookup"), data=form_data
    )


# ── THEN : Vérifications ────────────────────────────────────────────────────


@then(r'la réservation est créée avec succès')
def step_booking_created(context):
    """Vérifie qu'une réservation a été créée."""
    assert Booking.objects.count() > context.booking_count_before, (
        "Aucune réservation n'a été créée"
    )
    context.booking = Booking.objects.latest("created_at")


@then(r'la réservation a le statut "([^"]+)"')
def step_booking_status(context, expected_status):
    """Vérifie le statut de la réservation."""
    booking = context.booking
    booking.refresh_from_db()
    assert booking.status == expected_status, (
        f"Le statut de la réservation est '{booking.status}', "
        f"attendu '{expected_status}'"
    )


@then(r'un numéro de référence est généré')
def step_reference_generated(context):
    """Vérifie qu'un numéro de référence a été généré."""
    booking = context.booking
    assert booking.reference is not None, "Aucune référence générée"
    assert str(booking.reference)[:8], "La référence est vide"


@then(r'je vois la réservation "([^"]+)" dans la liste')
def step_see_booking_in_list(context, ref_label):
    """Vérifie qu'une réservation est visible dans la liste."""
    assert context.response.status_code == 200
    if "bookings" in context.response.context:
        bookings = list(context.response.context["bookings"])
        assert len(bookings) >= 1, "Aucune réservation dans la liste"
        assert context.booking in bookings, (
            "La réservation attendue n'est pas dans la liste"
        )


@then(r'la réservation est annulée')
def step_booking_cancelled(context):
    """Vérifie que la réservation a été annulée."""
    context.booking.refresh_from_db()
    assert context.booking.status == "cancelled", (
        f"La réservation n'est pas annulée, statut : {context.booking.status}"
    )


@then(r'le statut de la réservation est "([^"]+)"')
def step_status_is(context, status):
    """Vérifie le statut de la réservation."""
    context.booking.refresh_from_db()
    assert context.booking.status == status, (
        f"Statut inattendu : {context.booking.status} (attendu : {status})"
    )


@then(r'la réservation reste avec le statut "([^"]+)"')
def step_status_remains(context, status):
    """Vérifie que le statut n'a pas changé."""
    context.booking.refresh_from_db()
    assert context.booking.status == status, (
        f"Le statut a changé : {context.booking.status} (attendu : {status})"
    )


@then(r'je suis redirigé vers la page de détail de la réservation')
def step_redirected_to_detail(context):
    """Vérifie la redirection vers la page de détail de la réservation."""
    assert context.response.status_code in (301, 302), (
        f"Pas de redirection, statut : {context.response.status_code}"
    )
    assert context.response.url == reverse(
        "bookings:detail", kwargs={"reference": context.booking.reference}
    ), f"Redirection incorrecte : {context.response.url}"
