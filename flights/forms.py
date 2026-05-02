"""
Formulaire Flight - Formulaires de recherche et filtrage des vols.
"""

from django import forms
from datetime import date, timedelta

from .models import Airport


class FlightSearchForm(forms.Form):
    """Formulaire principal de recherche de vols (aller simple)."""

    TRAVEL_CLASS_CHOICES = [
        ('economy', 'Économie'),
        ('business', 'Affaires'),
    ]

    TRIP_TYPE_CHOICES = [
        ('oneway', 'Aller simple'),
        ('roundtrip', 'Aller-retour'),
    ]

    trip_type = forms.ChoiceField(
        choices=TRIP_TYPE_CHOICES,
        initial='oneway',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Type de voyage"
    )
    origin = forms.ModelChoiceField(
        queryset=Airport.objects.filter(is_active=True).order_by('city'),
        empty_label="Sélectionnez l'aéroport de départ",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'origin-select'}),
        label="De"
    )
    destination = forms.ModelChoiceField(
        queryset=Airport.objects.filter(is_active=True).order_by('city'),
        empty_label="Sélectionnez l'aéroport d'arrivée",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'destination-select'}),
        label="Vers"
    )
    departure_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'min': date.today().strftime('%Y-%m-%d'),
            }
        ),
        label="Date de départ",
        initial=date.today() + timedelta(days=3)
    )
    return_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
            }
        ),
        label="Date de retour"
    )
    passengers = forms.IntegerField(
        min_value=1,
        max_value=9,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 9}),
        label="Passagers"
    )
    travel_class = forms.ChoiceField(
        choices=TRAVEL_CLASS_CHOICES,
        initial='economy',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Classe"
    )

    def clean(self):
        cleaned_data = super().clean()
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        departure_date = cleaned_data.get('departure_date')
        return_date = cleaned_data.get('return_date')
        trip_type = cleaned_data.get('trip_type')

        if origin and destination and origin == destination:
            raise forms.ValidationError(
                "L'aéroport de départ et d'arrivée doivent être différents."
            )

        if departure_date and departure_date < date.today():
            raise forms.ValidationError(
                "La date de départ ne peut pas être dans le passé."
            )

        if trip_type == 'roundtrip' and return_date:
            if return_date <= departure_date:
                raise forms.ValidationError(
                    "La date de retour doit être postérieure à la date de départ."
                )

        return cleaned_data
