"""
Vues de l'application Flights.
"""

from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, TemplateView
from django.utils import timezone
from django.contrib import messages
from django.db import models
from .models import Airport, Flight
from .forms import FlightSearchForm


class HomeView(TemplateView):
    """Page d'accueil avec formulaire de recherche de vols."""

    template_name = 'flights/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = FlightSearchForm()
        context['popular_destinations'] = Airport.objects.filter(
            is_active=True
        ).order_by('?')[:6]
        context['upcoming_flights'] = Flight.objects.filter(
            departure_time__gt=timezone.now(),
            is_active=True,
            status='scheduled'
        ).select_related('origin', 'destination')[:4]
        return context

    def post(self, request, *args, **kwargs):
        form = FlightSearchForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            request.session['search_params'] = {
                'origin': cd['origin'].code,
                'destination': cd['destination'].code,
                'departure_date': cd['departure_date'].isoformat(),
                'return_date': cd['return_date'].isoformat() if cd['return_date'] else None,
                'passengers': cd['passengers'],
                'travel_class': cd['travel_class'],
                'trip_type': cd['trip_type'],
            }
            return redirect('flights:search_results')
        messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
        context = self.get_context_data(**kwargs)
        context['search_form'] = form
        return self.render_to_response(context)


class FlightSearchResultsView(ListView):
    """Page de résultats de recherche de vols."""

    template_name = 'flights/search_results.html'
    context_object_name = 'flights'
    paginate_by = 10

    def get_queryset(self):
        params = self.request.session.get('search_params', {})
        if not params:
            return Flight.objects.none()

        origin_code = params.get('origin')
        destination_code = params.get('destination')
        departure_date_str = params.get('departure_date')
        passengers = int(params.get('passengers', 1))
        travel_class = params.get('travel_class', 'economy')

        try:
            from datetime import datetime
            departure_date = datetime.fromisoformat(departure_date_str).date()
        except (ValueError, TypeError):
            departure_date = timezone.now().date()

        flights = Flight.search_flights(
            origin_code=origin_code,
            destination_code=destination_code,
            departure_date=departure_date,
            passengers=passengers,
            travel_class=travel_class
        )
        return flights

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.session.get('search_params', {})
        context['search_params'] = params

        if params.get('origin'):
            context['origin'] = Airport.objects.filter(code=params['origin']).first()
        if params.get('destination'):
            context['destination'] = Airport.objects.filter(code=params['destination']).first()

        context['search_form'] = FlightSearchForm(initial={
            'origin_code': params.get('origin'),
            'destination_code': params.get('destination'),
            'departure_date': params.get('departure_date'),
            'passengers': params.get('passengers', 1),
            'travel_class': params.get('travel_class', 'economy'),
            'trip_type': params.get('trip_type', 'oneway'),
        })
        return context


class FlightDetailView(DetailView):
    """Page de détail d'un vol."""

    model = Flight
    template_name = 'flights/flight_detail.html'
    context_object_name = 'flight'
    slug_field = 'flight_number'
    slug_url_kwarg = 'flight_number'

    def get_queryset(self):
        return Flight.objects.filter(is_active=True).select_related(
            'origin', 'destination', 'aircraft'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flight = self.get_object()
        params = self.request.session.get('search_params', {})

        context['passengers'] = int(params.get('passengers', 1))
        context['travel_class'] = params.get('travel_class', 'economy')

        if context['travel_class'] == 'business':
            context['price_per_passenger'] = flight.get_current_price_business()
        else:
            context['price_per_passenger'] = flight.get_current_price_economy()

        context['total_price'] = context['price_per_passenger'] * context['passengers']

        # Vols similaires (même trajet)
        context['similar_flights'] = Flight.objects.filter(
            origin=flight.origin,
            destination=flight.destination,
            is_active=True,
            departure_time__gt=timezone.now()
        ).exclude(pk=flight.pk).select_related('origin', 'destination')[:3]

        return context


def airport_autocomplete(request):
    """API d'autocomplétion pour les aéroports."""
    query = request.GET.get('q', '')
    if len(query) >= 1:
        airports = Airport.objects.filter(
            is_active=True
        ).filter(
            models.Q(code__icontains=query) |
            models.Q(name__icontains=query) |
            models.Q(city__icontains=query)
        ).values('id', 'code', 'name', 'city', 'country')[:10]
        return JsonResponse(list(airports), safe=False)
    return JsonResponse([], safe=False)


class AirportListView(ListView):
    """Liste de tous les aéroports disponibles."""

    model = Airport
    template_name = 'flights/airports.html'
    context_object_name = 'airports'

    def get_queryset(self):
        return Airport.objects.filter(is_active=True).order_by('country', 'city')
