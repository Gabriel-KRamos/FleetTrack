from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from datetime import date, timedelta, datetime
from django.utils import timezone
from .models import Vehicle, Driver, Maintenance, Route, AlertConfiguration
from accounts.models import UserProfile
from .forms import (
    VehicleForm, DriverForm, MaintenanceForm, RouteForm,
    MaintenanceCompletionForm, RouteCompletionForm, AlertConfigurationFormSet,
    UserProfileEditForm, CompanyProfileEditForm
)
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from django.db.models import Q
from django.utils.text import slugify
from django.views.generic import RedirectView
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from collections import Counter

import requests
import re


class VehicleAlert:
    def __init__(self, vehicle, service_type, message, priority='medium', overdue_value=0, overdue_unit='days'):
        self.vehicle = vehicle
        self.service_type = service_type
        self.message = message
        self.priority = priority
        self.overdue_value = overdue_value
        self.overdue_unit = overdue_unit

    def __lt__(self, other):
        priority_order = {'low': 0, 'medium': 1, 'high': 2}
        my_priority = priority_order.get(self.priority, 1)
        other_priority = priority_order.get(other.priority, 1)

        if my_priority != other_priority:
            return my_priority < other_priority

        if self.overdue_unit == 'km' and other.overdue_unit == 'days':
            return False
        if self.overdue_unit == 'days' and other.overdue_unit == 'km':
            return True
        return self.overdue_value < other.overdue_value


def get_vehicle_alerts(limit=None):
    alerts = []
    now = timezone.now()
    today = now.date()
    active_vehicles = Vehicle.objects.exclude(status='disabled')

    active_rules = AlertConfiguration.objects.filter(is_active=True)
    rules_dict = {rule.service_type: rule for rule in active_rules}

    for vehicle in active_vehicles:
        current_mileage = vehicle.mileage

        for service_type, rule in rules_dict.items():
            last_maint = Maintenance.objects.filter(
                vehicle=vehicle,
                service_type=service_type,
                status='completed'
            ).order_by('-actual_end_date').first()

            last_km: int
            last_service_date: date

            if last_maint:
                last_km = last_maint.current_mileage
                last_date_obj = last_maint.actual_end_date
                if isinstance(last_date_obj, datetime):
                    last_service_date = last_date_obj.date()
                elif isinstance(last_maint.end_date, datetime):
                     last_service_date = last_maint.end_date.date()
                elif isinstance(last_maint.end_date, date):
                    last_service_date = last_maint.end_date
                else:
                   last_service_date = vehicle.acquisition_date

            else:
                last_km = vehicle.initial_mileage
                last_service_date = vehicle.acquisition_date

            if not isinstance(last_service_date, date):
                last_service_date = vehicle.acquisition_date or today

            km_alert_triggered = False
            overdue_km = 0
            overdue_days = 0

            if rule.km_threshold is not None:
                km_delta = current_mileage - last_km
                if km_delta >= rule.km_threshold:
                    overdue_km = km_delta - rule.km_threshold
                    message = f"Vencida por {overdue_km} km"
                    alerts.append(VehicleAlert(vehicle, service_type, message, priority=rule.priority, overdue_value=overdue_km, overdue_unit='km'))
                    km_alert_triggered = True

            if rule.days_threshold is not None and not km_alert_triggered:
                if isinstance(last_service_date, datetime):
                   last_service_date = last_service_date.date()

                days_delta = (today - last_service_date).days
                if days_delta >= rule.days_threshold:
                    overdue_days = days_delta - rule.days_threshold
                    message = f"Vencida por {overdue_days} dias"
                    alerts.append(VehicleAlert(vehicle, service_type, message, priority=rule.priority, overdue_value=overdue_days, overdue_unit='days'))

    alerts.sort(reverse=True)
    if limit:
        return alerts[:limit]
    return alerts


def calculate_route_details(start_location, end_location):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': settings.GOOGLE_MAPS_API_KEY,
        'X-Goog-FieldMask': 'routes.distanceMeters,routes.travelAdvisory.tollInfo'
    }
    body = {
        "origin": {"address": start_location},
        "destination": {"address": end_location},
        "travelMode": "DRIVE",
        "routeModifiers": {
            "vehicleInfo": {"emissionType": "DIESEL"},
            "avoidTolls": False
        },
        "extraComputations": ["TOLLS"],
        "computeAlternativeRoutes": False,
        "languageCode": "pt-BR",
        "units": "METRIC"
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
        if not data.get('routes'):
            error_details = data.get('error', {}).get('message', 'Nenhuma rota encontrada entre os locais.')
            return f"Erro ao calcular rota: {error_details}"
        route = data['routes'][0]
        distance_meters = route.get('distanceMeters', 0)
        distance_km = round(distance_meters / 1000, 2)
        toll_cost = 0.0
        toll_info = route.get('travelAdvisory', {}).get('tollInfo')
        if toll_info and toll_info.get('estimatedPrice'):
            for price_info in toll_info['estimatedPrice']:
                toll_cost += float(price_info.get('units', 0)) + float(price_info.get('nanos', 0)) / 1_000_000_000
        return {'distance': distance_km, 'toll_cost': round(toll_cost, 2)}
    except requests.exceptions.HTTPError as e:
        error_body = e.response.text
        if e.response.status_code == 403:
            return f"Erro na API do Google (403): Verifique se a 'Routes API' está habilitada, o faturamento está ativo e a chave API é válida. Detalhes: {error_body}"
        return f"Erro na API do Google (HTTP {e.response.status_code}): {error_body}"
    except requests.exceptions.RequestException as e:
        return f"Erro de conexão com a API do Google: {e}"
    except Exception as e:
        return f"Erro inesperado ao processar rota: {e}"


def get_diesel_price(uf):
    url = "https://combustivelapi.com.br/api/precos"
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            return f"API de Combustível retornou um erro: {data.get('message', 'Erro desconhecido')}"
        precos = data.get('precos')
        if not precos:
            return "Estrutura de resposta inesperada da API de Combustível (sem 'precos')."
        uf_lower = uf.lower()
        price_str = None
        if 'diesel' in precos and uf_lower in precos['diesel']:
            price_str = precos['diesel'][uf_lower]
        else:
            return f"Preço 'diesel' não encontrado para a UF: {uf.upper()} na resposta da API."
        return float(price_str.replace(',', '.'))
    except requests.exceptions.HTTPError as e:
        return f"Erro na API de Combustível (HTTP {e.response.status_code}). O servidor não aceitou a requisição."
    except requests.exceptions.RequestException as e:
        return f"Erro de conexão com a API de Combustível: {e}"
    except (ValueError, TypeError, KeyError) as e:
        return f"Erro ao processar a resposta JSON da API: {e}"


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        all_vehicles = list(Vehicle.objects.all())
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
            'total': Driver.objects.count(),
            'active': Driver.objects.filter(is_active=True).count(),
            'inactive': Driver.objects.filter(is_active=False).count(),
        }
        now = timezone.now()
        vehicle_alerts = get_vehicle_alerts(limit=5)
        upcoming_maintenances = Maintenance.objects.select_related('vehicle').filter(status='scheduled', start_date__gte=now).order_by('start_date')[:3]
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

class DriverListView(LoginRequiredMixin, View):
    def get(self, request):
        queryset = Driver.objects.all().order_by('full_name')
        search_query = request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(Q(full_name__icontains=search_query) | Q(email__icontains=search_query) | Q(license_number__icontains=search_query))
        status_filter = request.GET.get('status', '')
        if status_filter == 'active': queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive': queryset = queryset.filter(is_active=False)
        stats = {
            'total': Driver.objects.count(),
            'active': Driver.objects.filter(is_active=True).count(),
            'inactive': Driver.objects.filter(is_active=False).count()
        }
        context = {
            'drivers': queryset, 'add_form': DriverForm(), 'stats': stats,
            'search_query': search_query, 'status_filter': status_filter
        }
        return render(request, 'dashboard/drivers.html', context)

class VehicleListView(LoginRequiredMixin, View):
    def get(self, request):
        all_vehicles = list(Vehicle.objects.select_related('driver').order_by('plate'))
        stats = { 'total': len(all_vehicles), 'available': 0, 'on_route': 0, 'maintenance': 0, 'disabled': 0 }
        filtered_vehicles = []
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        for vehicle in all_vehicles:
            dynamic_slug = vehicle.dynamic_status_slug
            if dynamic_slug == 'available': stats['available'] += 1
            elif dynamic_slug == 'on_route': stats['on_route'] += 1
            elif dynamic_slug == 'maintenance': stats['maintenance'] += 1
            elif dynamic_slug == 'disabled': stats['disabled'] += 1
            passes_status_filter = not status_filter or dynamic_slug == status_filter
            passes_search_filter = True
            if search_query:
                search_query_lower = search_query.lower()
                in_plate = search_query_lower in vehicle.plate.lower()
                in_model = search_query_lower in vehicle.model.lower()
                in_driver = (vehicle.driver and search_query_lower in vehicle.driver.full_name.lower())
                passes_search_filter = in_plate or in_model or in_driver
            if passes_status_filter and passes_search_filter:
                filtered_vehicles.append(vehicle)
        context = {
            'vehicles': filtered_vehicles, 'add_form': VehicleForm(),
            'status_choices': Vehicle.STATUS_CHOICES, 'search_query': search_query,
            'status_filter': status_filter, 'stats': stats
        }
        return render(request, 'dashboard/vehicles.html', context)

class VehicleCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo adicionado com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    label = form.fields.get(field).label if field != '__all__' else ''
                    message = f"{label}: {error}" if label else str(error)
                    messages.error(request, message)
        return redirect('vehicle-list')

class VehicleUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo atualizado com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    label = form.fields.get(field).label if field != '__all__' else ''
                    message = f"{label}: {error}" if label else str(error)
                    messages.error(request, message)
        return redirect('vehicle-list')

class VehicleDeactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle.status = 'disabled'
        vehicle.save()
        messages.success(request, f'Veículo {vehicle.plate} desativado com sucesso.')
        return redirect('vehicle-list')

class VehicleReactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle.status = 'available'
        vehicle.save()
        messages.success(request, f'Veículo {vehicle.plate} reativado com sucesso.')
        return redirect('vehicle-list')

class DriverCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista adicionado com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    label = form.fields.get(field).label if field != '__all__' else ''
                    message = f"{label}: {error}" if label else str(error)
                    messages.error(request, message)
        return redirect('driver-list')

class DriverUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista atualizado com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    label = form.fields.get(field).label if field != '__all__' else ''
                    message = f"{label}: {error}" if label else str(error)
                    messages.error(request, message)
        return redirect('driver-list')

class DriverDeactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        driver.is_active = False
        driver.demission_date = date.today()
        driver.save()
        messages.success(request, f'Motorista {driver.full_name} desativado com sucesso.')
        return redirect('driver-list')

class MaintenanceCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Manutenção agendada com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    label = form.fields.get(field).label if field != '__all__' else ''
                    message = f"{label}: {error}" if label else str(error)
                    messages.error(request, message)
        return redirect('maintenance-list')

class MaintenanceUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        maintenance = get_object_or_404(Maintenance, pk=pk)
        form = MaintenanceForm(request.POST, instance=maintenance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Manutenção atualizada com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    label = form.fields.get(field).label if field != '__all__' else ''
                    message = f"{label}: {error}" if label else str(error)
                    messages.error(request, message)
        return redirect('maintenance-list')

class MaintenanceCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        maintenance = get_object_or_404(Maintenance, pk=pk)
        maintenance.status = 'canceled'
        maintenance.save()
        messages.warning(request, f'Manutenção para o veículo {maintenance.vehicle.plate} foi cancelada.')
        return redirect('maintenance-list')

class MaintenanceCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        maintenance = get_object_or_404(Maintenance, pk=pk)
        form = MaintenanceCompletionForm(request.POST, instance=maintenance)
        if form.is_valid():
            updated_maintenance = form.save(commit=False)
            if updated_maintenance.estimated_cost is not None and updated_maintenance.actual_cost is not None and updated_maintenance.estimated_cost != updated_maintenance.actual_cost:
                messages.warning(request, f"Atenção: O custo final (R$ {updated_maintenance.actual_cost}) é diferente do estimado (R$ {updated_maintenance.estimated_cost}).")
            updated_maintenance.status = 'completed'
            updated_maintenance.save()
            messages.success(request, 'Manutenção concluída com sucesso!')
        else:
            messages.error(request, "Erro ao preencher o formulário de conclusão.")
        return redirect('maintenance-list')

class MaintenanceListView(LoginRequiredMixin, View):
    def get(self, request):
        queryset = Maintenance.objects.select_related('vehicle').order_by('-start_date')
        search_query = request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(Q(vehicle__plate__icontains=search_query) | Q(service_type__icontains=search_query) | Q(mechanic_shop_name__icontains=search_query))
        status_filter = request.GET.get('status', '')
        now = timezone.now()
        if status_filter == 'scheduled': queryset = queryset.filter(status__in=['scheduled', 'in_progress'], start_date__gt=now)
        elif status_filter == 'in_progress': queryset = queryset.filter(status__in=['scheduled', 'in_progress'], start_date__lte=now, end_date__gte=now)
        elif status_filter == 'overdue': queryset = queryset.filter(status__in=['scheduled', 'in_progress'], end_date__lt=now)
        elif status_filter == 'completed': queryset = queryset.filter(status='completed')
        elif status_filter == 'canceled': queryset = queryset.filter(status='canceled')
        stats = {
            'total': Maintenance.objects.count(),
            'scheduled': Maintenance.objects.filter(status__in=['scheduled', 'in_progress'], start_date__gt=now).count(),
            'in_progress': Maintenance.objects.filter(status__in=['scheduled', 'in_progress'], start_date__lte=now, end_date__gte=now).count(),
            'completed': Maintenance.objects.filter(status='completed').count(),
        }
        status_choices_for_filter = list(Maintenance.STATUS_CHOICES)
        status_choices_for_filter.append(('overdue', 'Atrasada'))
        all_active_vehicles = Vehicle.objects.exclude(status='disabled').order_by('plate')
        context = {
            'maintenances': queryset, 'add_form': MaintenanceForm(),
            'completion_form': MaintenanceCompletionForm(), 'stats': stats,
            'search_query': search_query, 'status_choices': status_choices_for_filter,
            'status_filter': status_filter, 'all_active_vehicles': all_active_vehicles,
        }
        return render(request, 'dashboard/maintenance.html', context)


class RouteCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save(commit=False)
            route_details = calculate_route_details(route.start_location, route.end_location)
            if isinstance(route_details, str):
                return JsonResponse({'success': False, 'errors': {'__all__': [route_details]}}, status=400)
            try:
                uf = re.split(r',\s*', route.start_location)[-1].strip().upper()
                if not (len(uf) == 2 and uf.isalpha()):
                     raise ValueError("Formato de UF inválido.")
            except Exception:
                return JsonResponse({'success': False, 'errors': {'__all__': ["Formato de Local de Partida inválido. Use 'Cidade, UF'."]}}, status=400)
            price_result = get_diesel_price(uf)
            if isinstance(price_result, str):
                return JsonResponse({'success': False, 'errors': {'__all__': [price_result]}}, status=400)
            route.estimated_distance = route_details['distance']
            route.estimated_toll_cost = route_details['toll_cost']
            route.fuel_price_per_liter = price_result
            route.save()
            route.refresh_from_db()
            messages.success(request, 'Rota registrada com sucesso!')
            return JsonResponse({
                'success': True,
                'summary': {
                    'start_location': route.start_location, 'end_location': route.end_location,
                    'distance': route.estimated_distance, 'toll_cost': route.estimated_toll_cost,
                    'fuel_cost': route.estimated_fuel_cost or 0.0
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

class RouteListView(LoginRequiredMixin, View):
    def get(self, request):
        all_routes = list(Route.objects.select_related('driver', 'vehicle').order_by('-start_time'))
        search_query = request.GET.get('search', '')
        if search_query:
            all_routes = [route for route in all_routes if search_query.lower() in route.start_location.lower() or search_query.lower() in route.end_location.lower() or (route.driver and search_query.lower() in route.driver.full_name.lower()) or (route.vehicle and search_query.lower() in route.vehicle.plate.lower())]
        stats = {'total': Route.objects.count(), 'active': 0, 'planned': 0, 'completed': 0, 'cancelled': 0}
        for r in Route.objects.all():
            status_slug = r.dynamic_status_slug
            if status_slug == 'in_progress': stats['active'] += 1
            elif status_slug == 'scheduled': stats['planned'] += 1
            elif status_slug == 'completed': stats['completed'] += 1
            elif status_slug == 'canceled': stats['cancelled'] += 1
        status_filter = request.GET.get('status', '')
        if status_filter:
            filtered_routes = [route for route in all_routes if route.dynamic_status_slug == status_filter]
        else:
            filtered_routes = all_routes
        context = {
            'routes': filtered_routes, 'stats': stats,
            'status_choices': Route.STATUS_CHOICES, 'search_query': search_query,
            'status_filter': status_filter, 'add_form': RouteForm(),
            'completion_form': RouteCompletionForm()
        }
        return render(request, 'dashboard/routes.html', context)

class RouteUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        route = get_object_or_404(Route, pk=pk)
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            updated_route = form.save(commit=False)
            route_details = calculate_route_details(updated_route.start_location, updated_route.end_location)
            if isinstance(route_details, str):
                return JsonResponse({'success': False, 'errors': {'__all__': [route_details]}}, status=400)
            try:
                uf = re.split(r',\s*', updated_route.start_location)[-1].strip().upper()
                if not (len(uf) == 2 and uf.isalpha()):
                     raise ValueError("Formato de UF inválido.")
            except Exception:
                return JsonResponse({'success': False, 'errors': {'__all__': ["Formato de Local de Partida inválido. Use 'Cidade, UF'."]}}, status=400)
            price_result = get_diesel_price(uf)
            if isinstance(price_result, str):
                return JsonResponse({'success': False, 'errors': {'__all__': [price_result]}}, status=400)
            updated_route.estimated_distance = route_details['distance']
            updated_route.estimated_toll_cost = route_details['toll_cost']
            updated_route.fuel_price_per_liter = price_result
            updated_route.save()
            updated_route.refresh_from_db()
            messages.success(request, 'Rota atualizada com sucesso!')
            return JsonResponse({
                'success': True,
                'summary': {
                    'start_location': updated_route.start_location, 'end_location': updated_route.end_location,
                    'distance': updated_route.estimated_distance, 'toll_cost': updated_route.estimated_toll_cost,
                    'fuel_cost': updated_route.estimated_fuel_cost or 0.0
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

class RouteCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        route = get_object_or_404(Route, pk=pk)
        route.status = 'canceled'
        route.save()
        messages.success(request, f'Rota de {route.start_location} para {route.end_location} cancelada.')
        return redirect('route-list')

class RouteReactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        route = get_object_or_404(Route, pk=pk)
        route.status = 'scheduled'
        route.save()
        messages.success(request, 'Rota reativada com sucesso.')
        return redirect('route-list')


class RouteCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        route = get_object_or_404(Route, pk=pk)
        form = RouteCompletionForm(request.POST, instance=route)
        if form.is_valid():
            completed_route = form.save(commit=False)
            completed_route.status = 'completed'
            if not completed_route.actual_distance or completed_route.actual_distance <= 0:
                completed_route.actual_distance = route.estimated_distance
            completed_route.save()
            messages.success(request, f'Rota de {route.start_location} para {route.end_location} concluída. A quilometragem do veículo foi atualizada.')
        else:
            messages.error(request, 'Erro ao concluir a rota. Verifique o valor da distância.')
        return redirect('route-list')

class VehicleMaintenanceHistoryView(LoginRequiredMixin, View):
    def get(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        maintenances = Maintenance.objects.filter(vehicle=vehicle, status='completed').order_by('-actual_end_date')
        total_cost_agg = maintenances.aggregate(total=Sum('actual_cost'))
        total_cost = float(total_cost_agg['total'] or 0.0)
        history_list = []
        for m in maintenances:
            history_list.append({
                'service_type': m.service_type, 'shop_name': m.mechanic_shop_name,
                'end_date': m.actual_end_date.strftime('%d/%m/%Y') if m.actual_end_date else 'N/A',
                'cost': float(m.actual_cost or 0.0),
            })
        return JsonResponse({ 'history': history_list, 'total_cost': total_cost })

class VehicleRouteHistoryView(LoginRequiredMixin, View):
    def get(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        routes = Route.objects.filter(vehicle=vehicle, status='completed').select_related('vehicle').order_by('-end_time')
        stats = routes.aggregate(
            total_distance=Sum(Coalesce('actual_distance', 'estimated_distance')),
            total_routes=Count('id'), total_toll=Sum('estimated_toll_cost')
        )
        total_distance = float(stats['total_distance'] or 0.0)
        total_routes = stats['total_routes'] or 0
        total_toll_cost = float(stats['total_toll'] or 0.0)
        total_fuel_cost = 0.0
        history_list = []
        for r in routes:
            route_fuel_cost = float(r.estimated_fuel_cost or 0.0)
            total_fuel_cost += route_fuel_cost
            route_toll_cost = float(r.estimated_toll_cost or 0.0)
            history_list.append({
                'start_location': r.start_location, 'end_location': r.end_location,
                'end_time': r.end_time.strftime('%d/%m/%Y %H:%M'),
                'distance': float(r.actual_distance or r.estimated_distance or 0.0),
                'fuel_cost': route_fuel_cost, 'toll_cost': route_toll_cost,
            })
        return JsonResponse({
            'history': history_list,
            'stats': {
                'total_distance': total_distance, 'total_routes': total_routes,
                'total_fuel_cost': total_fuel_cost, 'total_toll_cost': total_toll_cost,
            }
        })

class DriverRouteHistoryView(LoginRequiredMixin, View):
    def get(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        routes = Route.objects.filter(driver=driver, status='completed').select_related('vehicle').order_by('-end_time')
        stats = routes.aggregate(
            total_distance=Sum(Coalesce('actual_distance', 'estimated_distance')),
            total_routes=Count('id'), total_toll=Sum('estimated_toll_cost')
        )
        total_distance = float(stats['total_distance'] or 0.0)
        total_routes = stats['total_routes'] or 0
        total_toll_cost = float(stats['total_toll'] or 0.0)
        total_fuel_cost = 0.0
        history_list = []
        for r in routes:
            route_fuel_cost = float(r.estimated_fuel_cost or 0.0)
            total_fuel_cost += route_fuel_cost
            route_toll_cost = float(r.estimated_toll_cost or 0.0)
            history_list.append({
                'start_location': r.start_location, 'end_location': r.end_location,
                'end_time': r.end_time.strftime('%d/%m/%Y %H:%M'),
                'distance': float(r.actual_distance or r.estimated_distance or 0.0),
                'fuel_cost': route_fuel_cost, 'toll_cost': route_toll_cost,
                'vehicle_plate': r.vehicle.plate if r.vehicle else 'N/A',
            })
        return JsonResponse({
            'history': history_list,
            'stats': {
                'total_distance': total_distance, 'total_routes': total_routes,
                'total_fuel_cost': total_fuel_cost, 'total_toll_cost': total_toll_cost,
            }
        })

class AlertConfigView(LoginRequiredMixin, View):
    def get(self, request):
        for choice_val, choice_disp in Maintenance.SERVICE_CHOICES_ALERT_CONFIG:
            AlertConfiguration.objects.get_or_create(
                service_type=choice_val,
                defaults={'priority': 'medium'}
                )

        queryset = AlertConfiguration.objects.all().order_by('service_type')
        formset = AlertConfigurationFormSet(queryset=queryset)

        all_alerts = get_vehicle_alerts()


        total_alerts = len(all_alerts)
        priority_counts = Counter(alert.priority for alert in all_alerts)
        stats = {
            'total': total_alerts,
            'high': priority_counts.get('high', 0),
            'medium': priority_counts.get('medium', 0),
            'low': priority_counts.get('low', 0),
        }

        search_query = request.GET.get('search', '')
        priority_filter = request.GET.get('priority', '')

        filtered_alerts = all_alerts
        if search_query:
            search_query_lower = search_query.lower()
            filtered_alerts = [
                alert for alert in filtered_alerts
                if search_query_lower in alert.vehicle.plate.lower() or \
                   search_query_lower in alert.vehicle.model.lower() or \
                   search_query_lower in alert.service_type.lower()
            ]
        if priority_filter:
            filtered_alerts = [
                alert for alert in filtered_alerts
                if alert.priority == priority_filter
            ]

        priority_choices = AlertConfiguration.PRIORITY_CHOICES

        context = {
            'formset': formset,
            'alerts': filtered_alerts,
            'search_query': search_query,
            'priority_filter': priority_filter,
            'priority_choices': priority_choices,
            'stats': stats,
            }
        return render(request, 'dashboard/alert_config.html', context)

    def post(self, request):
        formset = AlertConfigurationFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Configurações de alerta salvas com sucesso!')
            return redirect('alert-config')
        else:
            all_alerts = get_vehicle_alerts()

            total_alerts = len(all_alerts)
            priority_counts = Counter(alert.priority for alert in all_alerts)
            stats = {
                'total': total_alerts,
                'high': priority_counts.get('high', 0),
                'medium': priority_counts.get('medium', 0),
                'low': priority_counts.get('low', 0),
            }

            search_query = request.GET.get('search', '')
            priority_filter = request.GET.get('priority', '')

            filtered_alerts = all_alerts
            if search_query:
                search_query_lower = search_query.lower()
                filtered_alerts = [
                    alert for alert in filtered_alerts
                    if search_query_lower in alert.vehicle.plate.lower() or \
                       search_query_lower in alert.vehicle.model.lower() or \
                       search_query_lower in alert.service_type.lower()
                ]
            if priority_filter:
                filtered_alerts = [
                    alert for alert in filtered_alerts
                    if alert.priority == priority_filter
                ]

            priority_choices = AlertConfiguration.PRIORITY_CHOICES

            messages.error(request, 'Erro ao salvar as configurações. Verifique os campos.')
            context = {
                'formset': formset,
                'alerts': filtered_alerts,
                'search_query': search_query,
                'priority_filter': priority_filter,
                'priority_choices': priority_choices,
                'stats': stats,
                }
            return render(request, 'dashboard/alert_config.html', context)