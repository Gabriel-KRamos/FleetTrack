from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from datetime import date
from django.utils import timezone
from .models import Vehicle, Driver, Maintenance, Route
from .forms import VehicleForm, DriverForm, MaintenanceForm, RouteForm, MaintenanceCompletionForm
from django.db.models import Q
from django.utils.text import slugify

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        now = timezone.now()
        vehicles_in_use_pks = Route.objects.filter(start_time__lte=now, end_time__gte=now).exclude(status='canceled').values_list('vehicle_id', flat=True)
        vehicles_in_maintenance_pks = Maintenance.objects.filter(start_date__lte=now, end_date__gte=now).values_list('vehicle_id', flat=True)
        vehicle_overview = {
            'total': Vehicle.objects.count(),
            'in_use': len(set(vehicles_in_use_pks)),
            'maintenance': len(set(vehicles_in_maintenance_pks)),
            'unavailable': Vehicle.objects.filter(status='disabled').count()
        }
        vehicle_overview['available'] = vehicle_overview['total'] - vehicle_overview['in_use'] - vehicle_overview['maintenance'] - vehicle_overview['unavailable']
        driver_overview = {
            'total': Driver.objects.count(),
            'active': Driver.objects.filter(is_active=True).count(),
            'inactive': Driver.objects.filter(is_active=False).count(),
        }
        recent_maintenances = Maintenance.objects.select_related('vehicle').order_by('-end_date')[:2]
        recent_routes = Route.objects.select_related('vehicle').filter(status='completed').order_by('-end_time')[:2]
        upcoming_maintenances = Maintenance.objects.select_related('vehicle').filter(status='scheduled', start_date__gte=now).order_by('start_date')[:3]
        context = {
            'vehicle_overview': vehicle_overview,
            'driver_overview': driver_overview,
            'recent_maintenances': recent_maintenances,
            'recent_routes': recent_routes,
            'upcoming_maintenances': upcoming_maintenances,
        }
        return render(request, 'dashboard/dashboard.html', context)

class DriverListView(LoginRequiredMixin, View):
    def get(self, request):
        queryset = Driver.objects.all().order_by('full_name')
        search_query = request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(Q(full_name__icontains=search_query) | Q(email__icontains=search_query) | Q(license_number__icontains=search_query))
        status_filter = request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        stats = {'total': Driver.objects.count(), 'active': Driver.objects.filter(is_active=True).count(), 'inactive': Driver.objects.filter(is_active=False).count(), 'suspended': Driver.objects.filter(is_active=False).count()}
        context = {'drivers': queryset, 'add_form': DriverForm(), 'stats': stats, 'search_query': search_query, 'status_filter': status_filter}
        return render(request, 'dashboard/drivers.html', context)

class VehicleListView(LoginRequiredMixin, View):
    def get(self, request):
        queryset = Vehicle.objects.select_related('driver').order_by('plate')
        search_query = request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(Q(plate__icontains=search_query) | Q(model__icontains=search_query) | Q(driver__full_name__icontains=search_query))
        status_filter = request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        stats = {'total': Vehicle.objects.count(), 'available': Vehicle.objects.filter(status='available').count(), 'on_route': Vehicle.objects.filter(status='on_route').count(), 'maintenance': Vehicle.objects.filter(status='maintenance').count(), 'disabled': Vehicle.objects.filter(status='disabled').count()}
        context = {'vehicles': queryset, 'add_form': VehicleForm(), 'status_choices': Vehicle.STATUS_CHOICES, 'search_query': search_query, 'status_filter': status_filter, 'stats': stats}
        return render(request, 'dashboard/vehicles.html', context)

class VehicleCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo adicionado com sucesso!')
        else:
            for field, errors in form.errors.items(): messages.error(request, f"{form.fields[field].label}: {', '.join(errors)}")
        return redirect('vehicle-list')

class VehicleUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo atualizado com sucesso!')
        else:
            for field, errors in form.errors.items(): messages.error(request, f"{vehicle.plate} - {form.fields[field].label}: {', '.join(errors)}")
        return redirect('vehicle-list')

class VehicleDeactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle.status = 'disabled'
        vehicle.save()
        messages.success(request, f'Veículo {vehicle.plate} desativado com sucesso.')
        return redirect('vehicle-list')

class DriverCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista adicionado com sucesso!')
        else:
            for field, errors in form.errors.items(): messages.error(request, f"Erro ao adicionar motorista: {', '.join(errors)}")
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
            for field, errors in form.errors.items(): error_text += f"{field}: {', '.join(errors)} "
            messages.error(request, f"Erro no agendamento: {error_text}")
        return redirect('maintenance-list')

class MaintenanceUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        maintenance = get_object_or_404(Maintenance, pk=pk)
        form = MaintenanceForm(request.POST, instance=maintenance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Manutenção atualizada com sucesso!')
        else:
            error_text = ""
            for field, errors in form.errors.items(): error_text += f"{field}: {', '.join(errors)} "
            messages.error(request, f"Erro ao atualizar: {error_text}")
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
            if updated_maintenance.estimated_cost != updated_maintenance.actual_cost:
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
        if status_filter == 'overdue':
            queryset = queryset.filter(end_date__lt=timezone.now()).exclude(status__in=['completed', 'canceled'])
        elif status_filter:
            queryset = queryset.filter(status=status_filter)

        stats = {
            'total': Maintenance.objects.count(),
            'scheduled': Maintenance.objects.filter(status='scheduled', end_date__gte=timezone.now()).count(),
            'in_progress': Maintenance.objects.filter(status='in_progress').count(),
            'completed': Maintenance.objects.filter(status='completed').count(),
        }
        
        status_choices_for_filter = list(Maintenance.STATUS_CHOICES)
        status_choices_for_filter.append(('overdue', 'Atrasada'))

        context = {
            'maintenances': queryset,
            'add_form': MaintenanceForm(),
            'completion_form': MaintenanceCompletionForm(),
            'stats': stats,
            'search_query': search_query,
            'status_choices': status_choices_for_filter,
            'status_filter': status_filter,
        }
        return render(request, 'dashboard/maintenance.html', context)

class RouteCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = RouteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rota registrada com sucesso!')
        else:
            error_text = ""
            for field, errors in form.errors.items(): error_text += f"{field}: {', '.join(errors)} "
            messages.error(request, f"Erro ao registrar rota: {error_text}")
        return redirect('route-list')

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
        context = {'routes': filtered_routes, 'stats': stats, 'status_choices': Route.STATUS_CHOICES, 'search_query': search_query, 'status_filter': status_filter, 'add_form': RouteForm()}
        return render(request, 'dashboard/routes.html', context)

class RouteUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        route = get_object_or_404(Route, pk=pk)
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rota atualizada com sucesso!')
        else:
            error_text = ""
            for field, errors in form.errors.items(): error_text += f"{field}: {', '.join(errors)} "
            messages.error(request, f"Erro ao atualizar rota: {error_text}")
        return redirect('route-list')

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