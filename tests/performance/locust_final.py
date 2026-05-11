# tests/performance/locustfile.py — Version complète
from locust import HttpUser, task, between, LoadTestShape
from locust import events
import random, time, csv, os
from tests.performance.scenarios.search_scenario import AnonymousSearchUser
from tests.performance.scenarios.auth_scenario import AuthenticatedUser
from tests.performance.config import SLO, LOAD_PROFILES


# ── Utilisateur Consultation Réservations ────────────────────
class BookingLookupUser(HttpUser):
    """Utilisateur consultation réservation — 10% du trafic."""
    wait_time = between(5, 15)
    weight = 2

    @task
    def lookup_booking(self):
        self.client.post('/booking/lookup/', data={
            'booking_reference': f'NV{random.randint(10000, 99999)}',
        }, name='POST /booking/lookup/')


# ── Shape Personnalisé pour Load Test Progressif ─────────────
class ProgressiveLoadShape(LoadTestShape):
    """
    Shape (profil) de montée en charge progressive.
    Simule un trafic réel : montée progressive, plateau, descente.

    Étapes :
    0-60s   : 0  → 20 users  (warm-up)
    60-180s : 20 → 100 users (montée normale)
    180-360s: 100 users      (plateau — phase de mesure principale)
    360-420s: 100 → 20 users (descente)
    420-480s: 20  → 0 users  (cool-down)
    """
    stages = [
        {'duration': 60,  'users': 20,  'spawn_rate': 1},   # Warm-up
        {'duration': 180, 'users': 100, 'spawn_rate': 5},   # Montée
        {'duration': 360, 'users': 100, 'spawn_rate': 0},   # Plateau
        {'duration': 420, 'users': 20,  'spawn_rate': 10},  # Descente
        {'duration': 480, 'users': 0,   'spawn_rate': 10},  # Cool-down
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage['duration']:
                return stage['users'], stage['spawn_rate']
        return None  # Fin du test


# ── Event hooks pour assertions automatiques ─────────────────
@events.quitting.add_listener
def check_slo_compliance(environment, **kwargs):
    """Vérifie les SLOs à la fin du test et retourne un exit code non-nul si KO."""
    stats = environment.stats
    failures = []

    for name, stat in stats.entries.items():
        # Vérification P95
        p95_ms = stat.get_response_time_percentile(0.95)
        if '/search/' in name[0] and p95_ms and p95_ms > SLO['search_p95_ms']:
            failures.append(f'SLO BREACH: {name[0]} P95={p95_ms}ms > {SLO["search_p95_ms"]}ms')
        if name[0] == '/' and p95_ms and p95_ms > SLO['homepage_p95_ms']:
            failures.append(f'SLO BREACH: homepage P95={p95_ms}ms > {SLO["homepage_p95_ms"]}ms')

    # Taux d'erreur global
    total = stats.total
    if total.num_requests > 0:
        error_rate = (total.num_failures / total.num_requests) * 100
        if error_rate > SLO['max_error_rate_pct']:
            failures.append(f'SLO BREACH: Error rate={error_rate:.2f}% > {SLO["max_error_rate_pct"]}%')

    if failures:
        print('\n⛔ SLO VIOLATIONS DÉTECTÉES :')
        for f in failures:
            print(f'  ❌ {f}')
        environment.process_exit_code = 1
    else:
        print('\n✅ Tous les SLOs sont respectés.')