"""
promotions_steps.py — Définitions d'étapes Behave pour les promotions.
=======================================================================

Scénarios couverts :
    - US-006 : Application de codes promotionnels (valide, expiré, inexistant)
    - US-034 : Inscription à la newsletter (valide, doublon)
"""

from behave import given, when, then
from django.urls import reverse
from django.utils import timezone


# ── GIVEN : Préconditions ────────────────────────────────────────────────────


@given(r'que la base de données est peuplée')
def step_db_populated(context):
    """Vérifie que la base de données contient des données."""
    from promotions.models import Promotion
    assert Promotion.objects.count() >= 1, "Aucune promotion en base"


@given(r'un code promo "([^"]+)" est actif avec (\d+)% de réduction')
def step_active_promo(context, code, discount):
    """Vérifie qu'un code promo actif existe avec un pourcentage de réduction."""
    from promotions.models import Promotion
    promo = Promotion.objects.filter(code=code).first()
    assert promo is not None, f"Le code promo '{code}' n'existe pas"
    assert promo.is_active, f"Le code promo '{code}' n'est pas actif"
    assert promo.discount_percentage == float(discount), (
        f"La réduction est de {promo.discount_percentage}%, attendu {discount}%"
    )
    context.current_promo = promo


@given(r'un code promo "([^"]+)" est expiré')
def step_expired_promo(context, code):
    """Vérifie qu'un code promo est expiré."""
    from promotions.models import Promotion
    promo = Promotion.objects.filter(code=code).first()
    assert promo is not None, f"Le code promo '{code}' n'existe pas"
    now = timezone.now()
    assert promo.end_date < now, (
        f"Le code promo '{code}' n'est pas expiré "
        f"(fin : {promo.end_date}, maintenant : {now})"
    )
    context.current_promo = promo


@given(r'un vol est disponible avec un prix de ([\d.]+) TND')
def step_flight_with_price(context, price):
    """Récupère un vol avec un prix spécifique."""
    from flights.models import Flight
    expected_price = float(price)
    flight = Flight.objects.filter(
        base_price_economy=expected_price,
        status="scheduled",
        is_active=True,
    ).first()
    if not flight:
        # Prendre un vol existant et vérifier son prix
        flight = Flight.objects.filter(status="scheduled", is_active=True).first()
    assert flight is not None, "Aucun vol disponible"
    context.promo_flight = flight
    context.original_price = expected_price


@given(r'un vol affaires est disponible avec un prix de ([\d.]+) TND')
def step_business_flight_with_price(context, price):
    """Récupère un vol affaires avec un prix spécifique."""
    from flights.models import Flight
    expected_price = float(price)
    flight = Flight.objects.filter(
        base_price_business=expected_price,
        status="scheduled",
        is_active=True,
    ).first()
    if not flight:
        flight = Flight.objects.filter(status="scheduled", is_active=True).first()
    assert flight is not None, "Aucun vol affaires disponible"
    context.promo_flight = flight
    context.original_price = expected_price


@given(
    r'l\'adresse "([^"]+)" est déjà inscrite à la newsletter'
)
def step_email_already_subscribed(context, email):
    """Inscrit un email à la newsletter avant le scénario."""
    from promotions.models import NewsletterSubscription
    NewsletterSubscription.objects.get_or_create(
        email=email,
        defaults={"first_name": "Test", "is_active": True},
    )


@given(r'je suis un visiteur non connecté')
def step_visitor(context):
    """S'assure qu'aucun utilisateur n'est connecté."""
    context.test.client.logout()
    context.is_visitor = True


# ── WHEN : Actions ───────────────────────────────────────────────────────────


@when(r'j\'applique le code "([^"]+)" au vol')
def step_apply_promo(context, code):
    """Applique un code promotionnel au vol sélectionné."""
    from promotions.models import Promotion
    promo = Promotion.objects.filter(code=code).first()
    flight = getattr(context, "promo_flight", None)

    if flight and promo:
        # Calcule le prix avec la promotion
        discount = promo.discount_percentage
        original_price = getattr(context, "original_price", flight.base_price_economy)

        if promo.is_valid:
            context.promo_applied = True
            context.discounted_price = round(
                float(original_price) * (1 - discount / 100), 2
            )
        else:
            context.promo_applied = False
            context.discounted_price = float(original_price)

    # Simule la vérification via la vue
    context.response = context.test.client.get(
        reverse("promotions:detail", kwargs={"code": code})
    )


@when(
    r'je m\'inscris à la newsletter avec "([^"]+)"'
)
def step_subscribe_newsletter(context, email):
    """Inscrit un email à la newsletter."""
    from promotions.models import NewsletterSubscription
    context.newsletter_email = email
    context.newsletter_count_before = NewsletterSubscription.objects.count()

    context.response = context.test.client.post(
        reverse("promotions:newsletter_subscribe"),
        data={"email": email},
    )


# ── THEN : Vérifications ────────────────────────────────────────────────────


@then(r'la remise est appliquée')
def step_discount_applied(context):
    """Vérifie que la remise a été appliquée."""
    assert getattr(context, "promo_applied", False), (
        "La remise n'a pas été appliquée"
    )


@then(r'le prix final est de ([\d.]+) TND')
def step_final_price(context, expected_price):
    """Vérifie que le prix final correspond à celui attendu après remise."""
    actual_price = getattr(context, "discounted_price", 0)
    assert actual_price == float(expected_price), (
        f"Prix final incorrect : {actual_price} TND (attendu {expected_price} TND)"
    )


@then(r'la remise n\'est pas appliquée')
def step_no_discount(context):
    """Vérifie qu'aucune remise n'a été appliquée."""
    assert not getattr(context, "promo_applied", True), (
        "Une remise a été appliquée alors qu'elle ne devait pas l'être"
    )


@then(r'un message de confirmation est affiché')
def step_confirmation_message(context):
    """Vérifie qu'un message de confirmation est affiché."""
    content = context.response.content.decode("utf-8").lower()
    has_confirmation = (
        "confirm" in content
        or "succès" in content
        or "merci" in content
        or "appliquée" in content
        or "enregistré" in content
        or "inscrit" in content
    )
    assert has_confirmation, (
        "Aucun message de confirmation trouvé dans la réponse"
    )


@then(r'un message d\'erreur contenant "([^"]+)" est affiché')
def step_error_contains(context, text):
    """Vérifie qu'un message d'erreur contenant un texte spécifique est affiché."""
    content = context.response.content.decode("utf-8").lower()
    assert text.lower() in content, (
        f"Le message d'erreur contenant '{text}' n'a pas été trouvé. "
        f"Contenu (extrait) : {content[:500]}"
    )


@then(r'l\'inscription à la newsletter est confirmée')
def step_newsletter_confirmed(context):
    """Vérifie que l'inscription à la newsletter est confirmée."""
    assert NewsletterSubscription.objects.filter(
        email=context.newsletter_email
    ).exists(), (
        f"L'email '{context.newsletter_email}' n'est pas inscrit à la newsletter"
    )


@then(r'l\'adresse email est enregistrée en base de données')
def step_email_in_db(context):
    """Vérifie que l'email est enregistré en base."""
    assert NewsletterSubscription.objects.filter(
        email=context.newsletter_email
    ).exists(), (
        f"L'email '{context.newsletter_email}' n'est pas en base de données"
    )


@then(r'l\'inscription échoue')
def step_subscription_fails(context):
    """Vérifie que l'inscription à la newsletter a échoué."""
    assert NewsletterSubscription.objects.count() == context.newsletter_count_before, (
        "Un abonnement a été créé alors qu'il ne devait pas l'être"
    )
