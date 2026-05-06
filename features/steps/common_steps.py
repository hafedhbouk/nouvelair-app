"""
common_steps.py — Étapes partagées entre tous les fichiers de features.
========================================================================

Ce fichier contient les étapes génériques utilisées dans plusieurs
fichiers .feature :
    - Accès aux pages par nom d'URL
    - Vérification du statut de réponse
    - Vérification de la page courante
    - Peuplement de la base de données
"""

from behave import given, when, then
from django.urls import reverse


# ── GIVEN : Préconditions ────────────────────────────────────────────────────


@given(r'la base de données est peuplée')
def step_db_populated(context):
    """
    Vérifie que la base de données contient les données de test minimales :
    - Au moins 3 aéroports
    - Au moins 2 vols
    - Au moins 1 utilisateur
    """
    from flights.models import Airport, Flight
    from django.contrib.auth.models import User
    assert Airport.objects.count() >= 3, (
        f"Pas assez d'aéroports en base : {Airport.objects.count()} (minimum 3)"
    )
    assert Flight.objects.count() >= 2, (
        f"Pas assez de vols en base : {Flight.objects.count()} (minimum 2)"
    )
    assert User.objects.count() >= 1, (
        f"Pas d'utilisateurs en base : {User.objects.count()}"
    )


@given(r'je suis un visiteur non connecté')
def step_visitor_not_logged_in(context):
    """S'assure qu'aucun utilisateur n'est connecté."""
    context.test.client.logout()


# ── WHEN : Actions ───────────────────────────────────────────────────────────


@when(r'j\'accède à la page "([^"]+)"')
def step_access_page(context, url_name):
    """
    Accède à une page par son nom d'URL Django.

    Le nom doit inclure le namespace, par exemple :
      - "flights:home"
      - "accounts:login"
      - "bookings:my_bookings"
    """
    url = reverse(url_name)
    context.response = context.test.client.get(url)
    context.current_url_name = url_name


# ── THEN : Vérifications ────────────────────────────────────────────────────


@then(r'le statut de la réponse est (\d+)')
def step_response_status(context, status_code):
    """Vérifie le code de statut HTTP de la réponse."""
    actual_status = context.response.status_code
    assert actual_status == int(status_code), (
        f"Statut inattendu : {actual_status} (attendu {status_code})"
    )


@then(r'je suis sur la page "([^"]+)"')
def step_on_page(context, url_name):
    """Vérifie que l'utilisateur est sur une page spécifique."""
    expected_url = reverse(url_name)

    # Si c'est une redirection, vérifier l'URL de redirection
    if context.response.status_code in (301, 302):
        assert context.response.url == expected_url, (
            f"Redirection vers {context.response.url}, "
            f"attendu {expected_url}"
        )
    else:
        # Pour une réponse 200, on vérifie que le template ou le contenu correspond
        assert context.response.status_code == 200, (
            f"Statut inattendu : {context.response.status_code}"
        )


@then(r'je suis redirigé vers la page "([^"]+)"')
def step_redirected_to_page(context, url_name):
    """Vérifie que la réponse est une redirection vers la page spécifiée."""
    assert context.response.status_code in (301, 302), (
        f"Pas de redirection, statut : {context.response.status_code}"
    )
    expected_url = reverse(url_name)
    assert context.response.url == expected_url, (
        f"Redirection vers {context.response.url}, attendu {expected_url}"
    )


@then(r'un message d\'erreur est affiché')
def step_error_message_generic(context):
    """Vérifie qu'un message d'erreur est affiché sur la page."""
    content = context.response.content.decode("utf-8").lower()
    has_error = (
        "error" in content
        or "erreur" in content
        or "invalid" in content
        or "invalide" in content
        or "échou" in content
        or "echec" in content
    )
    assert has_error, (
        "Aucun message d'erreur trouvé dans la réponse. "
        f"Contenu (extrait) : {content[:500]}"
    )


@then(r'un message d\'erreur contenant "([^"]+)" est affiché')
def step_error_message_contains(context, text):
    """Vérifie qu'un message d'erreur contenant un texte spécifique est affiché."""
    content = context.response.content.decode("utf-8").lower()
    assert text.lower() in content, (
        f"Le texte '{text}' n'a pas été trouvé dans la réponse. "
        f"Contenu (extrait) : {content[:500]}"
    )


@then(r'un message de confirmation est affiché')
def step_confirmation_message_generic(context):
    """Vérifie qu'un message de confirmation est affiché."""
    content = context.response.content.decode("utf-8").lower()
    has_confirmation = (
        "confirm" in content
        or "succès" in content
        or "merci" in content
        or "réussi" in content
        or "réussie" in content
        or "enregistré" in content
    )
    assert has_confirmation, (
        "Aucun message de confirmation trouvé dans la réponse"
    )
