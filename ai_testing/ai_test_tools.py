"""
NouvelAir - Module d'Intégration IA pour les Tests
===================================================

Ce module fournit des outils d'intelligence artificielle pour automatiser
et améliorer le processus de test de l'application NouvelAir.

Fonctionnalités:
- Génération automatique de données de test
- Détection d'anomalies dans les résultats de tests
- Analyse de couverture de test
- Génération de rapports intelligents
"""

import os
import json
import random
import string
from datetime import date, timedelta
from typing import List, Dict, Any, Optional


class DataGenerator:
    """
    Générateur intelligent de données de test pour l'application NouvelAir.
    Utilise des algorithmes pour créer des données réalistes et variées.
    """

    FIRST_NAMES_MALE = ['Mohamed', 'Ahmed', 'Ali', 'Youssef', 'Karim',
                        'Omar', 'Sami', 'Nizar', 'Hamdi', 'Mehdi',
                        'Jean', 'Pierre', 'Paul', 'Michel', 'Philippe',
                        'Hans', 'Klaus', 'Werner', 'Franz', 'Stefan']

    FIRST_NAMES_FEMALE = ['Fatima', 'Amina', 'Leila', 'Sarra', 'Meriem',
                          'Nadia', 'Salma', 'Ines', 'Rania', 'Yasmine',
                          'Marie', 'Sophie', 'Claire', 'Isabelle', 'Catherine']

    LAST_NAMES = ['Ben Ali', 'Trabelsi', 'Bouazizi', 'Hamdi', 'Mansour',
                  'Jendoubi', 'Chaabane', 'Gharbi', 'Haddad', 'Saidi',
                  'Dupont', 'Martin', 'Bernard', 'Moreau', 'Petit',
                  'Mueller', 'Schmidt', 'Weber', 'Fischer', 'Wagner']

    COUNTRIES = ['Tunisie', 'France', 'Allemagne', 'Italie', 'Belgique',
                 'Canada', 'Libye', 'Algérie', 'Maroc', 'Suisse']

    CITIES = ['Tunis', 'Paris', 'Munich', 'Rome', 'Bruxelles',
              'Montréal', 'Tripoli', 'Alger', 'Casablanca', 'Genève']

    MEAL_PREFERENCES = ['', 'Standard', 'Végétarien', 'Sans porc',
                        'Halal', 'Casher', 'Sans gluten', 'Diabétique']

    def __init__(self, seed: Optional[int] = None):
        if seed:
            random.seed(seed)

    def generate_passenger_data(self, count: int = 1) -> List[Dict[str, Any]]:
        """Génère des données de passagers réalistes."""
        passengers = []
        for _ in range(count):
            is_female = random.random() > 0.5
            first_names = self.FIRST_NAMES_FEMALE if is_female else self.FIRST_NAMES_MALE
            title = 'mme' if is_female else 'mr'

            year = random.randint(1960, 2005)
            month = random.randint(1, 12)
            day = random.randint(1, 28)

            passengers.append({
                'title': title,
                'first_name': random.choice(first_names),
                'last_name': random.choice(self.LAST_NAMES),
                'date_of_birth': date(year, month, day).isoformat(),
                'nationality': random.choice(self.COUNTRIES),
                'passport_number': ''.join(random.choices(
                    string.ascii_uppercase + string.digits, k=9
                )),
                'passport_expiry': (date.today() + timedelta(days=random.randint(180, 3650))).isoformat(),
                'special_assistance': random.random() > 0.9,
                'meal_preference': random.choice(self.MEAL_PREFERENCES),
            })
        return passengers

    def generate_booking_data(self) -> Dict[str, Any]:
        """Génère des données de réservation complètes."""
        passengers_count = random.randint(1, 4)
        return {
            'contact_email': f"{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com",
            'contact_phone': f"+216{random.randint(10000000, 99999999)}",
            'passengers': self.generate_passenger_data(passengers_count),
            'special_requests': random.choice([
                '', 'Siège côté couloir', 'Repas végétarien',
                'Assistance wheelchair', 'Bébé voyageant'
            ]),
        }

    def generate_search_criteria(self) -> Dict[str, Any]:
        """Génère des critères de recherche de vol variés."""
        departure_date = date.today() + timedelta(days=random.randint(1, 90))
        return {
            'trip_type': random.choice(['oneway', 'roundtrip']),
            'origin': random.choice(['TUN', 'MIR', 'NBE', 'DJE']),
            'destination': random.choice(['CDG', 'ORY', 'MUC', 'FRA', 'CMN']),
            'departure_date': departure_date.isoformat(),
            'return_date': (departure_date + timedelta(days=random.randint(3, 14))).isoformat()
            if random.random() > 0.5 else None,
            'passengers': random.randint(1, 4),
            'travel_class': random.choice(['economy', 'business']),
        }

    def generate_user_data(self) -> Dict[str, str]:
        """Génère des données d'utilisateur pour les tests."""
        first_name = random.choice(self.FIRST_NAMES_MALE + self.FIRST_NAMES_FEMALE)
        last_name = random.choice(self.LAST_NAMES)
        username = f"{first_name.lower()}.{last_name.lower()}".replace(' ', '.')
        username = f"{username}{random.randint(1, 999)}"
        return {
            'username': username,
            'password': f"TestPass{random.randint(100, 999)}!",
            'email': f"{username}@example.com",
            'first_name': first_name,
            'last_name': last_name,
        }

    def generate_bulk_test_data(self, scenarios: int = 10) -> List[Dict[str, Any]]:
        """Génère un ensemble complet de scénarios de test."""
        data = []
        for _ in range(scenarios):
            data.append({
                'search_criteria': self.generate_search_criteria(),
                'booking': self.generate_booking_data(),
                'user': self.generate_user_data(),
            })
        return data


class AnomalyDetector:
    """
    Détecteur d'anomalies dans les résultats de tests.
    Identifie les patterns inhabituels qui pourraient indiquer des bugs.
    """

    def __init__(self, test_results: List[Dict[str, Any]]):
        self.results = test_results
        self.anomalies = []

    def detect_performance_anomalies(self, threshold_seconds: float = 5.0) -> List[Dict]:
        """Détecte les tests anormalement lents."""
        anomalies = []
        for result in self.results:
            if result.get('duration', 0) > threshold_seconds:
                anomalies.append({
                    'type': 'performance',
                    'test': result.get('name', 'Unknown'),
                    'duration': result['duration'],
                    'message': f"Test trop lent: {result['duration']:.2f}s > {threshold_seconds}s"
                })
        return anomalies

    def detect_failure_patterns(self) -> Dict[str, Any]:
        """Analyse les patterns d'échec."""
        failures = [r for r in self.results if not r.get('passed', True)]
        error_messages = {}
        for failure in failures:
            msg = failure.get('error', 'Unknown error')
            error_messages[msg] = error_messages.get(msg, 0) + 1

        return {
            'total_failures': len(failures),
            'error_distribution': error_messages,
            'most_common_error': max(error_messages.items(), key=lambda x: x[1])[0]
            if error_messages else None
        }

    def detect_coverage_gaps(self, tested_modules: List[str],
                             all_modules: List[str]) -> List[str]:
        """Identifie les modules non testés."""
        return list(set(all_modules) - set(tested_modules))

    def generate_report(self) -> Dict[str, Any]:
        """Génère un rapport d'analyse complet."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get('passed', True))
        failed = total - passed

        return {
            'summary': {
                'total_tests': total,
                'passed': passed,
                'failed': failed,
                'pass_rate': (passed / total * 100) if total > 0 else 0,
            },
            'performance_anomalies': self.detect_performance_anomalies(),
            'failure_analysis': self.detect_failure_patterns(),
        }


class CoverageAnalyzer:
    """
    Analyseur de couverture de tests.
    Évalue la couverture des tests par module, fonctionnalité et type de test.
    """

    MODULES = ['flights', 'bookings', 'accounts', 'destinations', 'promotions']

    TEST_TYPES = ['unit', 'integration', 'functional', 'e2e']

    FEATURES = {
        'flights': ['search', 'detail', 'airport_list', 'autocomplete'],
        'bookings': ['create', 'confirm', 'cancel', 'lookup', 'my_bookings'],
        'accounts': ['register', 'login', 'logout', 'profile'],
        'destinations': ['list', 'detail'],
        'promotions': ['list', 'detail', 'newsletter'],
    }

    def __init__(self, test_registry: Dict[str, List[str]]):
        """
        Args:
            test_registry: Dictionnaire {module: [liste des features testées]}
        """
        self.registry = test_registry

    def calculate_coverage(self) -> Dict[str, Any]:
        """Calcule la couverture de test par module."""
        coverage = {}
        for module in self.MODULES:
            tested = set(self.registry.get(module, []))
            total = set(self.FEATURES.get(module, []))
            if total:
                rate = len(tested & total) / len(total) * 100
            else:
                rate = 0
            coverage[module] = {
                'tested': list(tested),
                'total': list(total),
                'missing': list(total - tested),
                'rate': round(rate, 1),
            }
        return coverage

    def generate_recommendations(self, coverage: Dict[str, Any]) -> List[str]:
        """Génère des recommandations pour améliorer la couverture."""
        recommendations = []
        for module, data in coverage.items():
            if data['missing']:
                recommendations.append(
                    f"[{module}] Features non testées: {', '.join(data['missing'])}"
                )
            if data['rate'] < 80:
                recommendations.append(
                    f"[{module}] Couverture insuffisante ({data['rate']}%). "
                    f"Recommandation: ajouter des tests pour {', '.join(data['missing'])}"
                )
        return recommendations

    def generate_html_report(self, coverage: Dict[str, Any],
                             recommendations: List[str]) -> str:
        """Génère un rapport HTML de couverture."""
        html = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <title>Rapport de Couverture - NouvelAir</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #1a237e; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
                th { background: #1a237e; color: white; }
                .low { color: #c62828; }
                .medium { color: #f57f17; }
                .high { color: #2e7d32; }
                .rec { background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Rapport de Couverture de Tests - NouvelAir</h1>
            <table>
                <tr><th>Module</th><th>Couverture</th><th>Testé</th><th>Manquant</th></tr>
        """
        for module, data in coverage.items():
            cls = 'low' if data['rate'] < 50 else ('medium' if data['rate'] < 80 else 'high')
            html += f"""
                <tr>
                    <td>{module}</td>
                    <td class="{cls}">{data['rate']}%</td>
                    <td>{', '.join(data['tested']) or '-'}</td>
                    <td>{', '.join(data['missing']) or '-'}</td>
                </tr>
            """
        html += "</table>"

        if recommendations:
            html += "<h2>Recommandations</h2>"
            for rec in recommendations:
                html += f'<div class="rec">{rec}</div>'

        html += "</body></html>"
        return html


# ============================================
# Point d'entrée pour l'exécution en ligne de commande
# ============================================

def main():
    """Fonction principale pour l'exécution des outils IA de test."""
    import argparse

    parser = argparse.ArgumentParser(description="NouvelAir AI Testing Tools")
    subparsers = parser.add_subparsers(dest='command', help='Commande')

    # Commande: generate
    gen_parser = subparsers.add_parser('generate', help='Générer des données de test')
    gen_parser.add_argument('--type', choices=['passenger', 'booking', 'search', 'user', 'all'],
                            default='all', help='Type de données')
    gen_parser.add_argument('--count', type=int, default=10, help='Nombre de scénarios')
    gen_parser.add_argument('--output', '-o', help='Fichier de sortie JSON')

    # Commande: analyze
    analyze_parser = subparsers.add_parser('analyze', help='Analyser les résultats de tests')
    analyze_parser.add_argument('--input', '-i', required=True, help='Fichier JSON des résultats')

    # Commande: coverage
    coverage_parser = subparsers.add_parser('coverage', help='Analyser la couverture de tests')
    coverage_parser.add_argument('--output', '-o', help='Fichier HTML de sortie')

    args = parser.parse_args()

    if args.command == 'generate':
        gen = DataGenerator()
        if args.type == 'all':
            data = gen.generate_bulk_test_data(args.count)
        elif args.type == 'passenger':
            data = gen.generate_passenger_data(args.count)
        elif args.type == 'booking':
            data = [gen.generate_booking_data() for _ in range(args.count)]
        elif args.type == 'search':
            data = [gen.generate_search_criteria() for _ in range(args.count)]
        elif args.type == 'user':
            data = [gen.generate_user_data() for _ in range(args.count)]

        output = json.dumps(data, indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Données générées: {args.output}")
        else:
            print(output)

    elif args.command == 'analyze':
        with open(args.input, 'r', encoding='utf-8') as f:
            results = json.load(f)
        detector = AnomalyDetector(results)
        report = detector.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))

    elif args.command == 'coverage':
        analyzer = CoverageAnalyzer({
            'flights': ['search', 'detail', 'airport_list', 'autocomplete'],
            'bookings': ['create', 'confirm', 'cancel', 'lookup', 'my_bookings'],
            'accounts': ['register', 'login', 'logout', 'profile'],
            'destinations': ['list', 'detail'],
            'promotions': ['list', 'detail', 'newsletter'],
        })
        coverage = analyzer.calculate_coverage()
        recommendations = analyzer.generate_recommendations(coverage)
        report_html = analyzer.generate_html_report(coverage, recommendations)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report_html)
            print(f"Rapport de couverture: {args.output}")
        else:
            print(report_html)


if __name__ == '__main__':
    main()
