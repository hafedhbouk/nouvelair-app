# tests/performance/scenarios/auth_scenario.py
from locust import HttpUser, task, between, events
import random
from tests.performance.config import TEST_USER, SLO


class AuthenticatedUser(HttpUser):
    """
    Utilisateur connecté — 25% du trafic.
    Se connecte au démarrage, maintient la session, effectue des réservations.
    """
    wait_time = between(3, 8)  # Utilisateurs plus lents (réflexion avant réservation)
    weight = 5

    def on_start(self):
        """Connexion au démarrage de l'utilisateur virtuel."""
        self._login()

    def _login(self):
        """Procédure de connexion avec gestion du CSRF."""
        # Étape 1 : Récupérer la page login pour obtenir le CSRF token
        response = self.client.get('/accounts/login/')
        self.csrf_token = self.client.cookies.get('csrftoken', '')

        # Étape 2 : Soumettre le formulaire de connexion
        login_response = self.client.post(
            '/accounts/login/',
            data={
                'username': TEST_USER['username'],
                'password': TEST_USER['password'],
                'csrfmiddlewaretoken': self.csrf_token,
            },
            headers={'Referer': 'http://127.0.0.1:8000/accounts/login/'},
            allow_redirects=True,
            name='POST /accounts/login/'
        )
        # Mise à jour du CSRF après login
        self.csrf_token = self.client.cookies.get('csrftoken', '')
        self.is_logged_in = login_response.status_code == 200

    @task(4)
    def search_and_view_flight(self):
        """Cherche un vol et consulte son détail."""
        from tests.performance.config import ROUTES, DATES
        origin, destination = random.choice(ROUTES)
        date = random.choice(DATES)

        self.client.post('/search/', data={
            'origin': origin, 'destination': destination,
            'departure_date': date, 'trip_type': 'one_way',
            'csrfmiddlewaretoken': self.csrf_token,
        }, name='POST /search/ [auth]')

        # Consulter le détail d'un vol trouvé
        flight_id = random.randint(1, 30)
        self.client.get(f'/flight/{flight_id}/', name='GET /flight/<pk>/ [auth]')

    @task(2)
    def create_booking(self):
        """Tente de créer une réservation — scénario critique."""
        if not self.is_logged_in:
            self._login()
            return

        flight_id = random.randint(1, 20)
        with self.client.post(
            f'/booking/create/{flight_id}/',
            data={
                'first_name': 'Ahmed',
                'last_name': 'Ben Ali',
                'passport_number': f'TN{random.randint(100000, 999999)}',
                'date_of_birth': '1990-05-15',
                'nationality': 'TN',
                'seat_class': 'economy',
                'csrfmiddlewaretoken': self.csrf_token,
            },
            catch_response=True,
            allow_redirects=True,
            name='POST /booking/create/<id>/'
        ) as r:
            if r.status_code in [200, 302]:
                r.success()
            elif r.status_code == 404:
                r.success()  # Vol non trouvé — attendu pour les IDs hors range
            else:
                r.failure(f'Booking KO: {r.status_code}')

    @task(1)
    def view_profile(self):
        """Consulte le profil utilisateur."""
        with self.client.get('/accounts/profile/', catch_response=True) as r:
            if r.status_code in [200, 302]:
                r.success()
            else:
                r.failure(f'Profile KO: {r.status_code}')

    def on_stop(self):
        """Déconnexion à la fin de la simulation."""
        self.client.get('/accounts/logout/', name='GET /accounts/logout/')