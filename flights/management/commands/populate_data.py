from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
import random

from flights.models import Airport, Aircraft, Flight
from destinations.models import Destination
from promotions.models import Promotion
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Peuple la base de donnees avec des donnees de test pour NouvelAir'

    def handle(self, *args, **options):
        self.stdout.write('=' * 50)
        self.stdout.write('NouvelAir - Creation des donnees de test')
        self.stdout.write('=' * 50)

        self._create_airports()
        self._create_aircrafts()
        self._create_flights()
        self._create_destinations()
        self._create_promotions()
        self._create_test_users()

        self.stdout.write(self.style.SUCCESS('\nDonnees de test creees avec succes !'))
        self.stdout.write('=' * 50)

    def _create_airports(self):
        airports = [
            ('TUN', 'Tunis-Carthage', 'Tunisie', 'TUN', 36.8510, 10.2272),
            ('JFK', 'John F. Kennedy', 'New York', 'USA', 40.6413, -73.7781),
            ('CDG', 'Charles de Gaulle', 'Paris', 'FRA', 49.0097, 2.5479),
            ('FCO', 'Fiumicino', 'Rome', 'ITA', 41.8003, 12.2389),
            ('CMN', 'Mohammed V', 'Casablanca', 'MAR', 33.3675, -7.5898),
            ('ALG', 'Houari Boumediene', 'Alger', 'ALG', 36.6940, 3.2154),
            ('DXB', 'Dubai International', 'Dubai', 'EAU', 25.2532, 55.3657),
            ('IST', 'Istanbul Airport', 'Istanbul', 'TUR', 41.2753, 28.7519),
            ('LHR', 'Heathrow', 'Londres', 'GBR', 51.4700, -0.4543),
            ('MUC', 'Munich Airport', 'Munich', 'ALL', 48.3537, 11.7750),
        ]
        for code, name, city, country, lat, lng in airports:
            Airport.objects.get_or_create(
                code=code,
                defaults={
                    'name': name, 'city': city, 'country': country,
                    'latitude': lat, 'longitude': lng
                }
            )
        self.stdout.write('  %d aeroports cres.' % Airport.objects.count())

    def _create_aircrafts(self):
        aircrafts = [
            ('TS-IPA', 'Airbus A320', 174, 12),
            ('TS-IPB', 'Airbus A330', 277, 24),
            ('TS-IPC', 'Boeing 737-800', 189, 0),
            ('TS-IPD', 'Boeing 787 Dreamliner', 242, 30),
        ]
        for registration, model_name, total, business in aircrafts:
            Aircraft.objects.get_or_create(
                registration=registration,
                defaults={
                    'model_name': model_name, 'total_seats': total,
                    'economy_seats': total - business,
                    'business_seats': business,
                    'is_active': True,
                }
            )
        self.stdout.write('  %d appareils cres.' % Aircraft.objects.count())

    def _create_flights(self):
        routes = [
            ('TUN', 'CDG'), ('TUN', 'JFK'), ('TUN', 'FCO'),
            ('TUN', 'CMN'), ('TUN', 'ALG'), ('TUN', 'DXB'),
            ('TUN', 'IST'), ('TUN', 'LHR'), ('TUN', 'MUC'),
        ]
        aircrafts = list(Aircraft.objects.all())
        if not aircrafts:
            self.stdout.write(self.style.ERROR('  Aucun appareil trouve !'))
            return
        flight_counter = 100

        for origin_code, dest_code in routes:
            origin = Airport.objects.get(code=origin_code)
            dest = Airport.objects.get(code=dest_code)

            for day_offset in range(0, 30, 2):
                departure = datetime.now() + timedelta(days=day_offset)
                for hour in [7, 12, 18][:random.randint(1, 3)]:
                    departure_time = departure.replace(
                        hour=hour,
                        minute=random.choice([0, 15, 30, 45]),
                        second=0, microsecond=0
                    )
                    duration_hours = random.uniform(1.5, 4.0)
                    arrival_time = departure_time + timedelta(hours=duration_hours)
                    aircraft = random.choice(aircrafts)
                    base_eco = random.uniform(180, 600)
                    base_biz = base_eco * random.uniform(2.2, 3.5)

                    Flight.objects.get_or_create(
                        flight_number='BJ%d' % flight_counter,
                        defaults={
                            'origin': origin, 'destination': dest,
                            'aircraft': aircraft,
                            'departure_time': departure_time,
                            'arrival_time': arrival_time,
                            'base_price_economy': round(base_eco, 2),
                            'base_price_business': round(base_biz, 2),
                            'available_seats_economy': max(0, aircraft.economy_seats - random.randint(0, 50)),
                            'available_seats_business': max(0, aircraft.business_seats - random.randint(0, 10)),
                            'status': 'scheduled',
                        }
                    )
                    flight_counter += 1

        self.stdout.write('  %d vols cres.' % Flight.objects.count())

    def _create_destinations(self):
        destinations = [
            ('Paris', 'paris', 'La Ville Lumiere', 'Decouvrez la tour Eiffel, le Louvre et bien plus encore.', 'Ville'),
            ('New York', 'new-york', 'La Grosse Pomme', 'Statue de la Liberte, Times Square, Central Park.', 'Ville'),
            ('Rome', 'rome', 'La Ville Eternelle', 'Colisee, Vatican, fontaine de Trevi.', 'Culture'),
            ('Casablanca', 'casablanca', 'Perle du Maroc', 'Mosquee Hassan II, medina, corniche.', 'Plage'),
            ('Istanbul', 'istanbul', 'Entre deux continents', 'Sainte-Sophie, Grand Bazar, Bosphore.', 'Culture'),
        ]
        for name, slug, short_desc, desc, cat in destinations:
            Destination.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name, 'short_description': short_desc,
                    'description': desc, 'category': cat,
                    'rating': round(random.uniform(3.5, 5.0), 1),
                    'is_featured': random.choice([True, False]),
                }
            )
        self.stdout.write('  %d destinations creees.' % Destination.objects.count())

    def _create_promotions(self):
        promos = [
            ('ETE25', 'Reduction ete', 25.0, '2025-06-01', '2025-08-31'),
            ('EARLY10', 'Reservation anticipee', 10.0, '2025-01-01', '2025-12-31'),
            ('WEEKEND', 'Offre week-end', 15.0, '2025-01-01', '2025-12-31'),
        ]
        for code, desc, pct, start, end in promos:
            Promotion.objects.get_or_create(
                code=code,
                defaults={
                    'description': desc, 'discount_percentage': pct,
                    'start_date': start, 'end_date': end,
                    'is_active': True,
                }
            )
        self.stdout.write('  %d promotions creees.' % Promotion.objects.count())

    def _create_test_users(self):
        from django.contrib.auth.models import User

        users_data = [
            ('admin', 'Admin', 'admin@nouvelair.tn', 'Admin', 'User', True),
            ('testuser', 'Test User', 'test@nouvelair.tn', 'Test', 'User', False),
        ]
        for username, first_name, email, last_name, dummy, is_staff in users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'first_name': first_name, 'last_name': last_name, 'is_staff': is_staff, 'is_active': True}
            )
            if created:
                user.set_password('NouvelAir2025!')
                user.save()
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'phone': '+216 71 000 000', 'city': 'Tunis', 'country': 'Tunisie'}
                )
                self.stdout.write('  Utilisateur "%s" cree (mot de passe: NouvelAir2025!)' % username)
            else:
                self.stdout.write('  Utilisateur "%s" existe deja.' % username)
