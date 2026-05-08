"""
Page Object Model – Page d'inscription (Jour 6).

Encapsule les interactions avec la page d'inscription (/accounts/register/) :
- Remplissage du formulaire d'inscription
- Soumission et validation
"""

from .base_page import BasePage


class RegisterPage(BasePage):
    """
    Page Object pour la page d'inscription de NouvelAir.

    Fournit des méthodes pour remplir le formulaire d'inscription
    avec toutes les informations requises et le soumettre.

    Attributes:
        url (str): chemin relatif de la page d'inscription.
    """

    url = "/accounts/inscription/"

    def fill_form(
        self,
        username: str,
        email: str,
        password1: str,
        password2: str,
        first_name: str = "",
        last_name: str = "",
    ) -> None:
        """
        Remplit tous les champs du formulaire d'inscription.

        Args:
            username: nom d'utilisateur souhaité.
            email: adresse email.
            password1: mot de passe.
            password2: confirmation du mot de passe.
            first_name: prénom (optionnel).
            last_name: nom de famille (optionnel).
        """
        # Remplir les champs principaux
        self.fill("input[name='username']", username)
        self.fill("input[name='email']", email)
        self.fill("input[name='password1']", password1)
        self.fill("input[name='password2']", password2)
        
        # Remplir les champs optionnels s'ils existent
        if first_name:
            try:
                self.fill("input[name='first_name']", first_name)
            except Exception:
                pass  # Champ optionnel
        
        if last_name:
            try:
                self.fill("input[name='last_name']", last_name)
            except Exception:
                pass  # Champ optionnel

    def submit(self) -> None:
        """
        Soumet le formulaire d'inscription.
        """
        submit_btn = self.page.locator(
            "button[type='submit']:has-text('S\\'inscrire'), "
            "button[type='submit']:has-text('Inscription'), "
            "button[type='submit']"
        )
        self.click("button[type='submit']")
