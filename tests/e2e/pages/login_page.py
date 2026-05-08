from playwright.sync_api import Page
from pages.base_page import BasePage


class LoginPage(BasePage):
    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.url = "/accounts/connexion/"      # ← was /accounts/login/

    def fill_username(self, username: str):
        self.page.fill('input[name="username"]', username)

    def fill_password(self, password: str):
        self.page.fill('input[name="password"]', password)

    def submit(self):
        self.page.click('button[type="submit"]')

    def get_error_message(self) -> str:
        locator = self.page.locator(".alert-danger, .errorlist")
        if locator.count() > 0:
            return locator.first.text_content() or ""
        return ""