"""
Page Object Model – Page de connexion (Jour 6).

Encapsule les interactions avec la page de connexion (/accounts/login/) :
- Remplissage des champs de connexion
- Soumission du formulaire
- Gestion des messages d'erreur
"""

from playwright.sync_api import Page
from .base_page import BasePage


class LoginPage(BasePage):
    """Page Object for the NouvelAir login page."""

    url = "/accounts/connexion/"

    def __init__(self, page: Page, base_url: str = "http://127.0.0.1:8000"):
        """
        Initialise la page de connexion.

        Args:
            page: instance de page Playwright (sync API).
            base_url: URL de base de l'application NouvelAir.
        """
        super().__init__(page, base_url)

    def fill_username(self, username: str) -> None:
        """
        Remplit le champ nom d'utilisateur.

        Args:
            username: nom d'utilisateur à saisir.
        """
        self.fill("input[name='username']", username)

    def fill_password(self, password: str) -> None:
        """
        Remplit le champ mot de passe.

        Args:
            password: mot de passe à saisir.
        """
        self.fill("input[name='password']", password)

    def submit(self) -> None:
        """Soumet le formulaire de connexion."""
        self.click("button[type='submit']")

    def get_error_message(self) -> str:
        """
        Retourne le message d'erreur de connexion s'il existe.

        Returns:
            str: texte du message d'erreur ou chaîne vide si aucun.
        """
        try:
            return self.page.locator(".alert-danger, .errorlist").first.text_content()
        except Exception:
            return ""

    def login(self, username: str, password: str) -> None:
        """
        Effectue la connexion en remplissant les champs et en soumettant.

        Args:
            username: nom d'utilisateur.
            password: mot de passe.
        """
        self.fill_username(username)
        self.fill_password(password)
        self.submit()