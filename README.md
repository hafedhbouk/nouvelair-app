# 🛫 NouvelAir — Système de Réservation Aérienne

![CI Pipeline](https://img.shields.io/github/actions/workflow/status/nouvelair/nouvelair_project/tests.yml?branch=main&style=flat-square&label=CI)
![Coverage](https://img.shields.io/badge/Coverage-83%25-brightgreen?style=flat-square)
![Security](https://img.shields.io/badge/Security-0%20HIGH-green?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square)
![Django](https://img.shields.io/badge/Django-4.2-green?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-250%2B-orange?style=flat-square)
![License](https://img.shields.io/badge/License-Educational-yellow?style=flat-square)

> Application web complète de réservation de vols développée dans le cadre d'une
> formation intensive en **Test/QA, Automatisation et Intelligence Artificielle**.

## 📋 Table des matières

- [Description](#-description)
- [Architecture du projet](#-architecture-du-projet)
- [Prérequis et installation](#-prérequis-et-installation)
- [Exécution des tests](#-exécution-des-tests)
- [Couverture de code](#-couverture-de-code)
- [Pipeline CI/CD](#-pipeline-cicd)
- [Métriques de qualité](#-métriques-de-qualité)
- [Programme de formation](#-programme-de-formation)
- [Licence](#-licence)

---

## 📖 Description

**NouvelAir** est un système de réservation aérienne complet développé avec le framework
Django 4.2. Le projet sert de **fil rouge** pour une formation de 10 jours couvrant
les tests logiciels, l'automatisation, la sécurité et l'intégration de l'IA.

### Fonctionnalités principales

| Module | Description |
|--------|-------------|
| **flights** | Recherche de vols, gestion des aéroports et aéronefs, autocomplétion API |
| **bookings** | Réservation multi-passagers, paiements, suivi en temps réel |
| **accounts** | Inscription, connexion, profil utilisateur, gestion de compte |
| **destinations** | Catalogue de destinations touristiques avec avis et filtrage |
| **promotions** | Codes promotionnels, offres spéciales, newsletter |
| **ai_testing** | Outils IA pour la génération et l'analyse de tests |

---

## 🏗 Architecture du projet

```
nouvelair_project/
├── manage.py                          # Point d'entrée Django
├── requirements.txt                   # Dépendances production
├── requirements_test.txt              # Dépendances de test
├── README.md                          # Ce fichier
├── .gitignore                         # Fichiers ignorés par Git
├── .flake8                            # Configuration Flake8
├── .pylintrc                          # Configuration Pylint
├── pytest.ini                         # Configuration Pytest
│
├── nouvelair/                         # Configuration du projet Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── context_processors.py
│   └── static/
│       ├── css/style.css
│       └── js/main.js
│
├── flights/                           # App : Gestion des vols
│   ├── models.py                      # Airport, Aircraft, Flight
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── signals.py
│   ├── apps.py
│   ├── templates/flights/
│   └── tests/test_models.py
│
├── bookings/                          # App : Réservations
│   ├── models.py                      # Booking, Passenger, Payment
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── apps.py
│   └── templates/bookings/
│
├── accounts/                          # App : Comptes utilisateurs
│   ├── models.py                      # UserProfile, SavedDestination
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── signals.py
│   ├── admin.py
│   └── templates/accounts/
│
├── destinations/                      # App : Destinations touristiques
│   ├── models.py                      # Destination, DestinationImage, DestinationReview
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── templates/destinations/
│
├── promotions/                        # App : Promotions & Newsletter
│   ├── models.py                      # Promotion, NewsletterSubscription
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── templates/promotions/
│
├── ai_testing/                        # Module IA pour les tests
│   ├── ai_test_tools.py               # Outils IA (génération, détection)
│   └── tests_e2e.py                   # Tests E2E avec Selenium
│
├── tests/                             # Suite de tests complète
│   ├── unit/                          # Tests unitaires (pytest)
│   │   ├── __init__.py
│   │   ├── test_models_flights.py
│   │   ├── test_models_bookings.py
│   │   ├── test_models_accounts.py
│   │   ├── test_models_promotions.py
│   │   └── test_models_utils.py
│   ├── integration/                   # Tests d'intégration (Django Test Client)
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_views_flights.py
│   │   ├── test_views_bookings.py
│   │   ├── test_views_accounts.py
│   │   ├── test_views_destinations.py
│   │   └── test_views_promotions.py
│   ├── api/                           # Tests API (endpoints REST)
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth_api.py
│   │   ├── test_booking_api.py
│   │   ├── test_autocomplete_api.py
│   │   └── test_newsletter_api.py
│   ├── e2e/                           # Tests End-to-End (Playwright)
│   │   └── test_e2e_scenarios.py
│   ├── performance/                   # Tests de performance (Locust)
│   │   ├── __init__.py
│   │   ├── locustfile.py
│   │   ├── run_load_test.py
│   │   └── performance_thresholds.py
│   ├── security/                      # Tests de sécurité
│   │   ├── __init__.py
│   │   ├── run_security_scan.py
│   │   ├── test_owasp_top10.py
│   │   └── test_security_manual.py
│   ├── factories.py                   # Factory Boy factories
│   └── test_regression.py             # Tests de régression
│
├── features/                          # Scénarios BDD (Gherkin/Behave)
│   ├── search_flights.feature
│   ├── booking_management.feature
│   ├── user_authentication.feature
│   ├── newsletter.feature
│   └── steps/
│       └── test_steps.py
│
├── docs/                              # Documentation du projet
│   ├── final_report_sprint2.md
│   ├── final_report_global.md
│   ├── certification_guide.md
│   ├── coverage_report_sprint1.md
│   ├── sprint1_metrics_template.md
│   └── retrospective_sprint1_template.md
│
├── reports/                           # Rapports générés
│   ├── final_summary.html
│   ├── performance/
│   └── security/
│
├── scripts/                           # Scripts utilitaires
│   ├── populate_test_data.py
│   ├── demo_sprint_review.py
│   └── generate_final_summary.py
│
├── .github/                           # Configuration CI/CD
│   └── workflows/
│       └── tests.yml
│
└── fixtures/                          # Données initiales
    └── initial_data.json
```

---

## 🛠 Prérequis et installation

### Prérequis

| Outil | Version minimale |
|-------|-----------------|
| Python | 3.12+ |
| Django | 4.2 |
| pip | Dernière version |
| Git | 2.x |

### Installation

```bash
# 1. Cloner ou extraire le projet
cd D:\NouvelairApp\nouvelair_project

# 2. Créer un environnement virtuel
python -m venv venv

# 3. Activer l'environnement virtuel
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Linux/macOS

# 4. Installer les dépendances de production
pip install -r requirements.txt

# 5. Installer les dépendances de test
pip install -r requirements_test.txt

# 6. Appliquer les migrations de la base de données
python manage.py migrate

# 7. Peupler les données de test
python scripts/populate_test_data.py

# 8. Créer le super-utilisateur (optionnel)
python manage.py createsuperuser

# 9. Lancer le serveur de développement
python manage.py runserver
```

L'application est accessible sur : **http://127.0.0.1:8000/**

### Comptes de test

| Rôle | Utilisateur | Mot de passe |
|------|------------|-------------|
| Utilisateur standard | `testuser` | `TestPass123!` |
| Administrateur | `admin` | `TestPass123!` |

---

## ✅ Exécution des tests

### Tests unitaires (pytest)

```bash
# Exécuter tous les tests unitaires
pytest tests/unit/ -v

# Exécuter les tests unitaires d'une application
pytest tests/unit/test_models_flights.py -v
pytest tests/unit/test_models_bookings.py -v

# Avec rapport détaillé
pytest tests/unit/ -v --tb=short
```

### Tests d'intégration (pytest + Django Test Client)

```bash
# Exécuter tous les tests d'intégration
pytest tests/integration/ -v

# Par application
pytest tests/integration/test_views_flights.py -v
pytest tests/integration/test_views_bookings.py -v
```

### Tests BDD (Behave)

```bash
# Exécuter tous les scénarios BDD
behave features/ --tags=sprint1,sprint2 -f pretty

# Exécuter un fichier feature spécifique
behave features/search_flights.feature -f pretty
```

### Tests API (pytest)

```bash
# Exécuter tous les tests API
pytest tests/api/ -v

# Tests d'authentification API
pytest tests/api/test_auth_api.py -v

# Tests d'autocomplétion
pytest tests/api/test_autocomplete_api.py -v
```

### Tests End-to-End (Playwright)

```bash
# Exécuter tous les tests E2E
pytest tests/e2e/ -v --browser chromium

# Avec captures d'écran en cas d'échec
pytest tests/e2e/ -v --browser chromium --screenshot=on
```

### Tests de performance (Locust)

```bash
# Lancer le serveur Django en arrière-plan
python manage.py runserver 0.0.0.0:8000 &

# Test de charge standard (50 utilisateurs, 5 minutes)
locust -f tests/performance/locustfile.py --host=http://127.0.0.1:8000 \
       --headless -u 50 -r 5 -t 5m --html=reports/performance/load_test.html

# Test de stress (200 utilisateurs)
python tests/performance/run_load_test.py --type stress

# Test de pic (100 utilisateurs instantanés)
python tests/performance/run_load_test.py --type spike

# Vérifier les seuils uniquement
python tests/performance/run_load_test.py --check-only
```

### Tests de sécurité

```bash
# Exécuter la suite complète de sécurité
pytest tests/security/ -v

# Scan Bandit (analyse statique)
bandit -r . -f screen

# Scan Safety (dépendances vulnérables)
safety check

# Scan complet automatisé
python tests/security/run_security_scan.py
```

---

## 📊 Couverture de code

### Commande de couverture

```bash
# Rapport terminal
pytest --cov=. --cov-report=term-missing

# Rapport HTML
pytest --cov=. --cov-report=html

# Couverture par application
pytest --cov=flights --cov=bookings --cov=accounts --cov=destinations --cov=promotions --cov-report=term-missing

# Couverture avec seuil minimum (échec si < 80%)
pytest --cov=. --cov-fail-under=80
```

### Objectifs de couverture

| Application | Cible | Priorité |
|-------------|-------|----------|
| `flights` | ≥ 85% | 🔴 Haute |
| `accounts` | ≥ 85% | 🔴 Haute |
| `bookings` | ≥ 80% | 🔴 Haute |
| `destinations` | ≥ 80% | 🟡 Moyen |
| `promotions` | ≥ 75% | 🟡 Moyen |
| **Global** | **≥ 80%** | — |

---

## 🔄 Pipeline CI/CD

Le projet utilise **GitHub Actions** avec un pipeline de **8 jobs** :

| # | Job | Description | Dépendances |
|---|-----|-------------|-------------|
| 1 | **Linting** | flake8 + pylint | — |
| 2 | **Tests unitaires** | pytest + coverage (matrix Python 3.10/3.11/3.12) | lint |
| 3 | **Tests d'intégration** | Django Test Client + JUnit XML | lint |
| 4 | **Tests BDD** | Behave avec tags sprint1/sprint2 | lint |
| 5 | **Tests E2E** | Playwright + captures d'écran | unit + integration |
| 6 | **Tests de performance** | Locust headless + seuils | unit + integration |
| 7 | **Tests de sécurité** | Bandit + Safety | lint |
| 8 | **Analyse SonarQube** | Qualité du code, couverture | lint |

### Déclencheurs

- **Push** sur `main`, `sprint1`, `sprint2`
- **Pull Request** vers `main`

### Configuration SonarQube

Pour activer l'analyse SonarQube, configurez ces secrets GitHub :

- `SONAR_TOKEN` : Token d'authentification SonarQube
- `SONAR_HOST_URL` : URL de votre serveur SonarQube (ex: `https://sonarcloud.io`)
- `SONAR_PROJECT_KEY` : Clé du projet (optionnel, défaut: `nouvelair-project`)

### Fichier de configuration

Le fichier `.sonar-project.properties` à la racine du projet configure l'analyse :

```properties
sonar.projectKey=nouvelair-project
sonar.sources=bookings,destinations,flights,nouvelair
sonar.python.coverage.reportPaths=coverage.xml
```

### Consultation

Les rapports CI sont disponibles dans l'onglet **Actions** du dépôt GitHub et via
les **artifacts** uploadés à chaque exécution.

---

## 📈 Métriques de qualité

### Résumé global

| Métrique | Valeur | Statut |
|----------|--------|--------|
| Tests unitaires | 75+ | ✅ |
| Tests d'intégration | 35+ | ✅ |
| Tests BDD (Behave) | 15 scénarios | ✅ |
| Tests API | 30+ | ✅ |
| Tests E2E (Playwright) | 26 | ✅ |
| Tests de performance | 5 scénarios (Locust) | ✅ |
| Tests de sécurité | 16+ (OWASP Top 10) | ✅ |
| Tests de régression | 20+ | ✅ |
| **Total** | **250+ tests** | ✅ |
| Couverture de code | **> 80%** | ✅ |
| CI/CD | **100% vert** | ✅ |
| Bugs documentés et résolus | **7+** | ✅ |

### Répartition des tests par type

```
                    ┌─────────────────┐
                    │   E2E (26)      │
                    │   Playwright     │
                  ┌─┤                 │
                  │ └─────────────────┘
                  │ ┌─────────────────┐
                  │ │  Sécurité (16+) │
                ┌─┤ │  OWASP Top 10   │
                │ │ └─────────────────┘
                │ │ ┌─────────────────┐
              ┌─┤ ├─┤  API (30+)      │
              │ │ │ │  Endpoints REST │
            ┌─┤ │ │ └─────────────────┘
            │ │ │ │ ┌─────────────────┐
            │ │ ├─┤ │ BDD (15)        │
          ┌─┤ │ │ │ │ Behave/Gherkin  │
          │ │ │ │ │ └─────────────────┘
          │ │ │ │ │ ┌─────────────────┐
        ┌─┤ │ │ ├─┤ │ Intégration (35+)│
        │ │ │ │ │ │ │ Django Client    │
        │ │ │ │ │ │ └─────────────────┘
        │ │ │ │ │ │ ┌─────────────────┐
      ┌─┤ │ │ │ ├─┤ │ Unitaires (75+)  │
      │ │ │ │ │ │ │ │ pytest           │
      │ │ │ │ │ │ │ └─────────────────┘
      │ │ │ │ │ │ │ ┌─────────────────┐
      │ │ │ │ │ │ │ │ Régression (20+) │
      │ │ │ │ │ │ │ └─────────────────┘
```

---

## 🎓 Programme de formation

Cette formation de **10 jours** est organisée en **2 sprints** :

### Sprint 1 — Fondamentaux (Jours 1-5)

| Jour | Thème | Livrables |
|------|-------|-----------|
| 1 | Setup, architecture, modèles Django | Structure du projet, 6 apps Django |
| 2 | Vues, templates, formulaires | Pages complètes, navigation |
| 3 | Tests unitaires + couverture | pytest, factories, coverage |
| 4 | Tests d'intégration + BDD | Django Test Client, Behave/Gherkin |
| 5 | Tests API + rétrospective Sprint 1 | Endpoints REST, métriques |

### Sprint 2 — Avancé (Jours 6-10)

| Jour | Thème | Livrables |
|------|-------|-----------|
| 6 | Tests E2E avec Playwright | 26 scénarios automatisés |
| 7 | Tests de performance (Locust) | 5 types de charge, seuils |
| 8 | Tests de sécurité (OWASP) | Bandit, Safety, 16+ tests |
| 9 | CI/CD GitHub Actions + régression | Pipeline 7 jobs, 20+ tests |
| 10 | **Sprint Review + Demo + Closure** | Rapports, dashboard, certification |

---

## 📜 Licence

Projet éducatif — Formation **Test/QA, Automatisation et Intelligence Artificielle**

© 2025 — Tous droits réservés pour usage pédagogique uniquement.

---

*Documentation générée automatiquement par `setup_jour10.py` — Jour 10*
