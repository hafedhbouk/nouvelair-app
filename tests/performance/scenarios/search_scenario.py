# tests/performance/scenarios/search_scenario.py
from locust import HttpUser, task, between, TaskSet
import random
from tests.performance.config import ROUTES, DATES, SLO


class SearchTaskSet(TaskSet):
    """Ensemble de tâches pour le parcours de recherche de vols."""

    def on_start(self):
        """Exécuté une fois au démarrage de chaque utilisateur virtuel."""
        # Récupérer la page d'accueil pour initialiser la session + CSRF
        response = self.client.get('/')
        # Extraire le token CSRF depuis les cookies
        self.csrf_token = self.client.cookies.get('csrftoken', '')

    @task(5)
    def homepage(self):
        """Visite la page d'accueil — tâche la plus fréquente."""
        with self.client.get('/', catch_response=True, name='GET /') as r:
            if r.elapsed.total_seconds() * 1000 > SLO['homepage_p95_ms']:
                # Log la lenteur mais ne marque pas comme échec
                print(f'SLOW homepage: {r.elapsed.total_seconds()*1000:.0f}ms')
            if r.status_code != 200:
                r.failure(f'Homepage KO: {r.status_code}')

    @task(8)
    def search_one_way(self):
        """Recherche un vol aller simple — parcours le plus courant."""
        origin, destination = random.choice(ROUTES)
        date = random.choice(DATES)

        with self.client.post(
            '/search/',
            data={
                'origin': origin,
                'destination': destination,
                'departure_date': date,
                'trip_type': 'one_way',
                'csrfmiddlewaretoken': self.csrf_token,
            },
            headers={'Referer': 'http://127.0.0.1:8000/'},
            catch_response=True,
            name='POST /search/ [one_way]'
        ) as r:
            if r.status_code == 200:
                # Vérifier que des résultats sont présents
                if 'vol' not in r.text.lower() and 'flight' not in r.text.lower():
                    # Aucun résultat — pas une erreur mais un warning
                    pass
                r.success()
            elif r.status_code == 302:
                r.success()  # Redirection acceptée
            else:
                r.failure(f'Search KO: {r.status_code}')

    @task(3)
    def flight_detail(self):
        """Consulte le détail d'un vol (ID entre 1 et 50)."""
        flight_id = random.randint(1, 50)
        with self.client.get(
            f'/flight/{flight_id}/',
            catch_response=True,
            name='GET /flight/<pk>/'
        ) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 404:
                r.success()  # 404 attendu pour les IDs hors range
            else:
                r.failure(f'Flight detail KO: {r.status_code}')

    @task(4)
    def autocomplete(self):
        """Appelle l'API d'autocomplétion — simulant la frappe utilisateur."""
        queries = ['T', 'Tu', 'Tun', 'C', 'CD', 'CDG', 'P', 'Pa', 'Par']
        for q in random.choices(queries, k=3):
            self.client.get(
                f'/airport-autocomplete/?q={q}',
                headers={'X-Requested-With': 'XMLHttpRequest'},
                name='/airport-autocomplete/?q=[q]'
            )

    @task(1)
    def stop(self):
        """Arrête le TaskSet — simule l'abandon de l'utilisateur."""
        self.interrupt()


class AnonymousSearchUser(HttpUser):
    """Utilisateur anonyme — 55% du trafic NouvelAir."""
    tasks = [SearchTaskSet]
    wait_time = between(2, 5)
    weight = 11  # Correspond aux 55% de trafic