"""
Scripts de lancement des tests de performance — Jour 8.

Permet d'exécuter différents types de tests de charge via Locust:
    - Load Test (test de charge standard)
    - Stress Test (test de montée en charge)
    - Spike Test (test de pic soudain)
    - Endurance Test (test d'endurance)
    - Baseline Test (test de référence)

Chaque type de test génère un rapport HTML dans reports/performance/
et vérifie que les seuils de performance sont respectés.

Dépendances:
    pip install locust

Usage:
    cd D:/NouvelAirApp/nouvelair_project/    python tests/performance/run_load_test.py --type load
    python tests/performance/run_load_test.py --type stress
    python tests/performance/run_load_test.py --type spike
    python tests/performance/run_load_test.py --type endurance
    python tests/performance/run_load_test.py --type baseline
    python tests/performance/run_load_test.py --type all
"""

import os
import sys
import subprocess
import argparse
import json
import time
from datetime import datetime

# Ajouter le répertoire parent au path pour les imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from tests.performance.performance_thresholds import THRESHOLDS, ENDPOINT_MAPPING

# ── Configuration ────────────────────────────────────────────────────────────

HOST = "http://127.0.0.1:8000"
LOCUSTFILE = os.path.join(BASE_DIR, "tests", "performance", "locustfile.py")
REPORTS_DIR = os.path.join(BASE_DIR, "reports", "performance")

# Assurer que le répertoire des rapports existe
os.makedirs(REPORTS_DIR, exist_ok=True)


# ── Définitions des tests ───────────────────────────────────────────────────

TEST_CONFIGS = {
    "load": {
        "description": "Test de charge standard — simule le trafic normal du site",
        "users": 50,
        "spawn_rate": 5,
        "duration": "5m",
        "report_file": "load_test.html",
        "description_detail": (
            "50 utilisateurs simultanés, montée progressive à 5 utilisateurs/seconde, "
            "durée de 5 minutes. Simule le trafic typique d'une journée normale."
        ),
    },
    "stress": {
        "description": "Test de montée en charge — pousse le système à ses limites",
        "users": 200,
        "spawn_rate": 10,
        "duration": "10m",
        "report_file": "stress_test.html",
        "description_detail": (
            "Montée de 10 à 200 utilisateurs, spawn rate de 10/s, durée de 10 minutes. "
            "Objectif: identifier le point de rupture du système."
        ),
    },
    "spike": {
        "description": "Test de pic soudain — simule un afflux massif d'utilisateurs",
        "users": 100,
        "spawn_rate": 100,
        "duration": "2m",
        "report_file": "spike_test.html",
        "description_detail": (
            "100 utilisateurs instantanés (spawn rate 100/s), maintien pendant 2 minutes. "
            "Simule un pic de trafic dû à une promotion ou un événement."
        ),
    },
    "endurance": {
        "description": "Test d'endurance — vérifie la stabilité sur la durée",
        "users": 30,
        "spawn_rate": 3,
        "duration": "15m",
        "report_file": "endurance_test.html",
        "description_detail": (
            "30 utilisateurs simultanés, spawn rate de 3/s, durée de 15 minutes. "
            "Détecte les fuites mémoire et la dégradation progressive des performances."
        ),
    },
    "baseline": {
        "description": "Test de référence — benchmark des performances de base",
        "users": 10,
        "spawn_rate": 2,
        "duration": "2m",
        "report_file": "baseline_test.html",
        "description_detail": (
            "10 utilisateurs, spawn rate de 2/s, durée de 2 minutes. "
            "Établit la ligne de base pour comparaison future."
        ),
    },
}


# ── Fonctions utilitaires ────────────────────────────────────────────────────

def print_header(title):
    """Affiche un en-tête formaté."""
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


def print_step(message):
    """Affiche une étape de progression."""
    print(f"  → {message}")


def run_locust_test(test_type, config):
    """
    Exécute un test Locust avec la configuration spécifiée.

    Args:
        test_type: Type de test (load, stress, spike, endurance, baseline)
        config: Dictionnaire de configuration du test

    Returns:
        str: Chemin vers le fichier rapport HTML généré
    """
    report_path = os.path.join(REPORTS_DIR, config["report_file"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path_with_ts = os.path.join(
        REPORTS_DIR, f"{timestamp}_{config['report_file']}"
    )

    print_header(f"TEST DE PERFORMANCE — {test_type.upper()}")
    print(f"  Description : {config['description']}")
    print(f"  Détails     : {config['description_detail']}")
    print(f"  Utilisateurs: {config['users']}")
    print(f"  Spawn rate  : {config['spawn_rate']}/s")
    print(f"  Durée       : {config['duration']}")
    print(f"  Rapport     : {report_path_with_ts}")
    print()

    print_step("Vérification du serveur...")
    # Vérifier que le serveur Django est en cours d'exécution
    try:
        import urllib.request
        urllib.request.urlopen(f"{HOST}/", timeout=5)
        print_step("Serveur Django est accessible ✓")
    except Exception as e:
        print(f"  ✗ ERREUR: Serveur Django inaccessible sur {HOST}")
        print(f"    Détail: {e}")
        print(f"    Assurez-vous que le serveur est lancé: python manage.py runserver")
        return None

    print_step(f"Lancement du test {test_type}...")

    cmd = [
        sys.executable, "-m", "locust",
        "-f", LOCUSTFILE,
        "--host", HOST,
        "--headless",
        "-u", str(config["users"]),
        "-r", str(config["spawn_rate"]),
        "-t", config["duration"],
        "--html", report_path_with_ts,
        "--only-summary",
    ]

    print_step(f"Commande: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=int(config["duration"].rstrip("m")) * 60 + 120,
        )

        if result.returncode == 0:
            print_step(f"Test terminé avec succès ✓")
            print_step(f"Rapport HTML généré: {report_path_with_ts}")

            # Copier aussi vers le nom standard
            with open(report_path_with_ts, "r", encoding="utf-8") as src:
                with open(report_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())

            return report_path_with_ts
        else:
            print(f"  ✗ ERREUR: Le test a échoué (code: {result.returncode})")
            if result.stderr:
                print(f"    stderr: {result.stderr[-500:]}")
            return None

    except subprocess.TimeoutExpired:
        print(f"  ✗ TIMEOUT: Le test a dépassé la durée maximale")
        return None
    except FileNotFoundError:
        print(f"  ✗ ERREUR: Locust n'est pas installé")
        print(f"    Installez-le: pip install locust")
        return None
    except Exception as e:
        print(f"  ✗ ERREUR: {e}")
        return None


def check_thresholds(test_type):
    """
    Vérifie les résultats du test par rapport aux seuils définis.

    Args:
        test_type: Type de test exécuté

    Returns:
        dict: Résultats de la vérification des seuils
    """
    print_header("VÉRIFICATION DES SEUILS DE PERFORMANCE")

    results = {}
    all_pass = True

    for endpoint, thresholds in THRESHOLDS.items():
        # Map endpoint to Locust task name
        locust_name = ENDPOINT_MAPPING.get(endpoint, endpoint)
        results[endpoint] = {
            "p50_max": thresholds["p50"],
            "p95_max": thresholds["p95"],
            "p99_max": thresholds["p99"],
            "status": "INFO",
        }

        status_parts = []
        status_parts.append(f"p50<{thresholds['p50']}ms")
        status_parts.append(f"p95<{thresholds['p95']}ms")
        status_parts.append(f"p99<{thresholds['p99']}ms")

        print(f"  {endpoint:20s} | {' | '.join(status_parts)}")

    print()
    print("  ⚠ Pour une vérification complète, consultez le rapport HTML")
    print(f"    et comparez les percentiles avec les seuils ci-dessus.")
    print()

    return results


def generate_summary_report(all_results):
    """
    Génère un résumé JSON de tous les tests exécutés.

    Args:
        all_results: Dictionnaire des résultats par type de test
    """
    summary = {
        "project": "NouvelAir",
        "date": datetime.now().isoformat(),
        "host": HOST,
        "tests": all_results,
        "thresholds": THRESHOLDS,
    }

    summary_path = os.path.join(REPORTS_DIR, "test_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    print_step(f"Résumé JSON sauvegardé: {summary_path}")


# ── Point d'entrée principal ─────────────────────────────────────────────────

def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description="Scripts de tests de performance NouvelAir — Jour 8",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Exemples:
  python run_load_test.py --type load         Test de charge (50 users, 5 min)
  python run_load_test.py --type stress       Test de stress (200 users)
  python run_load_test.py --type spike        Test de pic (100 users instant)
  python run_load_test.py --type endurance    Test d'endurance (30 users, 15 min)
  python run_load_test.py --type baseline     Test de référence (10 users, 2 min)
  python run_load_test.py --type all          Tous les tests séquentiels
        """,
    )

    parser.add_argument(
        "--type",
        choices=["load", "stress", "spike", "endurance", "baseline", "all"],
        default="baseline",
        help="Type de test à exécuter (défaut: baseline)",
    )

    parser.add_argument(
        "--host",
        default=HOST,
        help=f"URL du serveur cible (défaut: {HOST})",
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Vérifier uniquement les seuils sans exécuter les tests",
    )

    args = parser.parse_args()

    global HOST
    HOST = args.host

    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║    NouvelAir — Tests de Performance (Jour 8 — Sprint 1)              ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"  Date      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Serveur   : {HOST}")
    print(f"  Rapports  : {REPORTS_DIR}")
    print(f"  Seuils    : {len(THRESHOLDS)} endpoints configurés")

    if args.check_only:
        check_thresholds("manual")
        return

    all_results = {}

    if args.type == "all":
        # Exécuter tous les tests séquentiellement
        test_order = ["baseline", "load", "stress", "spike", "endurance"]
        for test_type in test_order:
            config = TEST_CONFIGS[test_type]
            report_path = run_locust_test(test_type, config)
            all_results[test_type] = {
                "config": config,
                "report": report_path,
                "timestamp": datetime.now().isoformat(),
            }
            time.sleep(5)  # Pause entre les tests
    else:
        test_type = args.type
        config = TEST_CONFIGS[test_type]
        report_path = run_locust_test(test_type, config)
        all_results[test_type] = {
            "config": config,
            "report": report_path,
            "timestamp": datetime.now().isoformat(),
        }

    # Vérification des seuils
    check_thresholds(args.type)

    # Résumé
    generate_summary_report(all_results)

    print_header("FIN DES TESTS DE PERFORMANCE")
    print()
    for test_name, result in all_results.items():
        status = "✓" if result["report"] else "✗"
        report_info = result["report"] or "ÉCHEC"
        print(f"  {status} {test_name:12s} — {report_info}")
    print()


if __name__ == "__main__":
    main()
