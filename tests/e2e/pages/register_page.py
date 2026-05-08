"""
Page Object Model – Page d'inscription (Jour 6).

Encapsule les interactions avec la page d'inscription (/accounts/register/) :
- Remplissage du formulaire d'inscription
- Soumission et validation
"""

from playwright.sync_api import Page
from pages.base_page import BasePage


class RegisterPage(BasePage):
    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.url = "/accounts/inscription/"    # ← was /accounts/register/

    def fill_form(self, username: str, email: str, password1: str, password2: str):
        self.page.fill('input[name="username"]', username)
        self.page.fill('input[name="email"]', email)
        self.page.fill('input[name="password1"]', password1)
        self.page.fill('input[name="password2"]', password2)

    def submit(self):
        self.page.click('button[type="submit"]')