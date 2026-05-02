# tests/unit/test_flights_tdd.py
import pytest
from datetime import datetime
from django.utils import timezone

from tests.factories import FlightFactory


@pytest.mark.django_db
@pytest.mark.unit
class TestFlightDurationDisplay:

    def test_get_duration_display_returns_hours_and_minutes(self):
        """Un vol de 2h30 doit afficher "2h 30min"."""
        departure = timezone.make_aware(datetime(2026, 6, 1, 10, 0))
        arrival = timezone.make_aware(datetime(2026, 6, 1, 12, 30))
        flight = FlightFactory(departure_time=departure, arrival_time=arrival)
        assert flight.get_duration_display() == "2h 30min"

    def test_get_duration_display_exact_hours(self):
        """Un vol de 3h00 doit afficher "3h"."""
        departure = timezone.make_aware(datetime(2026, 6, 1, 10, 0))
        arrival = timezone.make_aware(datetime(2026, 6, 1, 13, 0))
        flight = FlightFactory(departure_time=departure, arrival_time=arrival)
        assert flight.get_duration_display() == "3h"

    def test_get_duration_display_returns_short_flight(self):
        """Un vol de 45 minutes doit afficher "45min"."""
        departure = timezone.make_aware(datetime(2026, 6, 1, 10, 0))
        arrival = timezone.make_aware(datetime(2026, 6, 1, 10, 45))
        flight = FlightFactory(departure_time=departure, arrival_time=arrival)
        assert flight.get_duration_display() == "45min"

    def test_get_duration_display_returns_long_haul_flight(self):
        """Un vol de 10h15 doit afficher "10h 15min"."""
        departure = timezone.make_aware(datetime(2026, 6, 1, 10, 0))
        arrival = timezone.make_aware(datetime(2026, 6, 1, 20, 15))
        flight = FlightFactory(departure_time=departure, arrival_time=arrival)
        assert flight.get_duration_display() == "10h 15min"
