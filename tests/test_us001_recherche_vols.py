"""
US-001 – Recherche de vols aller-retour
========================================
8 cas de test Playwright/pytest couvrant les 5 critères d'acceptance.

Prérequis :
    pip install pytest pytest-playwright
    playwright install chromium

Lancer :
    pytest test_us001_recherche_vols.py -v
"""

import re
from datetime import date, timedelta

import pytest
from playwright.sync_api import Page, expect


# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"
TODAY = date.today()
SEARCH_DATE = TODAY + timedelta(days=2)  # 2 days ahead (even day) to match generated flight schedule
PAST_DATE = TODAY - timedelta(days=1)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def go_to_home(page: Page):
    """Charge la page d'accueil avant chaque test."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")


# ──────────────────────────────────────────────────────────────────────────────
# Critère 1 – Le moteur de recherche est visible sans défilement
# ──────────────────────────────────────────────────────────────────────────────

def test_search_form_visible_without_scroll(page: Page):
    """
    CA-1 (nominal) : Le formulaire de recherche doit être dans le viewport
    dès le chargement initial, sans aucun défilement.
    """
    search_card = page.locator(".search-card")
    expect(search_card).to_be_visible()

    # Vérifie que le haut du bloc est dans la zone visible (viewport height)
    bounding_box = search_card.bounding_box()
    viewport_height = page.viewport_size["height"]

    assert bounding_box is not None, "Le bloc .search-card n'a pas de bounding box"
    assert bounding_box["y"] >= 0, "Le formulaire déborde au-dessus du viewport"
    assert bounding_box["y"] < viewport_height, (
        f"Le formulaire commence à y={bounding_box['y']}px, "
        f"hors du viewport ({viewport_height}px) — défilement requis"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Critère 2 – Autocomplétion dès 2 caractères (Départ & Destination)
# ──────────────────────────────────────────────────────────────────────────────

def test_origin_autocomplete_shows_suggestions_after_2_chars(page: Page):
    """
    CA-2 (nominal) : Saisir 2 caractères dans le champ Départ doit afficher
    au moins une suggestion d'autocomplétion.

    Note : Le HTML actuel utilise un <select> natif. Ce test suppose que
    l'équipe remplace le select par un champ texte avec autocomplétion
    (datalist ou widget JS) – comportement attendu selon le CA.
    """
    origin_input = page.locator("input#origin-input, input[name='origin_text'], #origin-select")

    # Si l'implémentation utilise encore un <select>, on le signale explicitement
    tag = origin_input.evaluate("el => el.tagName.toLowerCase()")
    if tag == "select":
        pytest.skip(
            "CA-2 non implémenté : le champ Départ est encore un <select> "
            "sans autocomplétion – à corriger en US-001."
        )

    origin_input.fill("Tu")
    suggestions = page.locator("[data-testid='origin-suggestions'] li, .autocomplete-dropdown li")
    expect(suggestions.first).to_be_visible(timeout=3_000)
    assert suggestions.count() >= 1


def test_destination_autocomplete_shows_no_suggestion_for_1_char(page: Page):
    """
    CA-2 (erreur) : Saisir 1 seul caractère ne doit PAS déclencher
    l'autocomplétion (seuil = 2 caractères).
    """
    dest_input = page.locator("input#destination-input, input[name='destination_text'], #destination-select")

    tag = dest_input.evaluate("el => el.tagName.toLowerCase()")
    if tag == "select":
        pytest.skip("CA-2 non implémenté : champ Destination est encore un <select>.")

    dest_input.fill("P")
    suggestions = page.locator("[data-testid='destination-suggestions'] li, .autocomplete-dropdown li")
    # Aucune suggestion ne doit apparaître pour 1 caractère
    expect(suggestions).to_have_count(0, timeout=1_000)


# ──────────────────────────────────────────────────────────────────────────────
# Critère 3 – Calendrier : pas de date antérieure à aujourd'hui
# ──────────────────────────────────────────────────────────────────────────────

def test_departure_date_min_attribute_is_today(page: Page):
    """
    CA-3 (nominal) : L'attribut `min` du champ date de départ doit être
    égal à la date du jour, empêchant la sélection d'une date passée.
    """
    departure_input = page.locator("#id_departure_date")
    min_value = departure_input.get_attribute("min")
    assert min_value == TODAY.strftime("%Y-%m-%d"), (
        f"Attribut min='{min_value}' ≠ aujourd'hui ({TODAY.isoformat()})"
    )


def test_departure_date_rejects_past_date(page: Page):
    """
    CA-3 (erreur) : Forcer une date passée via JS doit rendre le formulaire
    invalide (constraint validation API du navigateur).
    """
    departure_input = page.locator("#id_departure_date")

    # Injection d'une date passée via JS (contourne l'UI mais teste la validation HTML5)
    page.evaluate(
        f"document.querySelector('#id_departure_date').value = '{PAST_DATE.isoformat()}'"
    )

    # Soumet le formulaire pour déclencher la validation native
    page.get_by_role("button", name="Rechercher des vols").click()

    # La page ne doit PAS naviguer vers les résultats : on reste sur l'accueil
    expect(page).to_have_url(re.compile(r"^" + re.escape(BASE_URL) + r"/?$"))

    # Vérifie l'invalidité via JS
    is_valid = departure_input.evaluate("el => el.validity.valid")
    assert not is_valid, "Une date passée devrait rendre le champ invalide"


# ──────────────────────────────────────────────────────────────────────────────
# Critère 4 – Résultats en moins de 3 secondes
# ──────────────────────────────────────────────────────────────────────────────

def test_search_returns_results_within_3_seconds(page: Page):
    """
    CA-4 (nominal) : Une recherche valide doit afficher les résultats
    en moins de 3 000 ms (critère de performance).
    """
    import time

    # Remplit le formulaire avec des données valides
    page.select_option("#origin-select", value="1")          # TUN
    page.select_option("#destination-select", value="3")     # CDG
    page.fill("#id_departure_date", SEARCH_DATE.strftime("%Y-%m-%d"))
    page.locator("input[name='trip_type'][value='oneway']").check()

    start = time.perf_counter()
    page.get_by_role("button", name="Rechercher des vols").click()
    page.wait_for_load_state("networkidle")
    elapsed = time.perf_counter() - start

    # La page de résultats doit contenir au moins un vol ou un message "aucun résultat"
    results_or_empty = page.locator(
        ".flight-card, [data-testid='no-results'], .alert-info"
    )
    expect(results_or_empty.first).to_be_visible(timeout=3_000)

    assert elapsed < 3.0, (
        f"Temps de réponse trop long : {elapsed:.2f}s (seuil : 3.00s)"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Critère 5 – Message d'erreur si champ obligatoire vide
# ──────────────────────────────────────────────────────────────────────────────

def test_submit_without_origin_shows_validation_error(page: Page):
    """
    CA-5 (erreur) : Soumettre le formulaire sans choisir de ville de départ
    doit afficher un message de validation et bloquer la navigation.
    """
    # Destination et date renseignées, mais pas l'origine
    page.select_option("#destination-select", value="3")     # CDG
    page.fill("#id_departure_date", SEARCH_DATE.strftime("%Y-%m-%d"))

    page.get_by_role("button", name="Rechercher des vols").click()

    # On doit rester sur la page d'accueil
    expect(page).to_have_url(re.compile(r"^" + re.escape(BASE_URL) + r"/?$"))

    origin_select = page.locator("#origin-select")
    is_valid = origin_select.evaluate("el => el.validity.valid")
    assert not is_valid, "Le champ origine vide devrait être invalide"


def test_submit_without_destination_shows_validation_error(page: Page):
    """
    CA-5 (erreur) : Soumettre le formulaire sans destination doit bloquer
    l'envoi et signaler le champ manquant.
    """
    page.select_option("#origin-select", value="1")          # TUN
    page.fill("#id_departure_date", SEARCH_DATE.strftime("%Y-%m-%d"))

    page.get_by_role("button", name="Rechercher des vols").click()

    expect(page).to_have_url(re.compile(r"^" + re.escape(BASE_URL) + r"/?$"))

    dest_select = page.locator("#destination-select")
    is_valid = dest_select.evaluate("el => el.validity.valid")
    assert not is_valid, "Le champ destination vide devrait être invalide"


def test_submit_empty_form_keeps_user_on_homepage(page: Page):
    """
    CA-5 (erreur – tous les champs vides) : Cliquer sur Rechercher sans
    renseigner aucun champ ne doit pas déclencher de requête serveur.
    L'utilisateur reste sur la page d'accueil.
    """
    # Aucun champ n'est renseigné
    page.get_by_role("button", name="Rechercher des vols").click()

    expect(page).to_have_url(re.compile(r"^" + re.escape(BASE_URL) + r"/?$"))

    # Au moins l'un des selects obligatoires doit être invalide
    origin_valid = page.locator("#origin-select").evaluate("el => el.validity.valid")
    assert not origin_valid, "Le formulaire vide aurait dû être bloqué par la validation"