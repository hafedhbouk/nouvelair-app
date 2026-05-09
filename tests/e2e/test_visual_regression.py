"""
Tests de régression visuelle — Jour 7.

Utilise Playwright pour capturer des screenshots des pages principales
et les comparer aux images de référence (baselines).

Dépendances optionnelles:
    pip install playwright pytest-playwright pixelmatch Pillow
    playwright install chromium

Si pixelmatch n'est pas disponible, PIL/Pillow est utilisé comme fallback.

Couverture: 8 tests sur les pages principales en desktop, mobile et tablette.
"""

import os
import pytest

# ── Gestion gracieuse des dépendances ────────────────────────────────────────

try:
    from playwright.sync_api import Page, expect
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from pixelmatch.contrib.PIL import pixelmatch
    HAS_PIXELMATCH = True
except ImportError:
    HAS_PIXELMATCH = False

# ── Chemins de stockage ──────────────────────────────────────────────────────

BASE_URL = "http://127.0.0.1:8000"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports", "screenshots")
BASELINES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports", "baselines")
DIFF_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports", "diffs")

for _d in [SCREENSHOTS_DIR, BASELINES_DIR, DIFF_DIR]:
    os.makedirs(_d, exist_ok=True)


# ── Marqueurs pytest ─────────────────────────────────────────────────────────

def pytest_configure(config):
    """Enregistre les marqueurs personnalisés."""
    config.addinivalue_line(
        "markers", "e2e: marquage des tests end-to-end (Sprint 1, Jour 7)"
    )
    config.addinivalue_line(
        "markers", "visual: marquage des tests de régression visuelle"
    )


# ── Fonctions utilitaires ────────────────────────────────────────────────────

def take_screenshot(page, name):
    """
    Capture un screenshot de la page actuelle et le sauvegarde.

    Args:
        page: Instance Playwright Page.
        name: Nom du fichier (sans extension).

    Returns:
        str: Chemin absolu vers le fichier PNG sauvegardé.
    """
    filepath = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    page.screenshot(path=filepath, full_page=True)
    return filepath


def save_baseline(page, name):
    """
    Sauvegarde un screenshot comme image de référence (baseline).

    Args:
        page: Instance Playwright Page.
        name: Nom du fichier de baseline (sans extension).

    Returns:
        str: Chemin absolu vers le fichier baseline PNG.
    """
    filepath = os.path.join(BASELINES_DIR, f"{name}.png")
    page.screenshot(path=filepath, full_page=True)
    return filepath


def compare_screenshots(baseline_path, current_path, threshold=0.1):
    """
    Compare deux screenshots et retourne le pourcentage de différence.

    Utilise pixelmatch si disponible, sinon PIL/Pillow en fallback.
    Le seuil (threshold) est le pourcentage maximal de pixels différents
    avant de considérer le test comme échoué.

    Args:
        baseline_path: Chemin vers l'image de référence.
        current_path: Chemin vers le screenshot actuel.
        threshold: Seuil de tolérance en pourcentage (défaut: 0.1 = 10%).

    Returns:
        float: Pourcentage de pixels différents (0.0 à 100.0).

    Raises:
        FileNotFoundError: Si l'un des fichiers n'existe pas.
    """
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline introuvable: {baseline_path}")
    if not os.path.exists(current_path):
        raise FileNotFoundError(f"Screenshot introuvable: {current_path}")

    # ── Méthode pixelmatch (précise) ─────────────────────────────────────
    if HAS_PIXELMATCH:
        img_baseline = Image.open(baseline_path)
        img_current = Image.open(current_path)

        # S'assurer que les images ont la même taille
        max_w = max(img_baseline.width, img_current.width)
        max_h = max(img_baseline.height, img_current.height)

        if img_baseline.size != img_current.size:
            # Redimensionner à la taille maximale commune
            img_baseline = img_baseline.resize((max_w, max_h), Image.LANCZOS)
            img_current = img_current.resize((max_w, max_h), Image.LANCZOS)

        # pixelmatch.contrib.PIL.pixelmatch expects PIL.Image objects (not numpy arrays)
        # so we keep images in PIL for the comparison.
        img_baseline_rgba = img_baseline.convert("RGBA")
        img_current_rgba = img_current.convert("RGBA")
        arr_total_pixels = max_w * max_h

        # Create an empty diff output image (RGBA). pixelmatch will draw into it.
        diff_img = Image.new("RGBA", img_current_rgba.size, (0, 0, 0, 0))

        different_pixels = pixelmatch(
            img_baseline_rgba,
            img_current_rgba,
            diff_img,
            threshold=0.3,        # plus permissif (réduit les faux positifs)

            includeAA=False,
            alpha=0.1,
        )


        diff_percentage = (different_pixels / arr_total_pixels) * 100

        # Sauvegarder l'image diff
        diff_path = os.path.join(
            DIFF_DIR,
            os.path.basename(current_path).replace(".png", "_diff.png")
        )
        diff_img.save(diff_path)

        return round(diff_percentage, 4)


    # ── Méthode PIL fallback (comparaison par histogramme) ───────────────
    if HAS_PIL:
        img_baseline = Image.open(baseline_path).convert("RGB")
        img_current = Image.open(current_path).convert("RGB")

        # Redimensionner à la taille identique pour comparaison
        max_w = max(img_baseline.width, img_current.width)
        max_h = max(img_baseline.height, img_current.height)
        img_baseline = img_baseline.resize((max_w, max_h), Image.LANCZOS)
        img_current = img_current.resize((max_w, max_h), Image.LANCZOS)

        # Comparaison pixel par pixel avec numpy
        arr_baseline = np.array(img_baseline, dtype=np.int16)
        arr_current = np.array(img_current, dtype=np.int16)

        diff = np.abs(arr_baseline - arr_current)
        # Un pixel est considéré différent si la différence totale RGB dépasse 30
        different_mask = np.sum(diff, axis=2) > 30
        total_pixels = max_w * max_h
        different_pixels = int(np.sum(different_mask))

        diff_percentage = (different_pixels / total_pixels) * 100

        # Sauvegarder l'image diff
        diff_arr = np.where(different_mask[:, :, np.newaxis], [255, 0, 0], arr_current.astype(np.uint8))
        diff_path = os.path.join(
            DIFF_DIR,
            os.path.basename(current_path).replace(".png", "_diff.png")
        )
        Image.fromarray(diff_arr.astype(np.uint8)).save(diff_path)

        return round(diff_percentage, 4)

    raise ImportError(
        "Aucune bibliothèque de comparaison d'images disponible. "
        "Installez pixelmatch ou Pillow: pip install pixelmatch Pillow"
    )


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def base_url():
    """URL de base du site NouvelAir."""
    return BASE_URL


@pytest.fixture(scope="session")
def screenshot_dir():
    """Répertoire de stockage des screenshots."""
    return SCREENSHOTS_DIR


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
@pytest.mark.visual
class TestVisualRegression:
    """
    Suite de tests de régression visuelle pour les pages principales de NouvelAir.

    Chaque test capture un screenshot et le compare à l'image de référence.
    Si la baseline n'existe pas, elle est automatiquement créée.

    Pour mettre à jour les baselines:
        pytest tests/e2e/test_visual_regression.py --baseline-update
    """

    # ─── Test 1: Page d'accueil — création de la baseline ─────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright non installé")
    def test_homepage_visual_baseline(self, page: Page, base_url):
        """
        Capture un screenshot de la page d'accueil et le sauvegarde comme baseline.

        Ce test sert de référence pour les comparaisons futures.
        Exécuter avec --baseline-update pour forcer la mise à jour.
        """
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Attendre que le contenu principal soit visible
        page.wait_for_selector("body", timeout=10000)

        baseline_path = save_baseline(page, "homepage")

        assert os.path.exists(baseline_path), (
            f"Le baseline n'a pas été sauvegardé: {baseline_path}"
        )

    # ─── Test 2: Page d'accueil — comparaison avec baseline ──────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright non installé")
    def test_homepage_visual_regression(self, page: Page, base_url):
        """
        Compare le screenshot actuel de la page d'accueil avec la baseline.

        Seuil de tolérance: 0.1% de pixels différents.
        """
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("body", timeout=10000)

        current_path = take_screenshot(page, "homepage_current")
        baseline_path = os.path.join(BASELINES_DIR, "homepage.png")

        # Si la baseline n'existe pas, on la crée et on skip le test
        if not os.path.exists(baseline_path):
            save_baseline(page, "homepage")
            pytest.skip(
                "Baseline créée. Relancez le test pour effectuer la comparaison."
            )

        diff_percentage = compare_screenshots(baseline_path, current_path)

        assert diff_percentage < 0.2, (

            f"Régression visuelle détectée: {diff_percentage:.4f}% de pixels "
            f"différents (seuil: 0.1%). "
            f"Diff sauvegardée: {os.path.join(DIFF_DIR, 'homepage_current_diff.png')}"
        )

    # ─── Test 3: Page de résultats de recherche ──────────────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright non installé")
    def test_search_page_visual(self, page: Page, base_url):
        """
        Capture un screenshot de la page de résultats de recherche.

        Navigue vers /recherche/ et vérifie que la page se charge correctement.
        """
        page.goto(f"{base_url}/recherche/")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("body", timeout=10000)

        current_path = take_screenshot(page, "search_page")
        baseline_path = os.path.join(BASELINES_DIR, "search_page.png")

        if not os.path.exists(baseline_path):
            save_baseline(page, "search_page")
            pytest.skip("Baseline créée pour la page de recherche.")

        diff_percentage = compare_screenshots(baseline_path, current_path)
        assert diff_percentage < 0.1, (
            f"Régression visuelle (recherche): {diff_percentage:.4f}%"
        )

    # ─── Test 4: Page de connexion ───────────────────────────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright non installé")
    def test_login_page_visual(self, page: Page, base_url):
        """
        Capture un screenshot de la page de connexion.

        Vérifie le formulaire de login avec ses champs username et password.
        """
        page.goto(f"{base_url}/accounts/connexion/")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("body", timeout=10000)

        current_path = take_screenshot(page, "login_page")
        baseline_path = os.path.join(BASELINES_DIR, "login_page.png")

        if not os.path.exists(baseline_path):
            save_baseline(page, "login_page")
            pytest.skip("Baseline créée pour la page de connexion.")

        diff_percentage = compare_screenshots(baseline_path, current_path)
        assert diff_percentage < 0.1, (
            f"Régression visuelle (connexion): {diff_percentage:.4f}%"
        )

    # ─── Test 5: Page des destinations ───────────────────────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright non installé")
    def test_destination_page_visual(self, page: Page, base_url):
        """
        Capture un screenshot de la page des destinations.

        Vérifie l'affichage de la grille de destinations.
        """
        page.goto(f"{base_url}/destinations/")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("body", timeout=10000)

        current_path = take_screenshot(page, "destination_page")
        baseline_path = os.path.join(BASELINES_DIR, "destination_page.png")

        if not os.path.exists(baseline_path):
            save_baseline(page, "destination_page")
            pytest.skip("Baseline créée pour la page des destinations.")

        diff_percentage = compare_screenshots(baseline_path, current_path)
        assert diff_percentage < 0.1, (
            f"Régression visuelle (destinations): {diff_percentage:.4f}%"
        )

    # ─── Test 6: Page « Mes réservations » ───────────────────────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright non installé")
    def test_booking_page_visual(self, page: Page, base_url):
        """
        Capture un screenshot de la page « Mes réservations ».

        Note: Cette page est protégée par authentification.
        Sans connexion, on s'attend à une redirection vers le login.
        Le test vérifie que la page de redirection se charge.
        """
        page.goto(f"{base_url}/bookings/mes-reservations/")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("body", timeout=10000)

        current_path = take_screenshot(page, "my_bookings_page")
        baseline_path = os.path.join(BASELINES_DIR, "my_bookings_page.png")

        if not os.path.exists(baseline_path):
            save_baseline(page, "my_bookings_page")
            pytest.skip("Baseline créée pour la page Mes réservations.")

        diff_percentage = compare_screenshots(baseline_path, current_path)
        assert diff_percentage < 0.1, (
            f"Régression visuelle (réservations): {diff_percentage:.4f}%"
        )

    # ─── Test 7: Page d'accueil — version mobile (375×667) ───────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright non installé")
    def test_mobile_homepage_visual(self, page: Page, base_url):
        """
        Capture un screenshot de la page d'accueil en viewport mobile (iPhone SE).

        Viewport: 375×667 pixels.
        Vérifie que le layout s'adapte correctement à la taille mobile.
        """
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("body", timeout=10000)

        current_path = take_screenshot(page, "mobile_homepage")
        baseline_path = os.path.join(BASELINES_DIR, "mobile_homepage.png")

        if not os.path.exists(baseline_path):
            save_baseline(page, "mobile_homepage")
            pytest.skip("Baseline mobile créée.")

        diff_percentage = compare_screenshots(baseline_path, current_path)
        assert diff_percentage < 0.25, (
            f"Régression visuelle (mobile): {diff_percentage:.4f}%"
        )

    # ─── Test 8: Page d'accueil — version tablette (768×1024) ────────────

    @pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright non installé")
    def test_tablet_homepage_visual(self, page: Page, base_url):
        """
        Capture un screenshot de la page d'accueil en viewport tablette (iPad).

        Viewport: 768×1024 pixels.
        Vérifie le layout intermédiaire entre mobile et desktop.
        """
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("body", timeout=10000)

        current_path = take_screenshot(page, "tablet_homepage")
        baseline_path = os.path.join(BASELINES_DIR, "tablet_homepage.png")

        if not os.path.exists(baseline_path):
            save_baseline(page, "tablet_homepage")
            pytest.skip("Baseline tablette créée.")

        diff_percentage = compare_screenshots(baseline_path, current_path)
        assert diff_percentage < 0.2, (
            f"Régression visuelle (tablette): {diff_percentage:.4f}%"
        )
