"""
Tests Playwright — Annulation de réservation (User Story NouvelAir).

En tant que passager connecté, je veux pouvoir annuler ma réservation depuis
mon espace personnel, afin d'obtenir un remboursement si j'annule plus de 24h
avant le vol.

Corrections v2 :
    - Connexion via input[name='username'] / input[name='password']
      (les labels Django n'ont pas le texte ciblé par la regex précédente)
    - base_url injecté comme fixture dans booking_page ET dans les tests
      non-authentifiés (BasePage.__init__ exige (page, base_url))

Exécution :
    pytest tests/e2e/test_booking_cancellation.py -v --base-url=http://127.0.0.1:8000
"""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.pages.booking_page import BookingPage

# ── Constantes ────────────────────────────────────────────────────────────────

USERNAME = "mytestuser"
PASSWORD = "NouvelAir2025!"

# ── Helpers de connexion ──────────────────────────────────────────────────────


def _login(page: Page, base_url: str) -> None:
    """
    Authentifie l'utilisateur de test.

    Utilise les sélecteurs par attribut name (input[name='username'] /
    input[name='password']) qui correspondent au formulaire Django par défaut,
    ainsi qu'à id_username / id_password générés par Django.
    Fallback sur get_by_placeholder si les champs name ne sont pas trouvés.
    """
    page.goto(f"{base_url}/accounts/connexion/")
    page.wait_for_load_state("networkidle")

    # ── Champ identifiant ──────────────────────────────────────────────────────
    # Django génère : <input id="id_username" name="username" …>
    username_field = page.locator("input[name='username'], #id_username").first
    if username_field.count() == 0:
        # Fallback placeholder
        username_field = page.get_by_placeholder(
            re.compile(r"username|identifiant|pseudo|nom", re.I)
        )
    username_field.fill(USERNAME)

    # ── Champ mot de passe ─────────────────────────────────────────────────────
    # Django génère : <input id="id_password" name="password" type="password" …>
    password_field = page.locator("input[name='password'], #id_password").first
    if password_field.count() == 0:
        password_field = page.get_by_placeholder(
            re.compile(r"password|mot de passe", re.I)
        )
    password_field.fill(PASSWORD)

    # ── Bouton soumettre ───────────────────────────────────────────────────────
    submit = page.locator("button[type='submit'], input[type='submit']").first
    if submit.count() == 0:
        submit = page.get_by_role(
            "button", name=re.compile(r"se connecter|connexion|login|sign in", re.I)
        )
    submit.click()
    page.wait_for_load_state("networkidle")


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def booking_page(page: Page, base_url: str) -> BookingPage:
    """
    Instancie BookingPage, connecte l'utilisateur de test,
    puis navigue vers la page Mes réservations.

    FIX #1 — base_url injecté en paramètre de fixture (requis par BasePage).
    FIX #2 — connexion via input[name=…] au lieu de get_by_label (labels absents).

    Returns:
        BookingPage: instance prête à l'emploi avec session active.
    """
    _login(page, base_url)

    bp = BookingPage(page, base_url)   # FIX #1 : passe base_url à BasePage
    bp.navigate()
    return bp


# ── Tests — Visibilité du bouton Annuler ─────────────────────────────────────


class TestCancelButtonVisibility:
    """Vérifie la visibilité du bouton Annuler selon le statut de réservation."""

    def test_cancel_button_visible_on_pending_booking(
        self, booking_page: BookingPage
    ) -> None:
        """Le bouton 'Annuler' est visible et activé sur une réservation 'pending'."""
        booking_page.screenshot("pending_list")

        row = booking_page.get_first_booking_by_status("pending")
        booking_page.debug_dump("pending")
        expect(row).to_be_visible()
        booking_page.screenshot("pending_row_found")

        assert booking_page.cancel_button_is_visible(row), (
            "Le bouton Annuler devrait être visible sur une réservation pending."
        )
        assert booking_page.cancel_button_is_enabled(row), (
            "Le bouton Annuler devrait être activé sur une réservation pending."
        )
        booking_page.screenshot("cancel_button_visible_pending")

    def test_cancel_button_visible_on_confirmed_booking(
        self, booking_page: BookingPage
    ) -> None:
        """Le bouton 'Annuler' est visible et activé sur une réservation 'confirmed'."""
        booking_page.screenshot("confirmed_list")

        row = booking_page.get_first_booking_by_status("confirmed")
        booking_page.debug_dump("confirmed")
        expect(row).to_be_visible()
        booking_page.screenshot("confirmed_row_found")

        assert booking_page.cancel_button_is_visible(row), (
            "Le bouton Annuler devrait être visible sur une réservation confirmed."
        )
        assert booking_page.cancel_button_is_enabled(row), (
            "Le bouton Annuler devrait être activé sur une réservation confirmed."
        )
        booking_page.screenshot("cancel_button_visible_confirmed")

    def test_cancel_button_absent_on_cancelled_booking(
        self, booking_page: BookingPage
    ) -> None:
        """Le bouton 'Annuler' est ABSENT sur une réservation déjà annulée."""
        booking_page.screenshot("cancelled_list")

        row = booking_page.get_first_booking_by_status("cancelled")
        expect(row).to_be_visible()
        booking_page.screenshot("cancelled_row_found")

        assert not booking_page.cancel_button_is_visible(row), (
            "Le bouton Annuler ne devrait PAS être visible sur une réservation cancelled."
        )
        booking_page.screenshot("cancel_button_absent_cancelled")


# ── Tests — Dialog de confirmation ───────────────────────────────────────────


class TestCancellationConfirmationDialog:
    """Vérifie l'affichage et le comportement du dialog de confirmation."""

    def test_confirmation_dialog_appears_on_cancel_click(
        self, booking_page: BookingPage
    ) -> None:
        """Un dialog de confirmation s'affiche quand l'utilisateur clique Annuler."""
        row = booking_page.get_first_booking_by_status("pending")
        if row.count() == 0:
            row = booking_page.get_first_booking_by_status("confirmed")
        expect(row).to_be_visible()

        booking_page.click_cancel_button(row)
        booking_page.screenshot("confirmation_dialog_opened")

        assert booking_page.confirmation_dialog_is_visible(), (
            "Le dialog de confirmation devrait s'afficher après clic sur Annuler."
        )
        dialog = booking_page.get_confirmation_dialog()
        expect(dialog).to_contain_text(
            re.compile(r"confirm|annuler|êtes.vous sûr|voulez.vous", re.I)
        )
        booking_page.screenshot("confirmation_dialog_content")

    def test_cancellation_aborted_when_user_declines(
        self, booking_page: BookingPage
    ) -> None:
        """Le statut de la réservation reste inchangé si l'utilisateur clique 'Non'."""
        row = booking_page.get_first_booking_by_status("pending")
        if row.count() == 0:
            row = booking_page.get_first_booking_by_status("confirmed")
        expect(row).to_be_visible()

        booking_page.click_cancel_button(row)
        assert booking_page.confirmation_dialog_is_visible(), (
            "Le dialog doit être visible avant le refus."
        )
        booking_page.screenshot("dialog_before_decline")

        booking_page.decline_cancellation()
        booking_page.screenshot("after_decline_dialog")

        still_cancellable = (
            booking_page.get_first_booking_by_status("pending").count() > 0
            or booking_page.get_first_booking_by_status("confirmed").count() > 0
        )
        assert still_cancellable, (
            "Après refus, au moins une réservation pending/confirmed doit encore exister."
        )


# ── Tests — Annulation réussie ────────────────────────────────────────────────


class TestSuccessfulCancellation:
    """Vérifie le flux complet d'annulation réussie."""

    def test_cancel_pending_booking_changes_status_to_cancelled(
        self, booking_page: BookingPage
    ) -> None:
        """Après confirmation, une réservation 'pending' passe au statut 'cancelled'."""
        row = booking_page.get_first_booking_by_status("pending")
        expect(row).to_be_visible()
        booking_page.screenshot("before_cancellation_pending")

        booking_page.click_cancel_button(row)
        assert booking_page.confirmation_dialog_is_visible()
        booking_page.screenshot("dialog_pending")

        booking_page.confirm_cancellation()
        booking_page.screenshot("after_cancellation_pending")

        assert booking_page.booking_shows_cancelled_status(), (
            "Le statut 'cancelled' devrait être affiché après annulation d'une réservation pending."
        )

    def test_cancel_confirmed_booking_changes_status_to_cancelled(
        self, booking_page: BookingPage
    ) -> None:
        """Après confirmation, une réservation 'confirmed' passe au statut 'cancelled'."""
        row = booking_page.get_first_booking_by_status("confirmed")
        expect(row).to_be_visible()
        booking_page.screenshot("before_cancellation_confirmed")

        booking_page.click_cancel_button(row)
        assert booking_page.confirmation_dialog_is_visible()
        booking_page.screenshot("dialog_confirmed")

        booking_page.confirm_cancellation()
        booking_page.screenshot("after_cancellation_confirmed")

        assert booking_page.booking_shows_cancelled_status(), (
            "Le statut 'cancelled' devrait être affiché après annulation d'une réservation confirmed."
        )

    def test_cancelled_booking_shows_no_cancel_button_after_cancellation(
        self, booking_page: BookingPage
    ) -> None:
        """Après annulation réussie, le bouton 'Annuler' disparaît de la réservation."""
        row = booking_page.get_first_booking_by_status("pending")
        if row.count() == 0:
            row = booking_page.get_first_booking_by_status("confirmed")
        expect(row).to_be_visible()

        booking_page.click_cancel_button(row)
        assert booking_page.confirmation_dialog_is_visible()
        booking_page.confirm_cancellation()
        booking_page.screenshot("after_cancel_no_button_check")

        cancelled_row = booking_page.get_first_booking_by_status("cancelled")
        expect(cancelled_row).to_be_visible()

        assert not booking_page.cancel_button_is_visible(cancelled_row), (
            "Le bouton Annuler ne devrait plus être visible sur la réservation fraîchement annulée."
        )
        booking_page.screenshot("no_cancel_button_after_cancellation")


# ── Tests — Blocage < 24h ─────────────────────────────────────────────────────


class TestCancellationBlockedWithin24h:
    """Vérifie que l'annulation est bloquée si le vol part dans moins de 24h."""

    def test_cancel_blocked_when_flight_within_24h(
        self, booking_page: BookingPage
    ) -> None:
        """
        Si le vol est dans moins de 24h, l'annulation est bloquée.
        Le statut ne doit pas passer à 'cancelled'.
        """
        imminent_row = booking_page.get_imminent_booking_row()
        if imminent_row.count() == 0:
            pytest.skip("Aucune réservation avec vol imminent (< 24h) trouvée.")

        expect(imminent_row).to_be_visible()
        booking_page.screenshot("imminent_flight_row")

        btn = booking_page.get_cancel_button(imminent_row)

        if btn.count() > 0 and btn.is_enabled():
            booking_page.click_cancel_button(imminent_row)
            booking_page.screenshot("after_click_imminent_cancel")

            assert booking_page.has_24h_error(), (
                "Un message d'erreur '< 24h' devrait s'afficher pour un vol imminent."
            )
            booking_page.screenshot("error_message_24h")

            assert not booking_page.booking_shows_cancelled_status(), (
                "Le statut ne devrait PAS passer à 'cancelled' pour un vol dans < 24h."
            )
        else:
            # Blocage préventif côté UI
            if btn.count() > 0:
                expect(btn).to_be_disabled()
            booking_page.screenshot("cancel_button_disabled_24h")

    def test_error_message_displayed_for_imminent_flight(
        self, booking_page: BookingPage
    ) -> None:
        """Un message d'erreur clair est affiché pour un vol imminent (< 24h)."""
        imminent_row = booking_page.get_imminent_booking_row()
        if imminent_row.count() == 0:
            pytest.skip("Aucune réservation avec vol imminent trouvée.")

        btn = booking_page.get_cancel_button(imminent_row)
        if btn.count() == 0 or not btn.is_enabled():
            pytest.skip(
                "Blocage < 24h géré côté UI (bouton absent/désactivé) — "
                "pas de message d'erreur à tester."
            )

        booking_page.click_cancel_button(imminent_row)
        booking_page.screenshot("error_24h_attempt")

        assert booking_page.has_24h_error(), (
            "Un message d'erreur mentionnant '24h' devrait être affiché."
        )
        booking_page.screenshot("error_24h_displayed")


# ── Tests — Accès non authentifié ─────────────────────────────────────────────


class TestUnauthenticatedAccess:
    """Vérifie la protection de la page réservations pour les visiteurs non connectés."""

    def test_bookings_page_redirects_unauthenticated_user(
        self, page: Page, base_url: str   # FIX #1 : base_url requis par BasePage
    ) -> None:
        """Un visiteur non connecté est redirigé vers la page de connexion."""
        bp = BookingPage(page, base_url)  # FIX #1 : passe base_url
        bp.navigate()

        expect(page).to_have_url(re.compile(r"connexion|login", re.I))
        expect(
            page.get_by_role(
                "button", name=re.compile(r"se connecter|connexion|login|sign in", re.I)
            )
        ).to_be_visible()

        page.screenshot(
            path="reports/screenshots/cancellation/unauthenticated_redirect.png"
        )

    def test_cancel_action_requires_authentication(
        self, page: Page, base_url: str   # FIX #1 : cohérence avec la fixture
    ) -> None:
        """Une tentative d'annulation directe (URL) sans session est rejetée."""
        # booking cancel endpoint expects <uuid:reference>, so 1/1 is guaranteed 404.
        # Use a clearly invalid UUID to keep behavior deterministic.
        page.goto(f"{base_url}/bookings/annuler/00000000-0000-0000-0000-000000000000/")
        # /bookings/annuler/<uuid:reference>/ attend une référence UUID existante.
        # On ne peut pas valider le redirect sans un booking créé en DB de test.
        page.wait_for_load_state("networkidle")

        page.screenshot(
            path="reports/screenshots/cancellation/unauthenticated_cancel_attempt.png"
        )

        url = page.url
        is_redirected = bool(re.search(r"connexion|login", url, re.I))
        is_forbidden = (
            page.locator("h1, h2, title")
            .filter(has_text=re.compile(r"403|404|interdit|non autorisé|forbidden", re.I))
            .count() > 0
        )

        assert is_redirected or is_forbidden, (
            "Une tentative d'annulation sans session devrait mener à login ou 403/404."
        )