"""
Vues de l'application Accounts.
"""

from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView, UpdateView
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, UserForm


class RegisterView(View):
    """Vue d'inscription."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('flights:home')
        form = CustomUserCreationForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Créer le profil utilisateur
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, "Bienvenue ! Votre compte a été créé avec succès.")
            return redirect('flights:home')
        return render(request, 'accounts/register.html', {'form': form})


class LoginView(View):
    """Vue de connexion personnalisée."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('flights:home')
        form = CustomAuthenticationForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bon retour, {user.first_name or user.username} !")
            next_url = request.GET.get('next', 'flights:home')
            return redirect(next_url)
        return render(request, 'accounts/login.html', {'form': form})


class LogoutView(View):
    """Vue de déconnexion."""

    def get(self, request):
        logout(request)
        messages.info(request, "Vous avez été déconnecté.")
        return redirect('flights:home')


class ProfileView(LoginRequiredMixin, View):
    """Vue du profil utilisateur."""

    login_url = '/accounts/login/'  # Spécifier l'URL de redirection pour la connexion

    def get(self, request):
        user_form = UserForm(instance=request.user)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = UserProfileForm(instance=profile)
        return render(request, 'accounts/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form,
        })

    def post(self, request):
        user_form = UserForm(request.POST, instance=request.user)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('accounts:profile')

        return render(request, 'accounts/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form,
        })
