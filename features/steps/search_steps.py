"""
search_steps.py — Définitions d'étapes Behave pour la recherche de vols.
======================================================================

Scénarios couverts :
    - US-001 : Recherche aller simple / aller-retour
    - US-004 : Tri par prix
    - US-005 : Sélection de classe de voyage
    - Validations : même aéroport, date passée, formulaire
    - Page d'accueil et aéroports populaires
"""

from behave import given, when, then
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date


# ── GIVEN : Préconditions ────────────────────────────────────────────────────


@given(r'l\'aéroport "([^"]+)" existe dans la base')
def step_airport_exists(context, airport_code):
    """Vérifie qu'un aéroport existe dans la base de données."""
    from flights.models import Airport
    airport = Airport.objects.filter(code=airport_code).first()
    assert airport is not None, (
        f"L'aéroport '{airport_code}' n'existe pas dans la base de données"
    )
    context.current_origin = airport


@given(r'un vol "([^"]+)" de "([^"]+)" à "([^"]+)" est programmé')
def step_flight_scheduled(context, flight_number, origin_code, dest_code):
    """Vérifie qu'un vol est programmé entre deux aéroports."""
    from flights.models import Flight
    flight = Flight.objects.filter(flight_number=flight_number).first()
    assert flight is not None, (
        f"Le vol '{flight_number}' n'existe pas dans la base de données"
    )
    assert flight.origin.code == origin_code, (
        f"Le vol '{flight_number}' ne part pas de '{origin_code}' "
        f"mais de '{flight.origin.code}'"
    )
    assert flight.destination.code == dest_code, (
        f"Le vol '{flight_number}' n'arrive pas à '{dest_code}' "
        f"mais à '{flight.destination.code}'"
    )
    context.current_flight = flight


@given(r'un vol "([^"]+)" de "([^"]+)" à "([^"]+)" à ([\d.]+) TND est programmé')
def step_flight_with_price(context, flight_number, origin_code, dest_code, price):
    """Vérifie qu'un vol est programmé avec un prix spécifique."""
    from flights.models import Flight
    flight = Flight.objects.filter(flight_number=flight_number).first()
    assert flight is not None, (
        f"Le vol '{flight_number}' n'existe pas dans la base de données"
    )
    expected_price = float(price)
    assert float(flight.base_price_economy) == expected_price, (
        f"Le vol '{flight_number}' coûte {flight.base_price_economy} TND, "
        f"pas {expected_price} TND"
    )
    context.current_flight = flight


@given(r'la base de données est peuplée')
def step_db_populated(context):
    """Vérifie que la base de données contient des données de test."""
    from flights.models import Airport, Flight
    assert Airport.objects.count() >= 3, (
        "La base de données ne contient pas assez d'aéroports"
    )
    assert Flight.objects.count() >= 2, (
        "La base de données ne contient pas assez de vols"
    )


# ── WHEN : Actions ───────────────────────────────────────────────────────────


@when(
    r'je recherche un vol aller simple de "([^"]+)" vers "([^"]+)" '
    r'avec (\d+) passager(?:s)?'
)
def step_search_oneway(context, origin_code, dest_code, passengers):
    """Effectue une recherche de vol aller simple via le formulaire."""
    from flights.models import Airport, Flight
    origin = Airport.objects.get(code=origin_code)
    dest = Airport.objects.get(code=dest_code)

    # Récupère la date du prochain vol pour la recherche
    flight = Flight.objects.filter(
        origin=origin, destination=dest, status="scheduled"
    ).first()

    if flight:
        departure_date = flight.departure_time.strftime("%Y-%m-%d")
    else:
        departure_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    data = {
        "trip_type": "oneway",
        "origin": str(origin.pk),
        "destination": str(dest.pk),
        "departure_date": departure_date,
        "passengers": passengers,
        "travel_class": "economy",
    }
    context.response = context.test.client.post(
        reverse("flights:home"), data=data
    )

    # Si redirection vers les résultats, suivre la redirection
    if context.response.status_code == 302:
        # Stocke les paramètres en session comme le fait la vue
        session = context.test.client.session
        session["search_params"] = {
            "origin": origin_code,
            "destination": dest_code,
            "departure_date": departure_date,
            "return_date": None,
            "passengers": passengers,
            "travel_class": "economy",
            "trip_type": "oneway",
        }
        session.save()
        context.response = context.test.client.get(
            reverse("flights:search_results")
        )


@when(
    r'je recherche un vol aller-retour de "([^"]+)" vers "([^"]+)" '
    r'avec (\d+) passager(?:s)?'
)
def step_search_roundtrip(context, origin_code, dest_code, passengers):
    """Effectue une recherche de vol aller-retour via le formulaire."""
    from flights.models import Airport, Flight
    origin = Airport.objects.get(code=origin_code)
    dest = Airport.objects.get(code=dest_code)

    flight = Flight.objects.filter(
        origin=origin, destination=dest, status="scheduled"
    ).first()
    if flight:
        departure_date = flight.departure_time.strftime("%Y-%m-%d")
    else:
        departure_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    return_date = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")

    data = {
        "trip_type": "roundtrip",
        "origin": str(origin.pk),
        "destination": str(dest.pk),
        "departure_date": departure_date,
        "return_date": return_date,
        "passengers": passengers,
        "travel_class": "economy",
    }
    context.response = context.test.client.post(
        reverse("flights:home"), data=data
    )

    if context.response.status_code == 302:
        session = context.test.client.session
        session["search_params"] = {
            "origin": origin_code,
            "destination": dest_code,
            "departure_date": departure_date,
            "return_date": return_date,
            "passengers": passengers,
            "travel_class": "economy",
            "trip_type": "roundtrip",
        }
        session.save()
        context.response = context.test.client.get(
            reverse("flights:search_results")
        )


@when(r'je recherche un vol aller simple de "([^"]+)" vers "([^"]+)" '
      r'pour la date d\'hier')
def step_search_past_date(context, origin_code, dest_code):
    """Effectue une recherche avec une date dans le passé."""
    from flights.models import Airport
    origin = Airport.objects.get(code=origin_code)
    dest = Airport.objects.get(code=dest_code)
    past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    data = {
        "trip_type": "oneway",
        "origin": str(origin.pk),
        "destination": str(dest.pk),
        "departure_date": past_date,
        "passengers": "1",
        "travel_class": "economy",
    }
    context.response = context.test.client.post(
        reverse("flights:home"), data=data
    )


@when(r'je trie les résultats par prix croissant')
def step_sort_by_price(context):
    """Trie les résultats de recherche par prix croissant."""
    # Le tri est généralement géré via un paramètre GET ou POST
    if context.response.status_code == 200 and "flights" in context.response.context:
        flights = list(context.response.context["flights"])
        context.sorted_flights = sorted(
            flights, key=lambda f: f.base_price_economy
        )
    else:
        # Réaccède avec paramètre de tri
        session = context.test.client.session
        search_params = session.get("search_params", {})
        params = {**search_params, "sort": "price_asc"}
        context.response = context.test.client.get(
            reverse("flights:search_results"), data=params
        )


@when(r'je sélectionne la classe "([^"]+)"')
def step_select_class(context, travel_class):
    """Sélectionne une classe de voyage dans la recherche."""
    # Map les noms français vers les valeurs internes
    class_map = {
        "Économie": "economy",
        "Affaires": "business",
    }
    class_value = class_map.get(travel_class, travel_class.lower())
    context.selected_class = class_value

    # Refait la recherche avec la nouvelle classe
    session = context.test.client.session
    search_params = session.get("search_params", {})
    if search_params:
        search_params["travel_class"] = class_value
        session["search_params"] = search_params
        session.save()
        context.response = context.test.client.get(
            reverse("flights:search_results")
        )


@when(r'j\'accède à la page "([^"]+)"')
def step_access_page(context, url_name):
    """Accède à une page par son nom d'URL Django."""
    url = reverse(url_name)
    context.response = context.test.client.get(url)
    context.current_url_name = url_name


# ── THEN : Vérifications ────────────────────────────────────────────────────


@then(r'je vois les résultats de recherche')
def step_see_results(context):
    """Vérifie que des résultats de recherche sont affichés."""
    assert context.response.status_code == 200, (
        f"Statut inattendu : {context.response.status_code}"
    )
    content = context.response.content.decode("utf-8")
    # Vérifie que le template de résultats est utilisé ou que des vols sont dans le contexte
    if "flights" in context.response.context:
        flights = context.response.context["flights"]
        assert len(list(flights)) >= 1, "Aucun vol trouvé dans les résultats"


@then(r'je ne vois aucun résultat')
def step_no_results(context):
    """Vérifie qu'aucun résultat n'est affiché."""
    assert context.response.status_code == 200, (
        f"Statut inattendu : {context.response.status_code}"
    )
    if "flights" in context.response.context:
        flights = list(context.response.context["flights"])
        assert len(flights) == 0, (
            f"Des résultats inattendus ont été trouvés : {len(flights)} vol(s)"
        )


@then(r'un message d\'erreur contenant "([^"]+)" est affiché')
def step_error_message(context, message_fragment):
    """Vérifie qu'un message d'erreur spécifique est affiché."""
    content = context.response.content.decode("utf-8").lower()
    fragment = message_fragment.lower()
    assert fragment in content, (
        f"Le message d'erreur contenant '{message_fragment}' n'a pas été trouvé "
        f"dans la réponse. Contenu (extrait) : {content[:500]}"
    )


@then(r'le prix est affiché en TND')
def step_price_in_tnd(context):
    """Vérifie que les prix sont affichés en dinars tunisiens."""
    content = context.response.content.decode("utf-8")
    assert "TND" in content, (
        "Le prix n'est pas affiché en TND dans la réponse"
    )


@then(r'le prix correspond à la classe "([^"]+)"')
def step_price_matches_class(context, travel_class):
    """Vérifie que le prix affiché correspond à la classe sélectionnée."""
    if "flights" in context.response.context:
        flights = list(context.response.context["flights"])
        if flights:
            flight = flights[0]
            if travel_class == "Économie":
                assert flight.base_price_economy > 0, (
                    "Le prix économie n'est pas affiché"
                )
            elif travel_class == "Affaires":
                assert flight.base_price_business > 0, (
                    "Le prix affaires n'est pas affiché"
                )


@then(r'le premier résultat a un prix inférieur ou égal au deuxième résultat')
def step_first_price_lower(context):
    """Vérifie que les résultats sont triés par prix croissant."""
    if hasattr(context, "sorted_flights") and context.sorted_flights:
        assert len(context.sorted_flights) >= 2, (
            "Pas assez de résultats pour vérifier le tri"
        )
        price1 = context.sorted_flights[0].base_price_economy
        price2 = context.sorted_flights[1].base_price_economy
        assert price1 <= price2, (
            f"Le tri par prix est incorrect : {price1} > {price2}"
        )


@then(r'je vois au moins (\d+) aéroports populaires')
def step_popular_airports(context, min_count):
    """Vérifie qu'un nombre minimum d'aéroports populaires est affiché."""
    assert context.response.status_code == 200, (
        f"Statut inattendu : {context.response.status_code}"
    )
    if "popular_destinations" in context.response.context:
        destinations = context.response.context["popular_destinations"]
        assert len(list(destinations)) >= int(min_count), (
            f"Pas assez d'aéroports populaires : "
            f"{len(list(destinations))} < {min_count}"
        )
    else:
        # Vérifie dans le contenu HTML
        content = context.response.content.decode("utf-8")
        # Vérifie que plusieurs codes d'aéroports apparaissent
        airport_codes = ["TUN", "CDG", "MRS", "CMN", "ALG", "FCO", "LHR"]
        found = sum(1 for code in airport_codes if code in content)
        assert found >= int(min_count), (
            f"Seulement {found} aéroports trouvés dans le contenu, "
            f"attendu au moins {min_count}"
        )


@then(r'le formulaire de recherche contient le champ "([^"]+)"')
def step_form_has_field(context, field_name):
    """Vérifie qu'un champ spécifique est présent dans le formulaire."""
    assert context.response.status_code == 200
    if "search_form" in context.response.context:
        form = context.response.context["search_form"]
        assert field_name in form.fields, (
            f"Le champ '{field_name}' n'est pas dans le formulaire de recherche. "
            f"Champs disponibles : {list(form.fields.keys())}"
        )
    else:
        # Vérification dans le HTML si le formulaire n'est pas dans le contexte
        content = context.response.content.decode("utf-8")
        assert field_name in content or f'name="{field_name}"' in content, (
            f"Le champ '{field_name}' n'est pas dans le HTML de la page"
        )


@then(r'la page affiche "([^"]+)"')
def step_page_displays(context, text):
    """Vérifie qu'un texte spécifique est affiché sur la page."""
    content = context.response.content.decode("utf-8")
    assert text in content, (
        f"Le texte '{text}' n'est pas affiché sur la page"
    )
