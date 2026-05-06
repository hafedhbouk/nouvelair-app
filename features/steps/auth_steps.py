"""
auth_steps.py — Définitions d'étapes Behave pour l'authentification.
=====================================================================

Scénarios couverts :
    - US-027 : Inscription avec données valides
    - US-027 : Inscription avec email dupliqué
    - US-028 : Connexion réussie
    - US-028 : Connexion échouée
    - US-028 : Déconnexion
    - US-030 : Mise à jour du profil
    - Accès profil nécessite connexion
"""

from behave import given, when, then
from django.urls import reverse


# ── GIVEN : Préconditions ────────────────────────────────────────────────────


@given(r'je suis connecté en tant que "([^"]+)" avec le mot de passe "([^"]+)"')
def step_logged_in(context, username, password):
    """Connecte un utilisateur via le client de test."""
    from django.contrib.auth.models import User
    success = context.test.client.login(username=username, password=password)
    assert success, (
        f"Impossible de connecter l'utilisateur '{username}' "
        f"avec le mot de passe fourni"
    )
    context.logged_in_user = User.objects.get(username=username)
    context.is_visitor = False


# ── WHEN : Actions ───────────────────────────────────────────────────────────


@when(
    r'je m\'inscris avec les données valides suivantes:'
)
def step_register_valid(context):
    """Inscrit un nouvel utilisateur avec des données valides."""
    from django.contrib.auth.models import User
    from accounts.models import UserProfile
    table = context.table
    row = table.rows[0]

    data = {
        "username": row["username"],
        "first_name": row["prenom"],
        "last_name": row["nom"],
        "email": row["email"],
        "password1": row["mot_de_passe"],
        "password2": row["confirmation"],
    }

    context.user_count_before = User.objects.count()
    context.profile_count_before = UserProfile.objects.count()

    context.response = context.test.client.post(
        reverse("accounts:register"), data=data
    )


@when(
    r'je m\'inscris avec les données suivantes ayant un email dupliqué:'
)
def step_register_duplicate_email(context):
    """Tente d'inscrire un utilisateur avec un email déjà utilisé."""
    from django.contrib.auth.models import User
    table = context.table
    row = table.rows[0]

    data = {
        "username": row["username"],
        "first_name": row["prenom"],
        "last_name": row["nom"],
        "email": row["email"],
        "password1": row["mot_de_passe"],
        "password2": row["confirmation"],
    }

    context.user_count_before = User.objects.count()

    context.response = context.test.client.post(
        reverse("accounts:register"), data=data
    )


@when(r'je me connecte avec "([^"]+)" et "([^"]+)"')
def step_login(context, username, password):
    """Tente de se connecter avec un nom d'utilisateur et un mot de passe."""
    context.response = context.test.client.post(
        reverse("accounts:login"),
        data={"username": username, "password": password},
    )


@when(r'je me déconnecte')
def step_logout(context):
    """Déconnecte l'utilisateur courant."""
    context.response = context.test.client.get(reverse("accounts:logout"))


@when(r'je mets à jour mon profil avec les données suivantes:')
def step_update_profile(context):
    """Met à jour le profil utilisateur avec de nouvelles données."""
    table = context.table
    row = table.rows[0]

    data = {
        "first_name": row["prenom"],
        "last_name": row["nom"],
        "email": row["email"],
        "phone": row["telephone"],
        "city": row["ville"],
        "country": row["pays"],
        "date_of_birth": "1990-01-15",
        "nationality": "Tunisienne",
        "passport_number": "PASS12345",
        "gender": "M",
        "newsletter": "on",
    }

    context.response = context.test.client.post(
        reverse("accounts:profile"), data=data
    )


# ── THEN : Vérifications ────────────────────────────────────────────────────


@then(r'le compte est créé avec succès')
def step_account_created(context):
    """Vérifie qu'un nouveau compte a été créé."""
    from django.contrib.auth.models import User
    assert User.objects.count() == context.user_count_before + 1, (
        "Le compte n'a pas été créé"
    )


@then(r'je suis connecté automatiquement')
def step_auto_logged_in(context):
    """Vérifie que l'utilisateur est automatiquement connecté après inscription."""
    user = context.test.client.session.get("_auth_user_id")
    assert user is not None, "L'utilisateur n'est pas connecté"


@then(r'un profil utilisateur est créé automatiquement')
def step_profile_created(context):
    """Vérifie qu'un profil a été créé pour l'utilisateur."""
    from django.contrib.auth.models import User
    from accounts.models import UserProfile
    latest_user = User.objects.latest("id")
    assert hasattr(latest_user, "profile"), (
        "Aucun profil n'a été créé pour le nouvel utilisateur"
    )


@then(r'le compte n\'est pas créé')
def step_account_not_created(context):
    """Vérifie qu'aucun nouveau compte n'a été créé."""
    from django.contrib.auth.models import User
    assert User.objects.count() == context.user_count_before, (
        "Un compte a été créé malgré l'erreur attendue"
    )


@then(r'je suis connecté avec succès')
def step_login_success(context):
    """Vérifie que la connexion a réussi."""
    user = context.test.client.session.get("_auth_user_id")
    assert user is not None, "L'utilisateur n'est pas connecté"


@then(r'je ne suis pas connecté')
def step_not_logged_in(context):
    """Vérifie que l'utilisateur n'est pas connecté."""
    user = context.test.client.session.get("_auth_user_id")
    assert user is None, "L'utilisateur est connecté alors qu'il ne devrait pas l'être"


@then(r'je suis déconnecté')
def step_logged_out(context):
    """Vérifie que l'utilisateur a été déconnecté."""
    user = context.test.client.session.get("_auth_user_id")
    assert user is None, "L'utilisateur est encore connecté"


@then(r'je reste sur la page "([^"]+)"')
def step_stay_on_page(context, url_name):
    """Vérifie que l'utilisateur reste sur la même page (pas de redirection)."""
    expected_url = reverse(url_name)
    if context.response.status_code in (301, 302):
        assert context.response.url == expected_url, (
            f"Redirection inattendue vers {context.response.url}"
        )
    else:
        assert context.response.status_code == 200, (
            f"Statut inattendu : {context.response.status_code}"
        )


@then(r'le profil est mis à jour avec succès')
def step_profile_updated(context):
    """Vérifie que la mise à jour du profil a réussi."""
    assert context.response.status_code in (200, 302), (
        f"Statut inattendu : {context.response.status_code}"
    )


@then(r'les informations sont sauvegardées en base de données')
def step_info_saved(context):
    """Vérifie que les informations sont bien enregistrées."""
    user = context.logged_in_user
    user.refresh_from_db()
    assert user.email == "modified@exemple.com", (
        f"Email non mis à jour : {user.email}"
    )
    user.profile.refresh_from_db()
    assert user.profile.phone == "+21698765432", (
        f"Téléphone non mis à jour : {user.profile.phone}"
    )
    assert user.profile.city == "Sousse", (
        f"Ville non mise à jour : {user.profile.city}"
    )
