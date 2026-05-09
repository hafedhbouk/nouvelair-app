"""
Tests d'accessibilité — Jour 7.

Utilise axe-playwright-python pour scanner les pages principales du site
NouvelAir et détecter les violations des normes WCAG 2.1 AA.

Dépendances optionnelles:
    pip install axe-playwright-python playwright pytest-playwright
    playwright install chromium

Couverture: 7 tests couvrant toutes les pages principales.
"""

import os
import json
from datetime import datetime

import pytest

# ── Gestion gracieuse des dépendances ────────────────────────────────────────

try:
    from playwright.sync_api import Page, expect
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    from axe_playwright_python.sync_playwright import Axe
    HAS_AXE = True
except ImportError:
    HAS_AXE = False

# ── Configuration ────────────────────────────────────────────────────────────

BASE_URL = "http://127.0.0.1:8000"
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports", "accessibility")


def pytest_configure(config):
    """Enregistre les marqueurs personnalisés."""
    config.addinivalue_line(
        "markers", "e2e: marquage des tests end-to-end (Sprint 1, Jour 7)"
    )
    config.addinivalue_line(
        "markers", "a11y: marquage des tests d'accessibilité"
    )


# ── Fonctions utilitaires ────────────────────────────────────────────────────

def run_accessibility_scan(page, tags=None):
    """
    Exécute un scan d'accessibilité axe sur la page actuelle.

    Args:
        page: Instance Playwright Page.
        tags: Liste de tags axe à inclure. Par défaut: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'].

    Returns:
        dict: Résultat du scan axe, contenant 'violations', 'passes', 'incomplete', 'inapplicable'.
    """
    if not HAS_AXE:
        raise ImportError(
            "axe-playwright-python n'est pas installé. "
            "Installez-le: pip install axe-playwright-python"
        )

    axe = Axe()
    if tags is None:
        tags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]

    # FIX: axe.run() returns an AxeResults object; the actual data lives in
    # results.response (a plain dict).  Accessing .violations directly raises
    # AttributeError in current versions of axe-playwright-python.
    axe_results = axe.run(page, options={"runOnly": {"type": "tag", "values": tags}})
    response = axe_results.response  # dict with violations, passes, etc.

    return {
        "violations": response.get("violations", []),
        "passes": response.get("passes", []),
        "incomplete": response.get("incomplete", []),
        "inapplicable": response.get("inapplicable", []),
    }


def assert_no_critical_violations(violations):
    """
    Vérifie qu'il n'y a pas de violations critiques dans les résultats axe.

    Les violations sont classifiées par impact:
        - critical: empêche totalement l'utilisation
        - serious: empêche significativement l'utilisation
        - moderate: gêne l'utilisation
        - minor: légèrement gênant

    Args:
        violations: Liste des violations retournées par axe.

    Raises:
        AssertionError: Si des violations critiques ou serious sont trouvées.
    """
    critical = [v for v in violations if v.get("impact") == "critical"]
    serious = [v for v in violations if v.get("impact") == "serious"]

    if critical:
        details = "\n".join(
            f"  - [{v['id']}] {v['description']} "
            f"({len(v.get('nodes', []))} éléments affectés)"
            for v in critical
        )
        pytest.fail(
            f"Violations CRITIQUES d'accessibilité détectées ({len(critical)}):\n{details}"
        )

    if serious:
        details = "\n".join(
            f"  - [{v['id']}] {v['description']} "
            f"({len(v.get('nodes', []))} éléments affectés)"
            for v in serious
        )
        pytest.fail(
            f"Violations SERIEUSES d'accessibilité détectées ({len(serious)}):\n{details}"
        )


def generate_accessibility_report(violations, page_name, page_url):
    """
    Génère un rapport HTML détaillé des violations d'accessibilité.

    Args:
        violations: Liste des violations axe.
        page_name: Nom lisible de la page (ex: "Page d'accueil").
        page_url: URL de la page scannée.

    Returns:
        str: Chemin vers le fichier HTML du rapport.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_name = page_name.lower().replace(" ", "_")

    # Regrouper par impact
    by_impact = {}
    for v in violations:
        impact = v.get("impact", "unknown")
        by_impact.setdefault(impact, []).append(v)

    impact_labels = {
        "critical": "🔴 Critique",
        "serious": "🟠 Sérieux",
        "moderate": "🟡 Modéré",
        "minor": "🔵 Mineur",
    }

    violation_cards = ""
    for impact, viols in sorted(
        by_impact.items(),
        key=lambda x: (
            ["critical", "serious", "moderate", "minor"].index(x[0])
            if x[0] in ["critical", "serious", "moderate", "minor"]
            else 99
        ),
    ):
        label = impact_labels.get(impact, f"⚪ {impact}")
        for v in viols:
            nodes_html = ""
            for node in v.get("nodes", []):
                target = ", ".join(node.get("target", []))
                failure = node.get("failureSummary", "Pas de description")
                nodes_html += f"""
                <tr>
                    <td style="padding:4px 8px;border:1px solid #ddd;font-family:monospace;font-size:12px;">{target}</td>
                    <td style="padding:4px 8px;border:1px solid #ddd;font-size:12px;">{failure}</td>
                </tr>"""
            border_color = {
                "critical": "#e74c3c",
                "serious": "#e67e22",
                "moderate": "#f1c40f",
                "minor": "#3498db",
            }.get(impact, "#95a5a6")
            violation_cards += f"""
            <div style="margin-bottom:16px;padding:12px;border-left:4px solid {border_color};background:#fafafa;">
                <h4 style="margin:0 0 4px;">[{v.get("id", "N/A")}] {v.get("description", "Sans description")}</h4>
                <p style="margin:0;color:#666;">Impact: <strong>{label}</strong> — 
                   <a href="{v.get("helpUrl", "#")}" target="_blank">En savoir plus</a></p>
                <table style="width:100%;margin-top:8px;border-collapse:collapse;">
                    <thead><tr>
                        <th style="text-align:left;padding:4px 8px;border:1px solid #ddd;background:#f0f0f0;">Sélecteur</th>
                        <th style="text-align:left;padding:4px 8px;border:1px solid #ddd;background:#f0f0f0;">Description</th>
                    </tr></thead>
                    <tbody>{nodes_html}</tbody>
                </table>
            </div>"""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Accessibilité — {page_name} — NouvelAir</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 960px; margin: 0 auto; padding: 20px; color: #333; }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 8px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 20px 0; }}
        .summary-card {{ padding: 16px; border-radius: 8px; text-align: center; }}
        .summary-card h3 {{ margin: 0; font-size: 2em; }}
        .summary-card p {{ margin: 4px 0 0; color: #666; }}
        .card-critical {{ background: #fde8e8; color: #e74c3c; }}
        .card-serious {{ background: #fef3e8; color: #e67e22; }}
        .card-moderate {{ background: #fef9e7; color: #f39c12; }}
        .card-minor {{ background: #ebf5fb; color: #3498db; }}
        .card-total {{ background: #f4f6f7; color: #2c3e50; }}
    </style>
</head>
<body>
    <h1>♿ Rapport d'Accessibilité — {page_name}</h1>
    <p><strong>Date:</strong> {timestamp}<br>
       <strong>URL:</strong> <a href="{page_url}">{page_url}</a><br>
       <strong>Standard:</strong> WCAG 2.1 AA</p>

    <div class="summary">
        <div class="summary-card card-total">
            <h3>{len(violations)}</h3><p>Total violations</p>
        </div>
        <div class="summary-card card-critical">
            <h3>{len(by_impact.get("critical", []))}</h3><p>Critiques</p>
        </div>
        <div class="summary-card card-serious">
            <h3>{len(by_impact.get("serious", []))}</h3><p>Sérieuses</p>
        </div>
        <div class="summary-card card-moderate">
            <h3>{len(by_impact.get("moderate", []))}</h3><p>Modérées</p>
        </div>
        <div class="summary-card card-minor">
            <h3>{len(by_impact.get("minor", []))}</h3><p>Mineures</p>
        </div>
    </div>

    <h2>Détails des violations</h2>
    {violation_cards if violations else '<p style="color:#27ae60;font-weight:bold;">✅ Aucune violation détectée !</p>'}
    <hr>
    <p style="color:#999;font-size:12px;">Généré automatiquement par NouvelAir E2E Tests — {timestamp}</p>
</body>
</html>"""

    report_path = os.path.join(REPORTS_DIR, f"a11y_{safe_name}.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Sauvegarder aussi en JSON
    json_path = os.path.join(REPORTS_DIR, f"a11y_{safe_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(violations, f, ensure_ascii=False, indent=2)

    return report_path


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
@pytest.mark.a11y
class TestAccessibility:
    """
    Suite de tests d'accessibilité pour le site NouvelAir.

    Chaque test scanne une page avec axe-core (WCAG 2.1 AA) et vérifie
    qu'il n'y a pas de violations critiques ou sérieuses.
    """

    # ─── Test 1: Page d'accueil ──────────────────────────────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT or not HAS_AXE, reason="Playwright ou axe-playwright-python non installé")
    def test_homepage_accessibility(self, page: Page, base_url):
        """
        Scan d'accessibilité de la page d'accueil.

        Vérifie la conformité WCAG 2.1 AA:
        - Images avec alt text
        - Structure de titres (h1, h2, etc.)
        - Contraste des couleurs
        - Navigation au clavier
        """
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        results = run_accessibility_scan(page)
        violations = results.get("violations", [])

        report_path = generate_accessibility_report(violations, "Page d'accueil", base_url)

        assert_no_critical_violations(violations)

        # Avertissement si violations modérées/mineures
        moderate = [v for v in violations if v.get("impact") in ("moderate", "minor")]
        if moderate:
            pytest.skip(
                f"Violations modérées/mineures trouvées ({len(moderate)}). "
                f"Rapport: {report_path}"
            )

    # ─── Test 2: Page de connexion ───────────────────────────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT or not HAS_AXE, reason="Playwright ou axe-playwright-python non installé")
    def test_login_page_accessibility(self, page: Page, base_url):
        """
        Scan d'accessibilité de la page de connexion.

        Points de contrôle:
        - Labels associés aux champs de formulaire
        - Messages d'erreur accessibles
        - Focus visible sur les champs
        """
        page.goto(f"{base_url}/accounts/connexion/")
        page.wait_for_load_state("networkidle")

        results = run_accessibility_scan(page)
        violations = results.get("violations", [])

        report_path = generate_accessibility_report(violations, "Connexion", f"{base_url}/accounts/connexion/")

        assert_no_critical_violations(violations)

    # ─── Test 3: Page de résultats de recherche ──────────────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT or not HAS_AXE, reason="Playwright ou axe-playwright-python non installé")
    def test_search_page_accessibility(self, page: Page, base_url):
        """
        Scan d'accessibilité de la page de résultats de recherche.

        Points de contrôle:
        - Tableau de résultats accessible
        - Filtres utilisables au clavier
        - Information de tri (aria-sort)
        """
        page.goto(f"{base_url}/recherche/")
        page.wait_for_load_state("networkidle")

        results = run_accessibility_scan(page)
        violations = results.get("violations", [])

        report_path = generate_accessibility_report(violations, "Recherche", f"{base_url}/recherche/")

        assert_no_critical_violations(violations)

    # ─── Test 4: Page Mes réservations ───────────────────────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT or not HAS_AXE, reason="Playwright ou axe-playwright-python non installé")
    def test_booking_page_accessibility(self, page: Page, base_url):
        """
        Scan d'accessibilité de la page « Mes réservations ».

        Points de contrôle:
        - Tableau de réservations lisible
        - Liens d'action accessibles
        - Statuts avec couleurs + texte (pas couleur seule)
        """
        page.goto(f"{base_url}/bookings/mes-reservations/")
        page.wait_for_load_state("networkidle")

        results = run_accessibility_scan(page)
        violations = results.get("violations", [])

        report_path = generate_accessibility_report(
            violations, "Mes réservations", f"{base_url}/bookings/mes-reservations/"
        )

        assert_no_critical_violations(violations)

    # ─── Test 5: Page des destinations ───────────────────────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT or not HAS_AXE, reason="Playwright ou axe-playwright-python non installé")
    def test_destination_page_accessibility(self, page: Page, base_url):
        """
        Scan d'accessibilité de la page des destinations.

        Points de contrôle:
        - Images de destinations avec alt descriptif
        - Cartes cliquables avec rôle approprié
        - Nom de destination comme heading
        """
        page.goto(f"{base_url}/destinations/")
        page.wait_for_load_state("networkidle")

        results = run_accessibility_scan(page)
        violations = results.get("violations", [])

        report_path = generate_accessibility_report(
            violations, "Destinations", f"{base_url}/destinations/"
        )

        assert_no_critical_violations(violations)

    # ─── Test 6: Page d'inscription ──────────────────────────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT or not HAS_AXE, reason="Playwright ou axe-playwright-python non installé")
    def test_register_page_accessibility(self, page: Page, base_url):
        """
        Scan d'accessibilité de la page d'inscription.

        Points de contrôle:
        - Champs avec labels et descriptions
        - Validation en temps réel accessible
        - Indicateur de force du mot de passe
        """
        page.goto(f"{base_url}/accounts/inscription/")
        page.wait_for_load_state("networkidle")

        results = run_accessibility_scan(page)
        violations = results.get("violations", [])

        report_path = generate_accessibility_report(
            violations, "Inscription", f"{base_url}/accounts/inscription/"
        )

        assert_no_critical_violations(violations)

    # ─── Test 7: Vérification spécifique du contraste des couleurs ───────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT or not HAS_AXE, reason="Playwright ou axe-playwright-python non installé")
    def test_color_contrast(self, page: Page, base_url):
        """
        Vérification spécifique du contraste des couleurs sur les éléments clés.

        Scan uniquement la règle 'color-contrast' d'axe pour s'assurer
        que le texte est lisible par tous les utilisateurs.

        WCAG 2.1 AA exige:
        - Ratio 4.5:1 pour le texte normal
        - Ratio 3:1 pour le texte large (≥18pt ou ≥14pt gras)
        """
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # FIX: use the helper so AxeResults is unwrapped consistently
        results = run_accessibility_scan(
            page,
            tags=None,  # tags ignored — we override via a direct call below
        )

        # Override: scan only the color-contrast rule
        axe = Axe()
        axe_results = axe.run(
            page,
            options={"runOnly": {"type": "rule", "values": ["color-contrast"]}},
        )
        # FIX: access the underlying dict via .response, not .get()
        violations = axe_results.response.get("violations", [])

        report_path = generate_accessibility_report(
            violations, "Contraste couleurs", base_url
        )

        # Pas de violations de contraste acceptées
        assert len(violations) == 0, (
            f"Violations de contraste couleur détectées ({len(violations)}): "
            f"Consultez le rapport: {report_path}"
        )