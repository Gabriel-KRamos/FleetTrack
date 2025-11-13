from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from .models import Vehicle, Driver, Maintenance
from accounts.models import UserProfile
from .forms import (
    UserProfileEditForm, CompanyProfileEditForm
)
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .services import get_vehicle_alerts


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        
        all_vehicles = list(Vehicle.objects.filter(user_profile=profile))
        vehicle_overview = {
            'total': len(all_vehicles), 'available': 0, 'in_use': 0,
            'maintenance': 0, 'unavailable': 0
        }
        for vehicle in all_vehicles:
            dynamic_slug = vehicle.dynamic_status_slug
            if dynamic_slug == 'available': vehicle_overview['available'] += 1
            elif dynamic_slug == 'on_route': vehicle_overview['in_use'] += 1
            elif dynamic_slug == 'maintenance': vehicle_overview['maintenance'] += 1
            elif dynamic_slug == 'disabled': vehicle_overview['unavailable'] += 1
        
        driver_overview = {
            'total': Driver.objects.filter(user_profile=profile).count(),
            'active': Driver.objects.filter(user_profile=profile, is_active=True).count(),
            'inactive': Driver.objects.filter(user_profile=profile, is_active=False).count(),
        }
        
        now = timezone.now()
        vehicle_alerts = get_vehicle_alerts(profile, limit=5)
        upcoming_maintenances = Maintenance.objects.select_related('vehicle').filter(
            user_profile=profile, status='scheduled', start_date__gte=now
        ).order_by('start_date')[:3]
        
        context = {
            'vehicle_overview': vehicle_overview,
            'driver_overview': driver_overview,
            'upcoming_maintenances': upcoming_maintenances,
            'vehicle_alerts': vehicle_alerts,
        }
        return render(request, 'dashboard/dashboard.html', context)

class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        user_form = UserProfileEditForm(instance=request.user)
        company_form = CompanyProfileEditForm(instance=profile)
        password_form = PasswordChangeForm(request.user)

        context = {
            'user': request.user,
            'profile': profile,
            'user_form': user_form,
            'company_form': company_form,
            'password_form': password_form,
            'show_password_form_errors': False
        }
        return render(request, 'dashboard/user_profile.html', context)

    def post(self, request):
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        user_form = UserProfileEditForm(instance=request.user)
        company_form = CompanyProfileEditForm(instance=profile)
        password_form = PasswordChangeForm(request.user)
        show_password_form_errors = False

        if 'update_profile' in request.POST:
            user_form = UserProfileEditForm(request.POST, instance=request.user)
            company_form = CompanyProfileEditForm(request.POST, instance=profile)

            if user_form.is_valid() and company_form.is_valid():
                user_form.save()
                company_form.save()
                messages.success(request, 'Perfil atualizado com sucesso!')
                return redirect('user-profile')
            else:
                messages.error(request, 'Erro ao atualizar o perfil. Verifique os campos.')

        elif 'update_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('user-profile')
            else:
                messages.error(request, 'Erro ao alterar a senha. Verifique os campos.')
                show_password_form_errors = True

        context = {
            'user': request.user,
            'profile': profile,
            'user_form': user_form,
            'company_form': company_form,
            'password_form': password_form,
            'show_password_form_errors': show_password_form_errors
        }
        return render(request, 'dashboard/user_profile.html', context)