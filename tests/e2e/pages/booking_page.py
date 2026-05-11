"""
Page Object Model – Page des réservations (Jour 6 + annulation).

Encapsule les interactions avec la page Mes réservations (/bookings/my-bookings/) :
- Liste des réservations de l'utilisateur
- Vérification de la présence de réservations
- Détails d'une réservation
- Flux d'annulation (bouton, dialog de confirmation, message d'erreur)
"""

import os
import re
from datetime import datetime

from playwright.sync_api import Locator, expect
from .base_page import BasePage


# ── Sélecteurs centralisés ────────────────────────────────────────────────────

_ROW_SEL = (
    ".booking-card, .reservation-card, .booking-item, "
    "[class*='booking'], [class*='reservation']"
)
_DIALOG_SEL = (
    "dialog[open], .modal.show, .modal-dialog, "
    "[role='dialog'], [role='alertdialog']"
)
_ERROR_SEL = (
    ".alert-danger, .alert-warning, .error, .errorlist, "
    "[role='alert'], .toast, .toast-error"
)
_STATUS_RE = {
    "pending":   re.compile(r"\bpending\b|\ben attente\b",    re.I),
    "confirmed": re.compile(r"\bconfirmed\b|\bconfirmée?\b",  re.I),
    "cancelled": re.compile(r"\bcancelled\b|\bannulée?\b",    re.I),
}
_CANCEL_BTN_RE  = re.compile(r"annuler|cancel",               re.I)
_CONFIRM_BTN_RE = re.compile(
    r"\boui\b|confirmer|confirm|valider|annuler la réservation", re.I
)
_DECLINE_BTN_RE = re.compile(r"\bnon\b|fermer|close|retour",  re.I)
_ERROR_24H_RE   = re.compile(
    r"24.?h|moins de|cannot cancel|annulation impossible|trop tard", re.I
)


class BookingPage(BasePage):
    def debug_dump(self, prefix: str = "debug") -> None:
        """Dump bookings page content to help align selectors."""
        content = self.page.content()
        # also capture visible text blocks
        text = self.page.inner_text("body") if self.page.locator("body").count() > 0 else ""
        directory = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "test-results", "debug",
            "booking_cancellation",
        )
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, f"{prefix}_page.html"), "w", encoding="utf-8") as f:
            f.write(content)
        with open(os.path.join(directory, f"{prefix}_page.txt"), "w", encoding="utf-8") as f:
            f.write(text)

    """
    Page Object pour la page "Mes réservations" de NouvelAir.

    Fournit des méthodes pour :
    - Accéder à la liste et aux statuts des réservations
    - Déclencher le flux d'annulation (clic + dialog)
    - Vérifier l'état post-annulation et les messages d'erreur

    Attributes:
        url (str): chemin relatif de la page Mes réservations.
    """

    url = "/bookings/mes-reservations/"

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate(self) -> None:
        """Ouvre la page Mes réservations et attend le chargement complet."""
        super().navigate(self.url)
        self.page.wait_for_load_state("networkidle")

    # ── Liste des réservations ────────────────────────────────────────────────

    def get_bookings(self) -> list[Locator]:
        """
        Retourne la liste des cartes de réservation affichées.

        Returns:
            list[Locator]: locators correspondant aux cartes de réservation.
        """
        return self.page.locator(_ROW_SEL).all()

    def has_bookings(self) -> bool:
        """
        Vérifie si au moins une réservation est affichée.

        Returns:
            bool: True si des réservations sont présentes, False sinon.
        """
        return len(self.get_bookings()) > 0

    # ── Accès par statut ──────────────────────────────────────────────────────

    def get_first_booking_by_status(self, status: str) -> Locator:
        """
        Retourne la première carte de réservation correspondant au statut donné.

        Args:
            status: 'pending', 'confirmed' ou 'cancelled'.

        Returns:
            Locator: premier élément correspondant.

        Raises:
            ValueError: si le statut n'est pas reconnu.
        """
        pattern = _STATUS_RE.get(status)
        if pattern is None:
            raise ValueError(
                f"Statut inconnu : '{status}'. "
                f"Valeurs acceptées : {list(_STATUS_RE)}"
            )
        return self.page.locator(_ROW_SEL).filter(has=self.page.locator("[class*='status'], .status, .badge").filter(has_text=pattern)).first

    def get_all_bookings_by_status(self, status: str) -> list[Locator]:
        """
        Retourne toutes les cartes de réservation correspondant au statut donné.

        Args:
            status: 'pending', 'confirmed' ou 'cancelled'.

        Returns:
            list[Locator]: liste de locators.
        """
        pattern = _STATUS_RE.get(status)
        if pattern is None:
            raise ValueError(f"Statut inconnu : '{status}'.")
        return self.page.locator(_ROW_SEL).filter(has_text=pattern).all()

    # ── Bouton Annuler ────────────────────────────────────────────────────────

    def get_cancel_button(self, booking_row: Locator) -> Locator:
        """
        Retourne le bouton 'Annuler' à l'intérieur d'une carte de réservation.

        Args:
            booking_row: locator de la carte de réservation cible.

        Returns:
            Locator: bouton d'annulation (count=0 s'il est absent).
        """
        return booking_row.get_by_role("button", name=_CANCEL_BTN_RE)

    def cancel_button_is_visible(self, booking_row: Locator) -> bool:
        """Indique si le bouton Annuler est présent et visible."""
        btn = self.get_cancel_button(booking_row)
        return btn.count() > 0 and btn.is_visible()

    def cancel_button_is_enabled(self, booking_row: Locator) -> bool:
        """Indique si le bouton Annuler est activé (non désactivé)."""
        btn = self.get_cancel_button(booking_row)
        return btn.count() > 0 and btn.is_enabled()

    def click_cancel_button(self, booking_row: Locator) -> None:
        """Clique sur le bouton 'Annuler' de la réservation donnée."""
        self.get_cancel_button(booking_row).click()

    # ── Dialog de confirmation ────────────────────────────────────────────────

    def get_confirmation_dialog(self) -> Locator:
        """Retourne le locator du dialog de confirmation d'annulation."""
        return self.page.locator(_DIALOG_SEL).first

    def confirmation_dialog_is_visible(self, timeout: int = 5_000) -> bool:
        """Indique si le dialog de confirmation est affiché."""
        try:
            expect(self.get_confirmation_dialog()).to_be_visible(timeout=timeout)
            return True
        except AssertionError:
            return False

    def confirm_cancellation(self) -> None:
        """Clique sur le bouton de confirmation ('Oui', 'Confirmer', …)."""
        dialog = self.get_confirmation_dialog()
        dialog.get_by_role("button", name=_CONFIRM_BTN_RE).first.click()
        self.page.wait_for_load_state("networkidle")

    def decline_cancellation(self) -> None:
        """Clique sur le bouton de refus ('Non', 'Fermer', …)."""
        dialog = self.get_confirmation_dialog()
        dialog.get_by_role("button", name=_DECLINE_BTN_RE).first.click()
        self.page.wait_for_load_state("networkidle")

    # ── Messages d'erreur ─────────────────────────────────────────────────────

    def get_error_message(self) -> Locator:
        """Retourne le locator du premier message d'erreur affiché."""
        return self.page.locator(_ERROR_SEL).first

    def has_24h_error(self, timeout: int = 5_000) -> bool:
        """Indique si un message d'erreur '< 24h' est affiché."""
        error = self.page.locator(_ERROR_SEL).filter(has_text=_ERROR_24H_RE).first
        try:
            expect(error).to_be_visible(timeout=timeout)
            return True
        except AssertionError:
            return False

    # ── Statut post-action ────────────────────────────────────────────────────

    def booking_shows_cancelled_status(self) -> bool:
        """Vérifie qu'au moins une réservation affiche le statut 'cancelled'."""
        locator = self.page.locator(
            f"{_ROW_SEL}, .status-badge, .badge"
        ).filter(has_text=_STATUS_RE["cancelled"]).first
        return locator.count() > 0 and locator.is_visible()

    # ── Réservation imminente (vol < 24h) ─────────────────────────────────────

    def get_imminent_booking_row(self) -> Locator:
        """
        Retourne la première réservation dont le vol part dans moins de 24h,
        identifiée par l'attribut data-departure-soon='true' ou la classe .imminent.
        """
        return self.page.locator(_ROW_SEL).filter(
            has=self.page.locator("[data-departure-soon='true'], .imminent, .soon")
        ).first

    # ── Screenshots ───────────────────────────────────────────────────────────

    def screenshot(self, name: str) -> None:
        """Prend un screenshot pleine page avec un nom explicite."""
        directory = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "reports", "screenshots", "cancellation",
        )
        os.makedirs(directory, exist_ok=True)
        ts = datetime.now().strftime("%H%M%S")
        path = os.path.join(directory, f"{ts}_{name}.png")
        self.page.screenshot(path=path, full_page=True)