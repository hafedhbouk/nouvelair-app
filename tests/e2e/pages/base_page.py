"""
Page Object Model – Classe de base (Jour 6).

Classe abstraite BasePage servant de fondation à toutes les Page Objects.
Encapsule les opérations de navigation et d'interaction communes
à toutes les pages de l'application NouvelAir.
"""

from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")

    def navigate(self, path: str):
        """Navigate to a full URL built from base_url + path."""
        full_url = f"{self.base_url}{path}"
        self.page.goto(full_url, wait_until="domcontentloaded")

    def wait_for_selector(self, selector: str, timeout: int = 5000):
        self.page.wait_for_selector(selector, timeout=timeout)