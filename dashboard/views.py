from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from datetime import date
from .models import Vehicle, Driver, Maintenance, Route
from .forms import VehicleForm, DriverForm, MaintenanceForm, RouteForm
import random

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        now = timezone.now()

        # --- LÓGICA DO GRÁFICO ---
        total_vehicles = Vehicle.objects.exclude(status='disabled').count()

        vehicles_in_maintenance_ids = Maintenance.objects.filter(
            start_date__lte=now, 
            end_date__gte=now
        ).values_list('vehicle_id', flat=True).distinct()
        
        vehicles_on_route_ids = Route.objects.filter(
            start_time__lte=now, 
            end_time__gte=now
        ).exclude(
            vehicle_id__in=vehicles_in_maintenance_ids
        ).values_list('vehicle_id', flat=True).distinct()

        on_route_count = vehicles_on_route_ids.count()
        in_maintenance_count = vehicles_in_maintenance_ids.count()
        
        # Calcula a contagem de veículos disponíveis
        available_count = total_vehicles - on_route_count - in_maintenance_count

        # --- FIM DA LÓGICA DO GRÁFICO ---

        active_routes = Route.objects.filter(
            start_time__lte=now, 
            end_time__gte=now
        ).select_related('vehicle', 'driver')

        active_routes_with_coords = []
        for route in active_routes:
            route.lat = -23.5505 + random.uniform(-0.1, 0.1)
            route.lng = -46.6333 + random.uniform(-0.1, 0.1)
            active_routes_with_coords.append(route)
            
        current_maintenances = Maintenance.objects.filter(
            start_date__lte=now, 
            end_date__gte=now
        ).select_related('vehicle').order_by('-start_date')[:5]

        upcoming_maintenances = Maintenance.objects.filter(
            start_date__gt=now
        ).select_related('vehicle').order_by('start_date')[:5]

        context = {
            'maintenance_form': MaintenanceForm(),
            'route_form': RouteForm(),
            'total_vehicles': total_vehicles,
            'vehicles_on_route': on_route_count,
            'vehicles_in_maintenance': in_maintenance_count,
            'active_routes': active_routes_with_coords,
            'current_maintenances': current_maintenances,
            'upcoming_maintenances': upcoming_maintenances,
            # Novos dados para o gráfico
            'chart_available': available_count,
            'chart_on_route': on_route_count,
            'chart_in_maintenance': in_maintenance_count,
        }
        return render(request, 'dashboard/dashboard.html', context)

# ... O restante das views (VehicleListView, etc.) permanece o mesmo ...
class VehicleListView(LoginRequiredMixin, View):
    def get(self, request):
        vehicles = Vehicle.objects.prefetch_related('maintenance_set', 'route_set').all().order_by('status', '-year')
        
        context = {
            'vehicles': vehicles,
            'add_form': VehicleForm(),
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
                    messages.error(request, f"{form.fields[field].label}: {error}")
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
                    messages.error(request, f"{vehicle.plate} - {form.fields[field].label}: {error}")
        return redirect('vehicle-list')

class VehicleDeactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle.status = 'disabled'
        vehicle.save()
        messages.success(request, f'Veículo {vehicle.plate} desativado com sucesso.')
        return redirect('vehicle-list')

class DriverListView(LoginRequiredMixin, View):
    def get(self, request):
        drivers = Driver.objects.all().order_by('-is_active', 'full_name')
        context = {
            'drivers': drivers,
            'add_form': DriverForm(),
        }
        return render(request, 'dashboard/drivers.html', context)

class DriverCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista adicionado com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro ao adicionar motorista: {error}")
        return redirect('driver-list')

class DriverUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista atualizado com sucesso!')
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
            error_text = ""
            for field, errors in form.errors.items():
                error_text += f"{field}: {', '.join(errors)} "
            messages.error(request, f"Erro no agendamento: {error_text}")
        return redirect('dashboard')

class RouteCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = RouteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rota registrada com sucesso!')
        else:
            error_text = ""
            for field, errors in form.errors.items():
                error_text += f"{field}: {', '.join(errors)} "
            messages.error(request, f"Erro ao registrar rota: {error_text}")
        return redirect('dashboard')