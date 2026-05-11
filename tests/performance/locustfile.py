"""
Locust file pour les tests de charge NouvelAir — Jour 8.

Simule le comportement réel des utilisateurs sur le site NouvelAir:
- Navigation sur les pages publiques (accueil, destinations, promotions)
- Recherche de vols et autocomplétion des aéroports
- Accès aux pages protégées (mes réservations, recherche de réservation)
- Authentification automatique des utilisateurs virtuels

Dépendances:
    pip install locust

Exécution:
    cd D:/NouvelAirApp/nouvelair_project/    locust -f tests/performance/locustfile.py --host=http://127.0.0.1:8000

    Ou sans interface web (headless):
    locust -f tests/performance/locustfile.py --host=http://127.0.0.1:8000            --headless -u 50 -r 5 -t 5m --html=reports/performance/load_test.html
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import json
import logging
import time

logger = logging.getLogger(__name__)


# ── Compteurs de métriques personnalisés ─────────────────────────────────────

custom_metrics = {
    "search_requests": 0,
    "booking_requests": 0,
    "auth_requests": 0,
    "total_errors": 0,
    "total_requests": 0,
}


# ── Event hooks pour métriques personnalisées ────────────────────────────────

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Hook appelé à chaque requête pour collecter des métriques personnalisées.

    Args:
        request_type: Type de requête (GET, POST, etc.)
        name: Nom de la tâche/endpoint
        response_time: Temps de réponse en ms
        response_length: Taille de la réponse en octets
        exception: Exception si la requête a échoué
    """
    custom_metrics["total_requests"] += 1

    if name and "search" in name.lower():
        custom_metrics["search_requests"] += 1
    elif name and "booking" in name.lower():
        custom_metrics["booking_requests"] += 1
    elif name and ("login" in name.lower() or "auth" in name.lower()):
        custom_metrics["auth_requests"] += 1

    if exception:
        custom_metrics["total_errors"] += 1
        logger.warning(
            "Requête échouée: %s %s — %.0f ms — %s",
            request_type, name, response_time, str(exception)
        )


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Hook appelé à la fin du test pour afficher les métriques résumées.

    Args:
        environment: Environnement Locust
    """
    print("\n" + "=" * 60)
    print("  MÉTRIQUES PERSONNALISÉES — NOUVELAIR")
    print("=" * 60)
    print(f"  Requêtes totales         : {custom_metrics['total_requests']}")
    print(f"  Requêtes de recherche    : {custom_metrics['search_requests']}")
    print(f"  Requêtes de réservation  : {custom_metrics['booking_requests']}")
    print(f"  Requêtes d\'authentification: {custom_metrics['auth_requests']}")
    print(f"  Erreurs totales          : {custom_metrics['total_errors']}")

    if custom_metrics["total_requests"] > 0:
        error_rate = (custom_metrics["total_errors"] / custom_metrics["total_requests"]) * 100
        print(f"  Taux d\'erreur            : {error_rate:.2f}%")
    print("=" * 60 + "\n")


# ── Comportement de navigation ───────────────────────────────────────────────

class BrowsingBehavior:
    """
    Comportement de navigation type « visiteur curieux ».

    L'utilisateur parcourt les pages publiques du site, consulte
    les destinations et les promotions sans effectuer de recherche.
    """

    def __init__(self, client):
        self.client = client

    def browse_homepage(self):
        """Navigue vers la page d'accueil."""
        self.client.get("/")

    def view_destinations(self):
        """Consulte la page des destinations."""
        self.client.get("/destinations/")

    def view_promotions(self):
        """Consulte la page des promotions."""
        self.client.get("/promotions/")


class SearchingBehavior:
    """
    Comportement de recherche type « voyageur ».

    L'utilisateur effectue des recherches de vols, utilise
    l'autocomplétion des aéroports et consulte les résultats.
    """

    def __init__(self, client):
        self.client = client

    def search_airports(self):
        """Consulte la liste des aéroports disponibles."""
        self.client.get("/flights/aeroports/")

    def airport_autocomplete_tunis(self):
        """Teste l'autocomplétion avec la requête TUN."""
        with self.client.get(
            "/api/airports/autocomplete/?q=TUN",
            name="/api/airports/autocomplete/?q=TUN",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure("Réponse JSON invalide: attendu une liste")
                except json.JSONDecodeError:
                    response.failure("Réponse non-JSON")
            else:
                response.failure(f"Status code: {response.status_code}")

    def airport_autocomplete_paris(self):
        """Teste l'autocomplétion avec la requête PAR."""
        with self.client.get(
            "/api/airports/autocomplete/?q=PAR",
            name="/api/airports/autocomplete/?q=PAR",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure("Réponse JSON invalide: attendu une liste")
                except json.JSONDecodeError:
                    response.failure("Réponse non-JSON")
            else:
                response.failure(f"Status code: {response.status_code}")

    def airport_autocomplete_empty(self):
        """Teste l'autocomplétion avec une requête vide."""
        self.client.get(
            "/api/airports/autocomplete/?q=",
            name="/api/airports/autocomplete/?q=(empty)"
        )


class BookingBehavior:
    """
    Comportement de réservation type « client enregistré ».

    L'utilisateur connecté accède à ses réservations et
    utilise la fonctionnalité de recherche de réservation.
    """

    def __init__(self, client):
        self.client = client

    def view_my_bookings(self):
        """Consulte la page « Mes réservations »."""
        with self.client.get(
            "/bookings/mes-reservations/",
            name="/bookings/mes-reservations/",
            catch_response=True
        ) as response:
            # 302 = redirection vers login si non authentifié, 200 = OK
            if response.status_code in (200, 302):
                response.success()
            else:
                response.failure(f"Status inattendu: {response.status_code}")

    def booking_lookup_page(self):
        """Consulte la page de recherche de réservation."""
        self.client.get("/bookings/recherche/")

    def view_legal_pages(self):
        """Consulte les mentions légales et CGV."""
        self.client.get("/mentions-legales/", name="/mentions-legales/")
        self.client.get("/conditions-generales/", name="/conditions-generales/")


# ── Utilisateur Locust principal ─────────────────────────────────────────────

class NouvelAirUser(HttpUser):
    """
    Utilisateur virtuel Locust simulant le comportement d'un visiteur NouvelAir.

    Pondération des tâches (weight):
        - Homepage: 5 (page la plus visitée)
        - Destinations: 3
        - Promotions: 3
        - Recherche aéroports: 2
        - Autocomplétion TUN: 2
        - Autocomplétion PAR: 1
        - Mes réservations: 1
        - Recherche réservation: 1

    Temps de réflexion (think time): 1 à 3 secondes entre chaque requête.
    """

    wait_time = between(1, 3)
    host = "http://127.0.0.1:8000"

    def on_start(self):
        """
        Initialisation de l'utilisateur virtuel.

        Tente de se connecter avec un compte de test pour accéder
        aux pages protégées. Si la connexion échoue, l'utilisateur
        continuera en mode visiteur anonyme.
        """
        self.browsing = BrowsingBehavior(self.client)
        self.searching = SearchingBehavior(self.client)
        self.booking = BookingBehavior(self.client)
        self.is_authenticated = False

        # Tentative de connexion
        try:
            self.client.get("/accounts/connexion/", name="/accounts/connexion/ [GET]")
            csrftoken = self.client.cookies.get("csrftoken", "")

            response = self.client.post(
                "/accounts/connexion/",
                {
                    "username": "mytestuser",
                    "password": "NouvelAir2025!",
                    "csrfmiddlewaretoken": csrftoken,
                },
                name="/accounts/connexion/ [POST]",
            )

            # Vérifier si la connexion a réussi (redirection vers l'accueil)
            if response.status_code in (200, 302):
                self.is_authenticated = True
                logger.info("Utilisateur virtuel connecté avec succès")
            else:
                logger.warning(
                    "Connexion échouée (status: %d), mode visiteur activé",
                    response.status_code,
                )
        except Exception as e:
            logger.warning("Erreur lors de la connexion: %s", str(e))

    # ─── Tâches de navigation (pages publiques) ────────────────────────

    @task(5)
    def browse_homepage(self):
        """
        [Weight 5] Navigation vers la page d'accueil.

        C'est la tâche la plus fréquente car c'est le point d'entrée
        principal du site. Chaque visiteur passe au moins une fois
        par cette page.
        """
        with self.client.get("/", name="/ [Homepage]", catch_response=True) as response:
            if response.status_code == 200:
                # Vérifier que la page contient du contenu significatif
                if len(response.text) > 500:
                    response.success()
                else:
                    response.failure("Page d'accueil trop légère (< 500 octets)")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def view_destinations(self):
        """
        [Weight 3] Consultation de la page des destinations.

        Les voyageurs consultent fréquemment les destinations
        disponibles pour planifier leurs voyages.
        """
        with self.client.get(
            "/destinations/", name="/destinations/", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def view_promotions(self):
        """
        [Weight 3] Consultation de la page des promotions.

        Les offres promotionnelles attirent de nombreux visiteurs
        cherchant des bonnes affaires.
        """
        with self.client.get(
            "/promotions/", name="/promotions/", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    # ─── Tâches de recherche ───────────────────────────────────────────

    @task(2)
    def search_airports(self):
        """
        [Weight 2] Consultation de la liste des aéroports.

        Utilisée lors de la planification de voyage pour identifier
        les aéroports de départ et d'arrivée.
        """
        self.searching.search_airports()

    @task(2)
    def airport_autocomplete_tun(self):
        """
        [Weight 2] Autocomplétion avec la requête « TUN ».

        Simule la saisie de l'utilisateur dans le champ de recherche
        d'aéroport. Tunis (TUN) est l'aéroport principal.
        """
        self.searching.airport_autocomplete_tunis()

    @task(1)
    def airport_autocomplete_par(self):
        """
        [Weight 1] Autocomplétion avec la requête « PAR ».

        Simule une recherche vers Paris, destination populaire
        depuis la Tunisie.
        """
        self.searching.airport_autocomplete_par()

    @task(1)
    def airport_autocomplete_empty(self):
        """
        [Weight 1] Autocomplétion avec requête vide.

        Teste le comportement du serveur avec une entrée vide,
        simulant un utilisateur qui efface le champ de recherche.
        """
        self.searching.airport_autocomplete_empty()

    # ─── Tâches de réservation (nécessitent l'auth) ────────────────────

    @task(1)
    def view_my_bookings(self):
        """
        [Weight 1] Consultation de « Mes réservations ».

        Page protégée accessible uniquement aux utilisateurs connectés.
        """
        self.booking.view_my_bookings()

    @task(1)
    def booking_lookup(self):
        """
        [Weight 1] Page de recherche de réservation.

        Permet de retrouver une réservation via sa référence et email.
        Accessible sans authentification.
        """
        self.booking.booking_lookup_page()

    # ─── Tâches secondaires ────────────────────────────────────────────

    @task(1)
    def view_legal_pages(self):
        """
        [Weight 1] Consultation des pages légales.

        Mentions légales et conditions générales de vente.
        Peu fréquent mais nécessaire pour la conformité.
        """
        self.booking.view_legal_pages()

    @task(1)
    def view_registration(self):
        """
        [Weight 1] Consultation de la page d'inscription.

        Nouveaux visiteurs intéressés par la création d'un compte.
        """
        self.client.get("/accounts/inscription/", name="/accounts/inscription/")
