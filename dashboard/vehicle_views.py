from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from .models import Vehicle, Maintenance, Route
from accounts.models import UserProfile
from .forms import VehicleForm


class VehicleListView(LoginRequiredMixin, View):
    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        
        all_vehicles = list(Vehicle.objects.filter(user_profile=profile).select_related('driver').order_by('plate'))
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
        profile = get_object_or_404(UserProfile, user=request.user)
        form = VehicleForm(request.POST)
        if form.is_valid():
            new_vehicle = form.save(commit=False)
            new_vehicle.user_profile = profile
            new_vehicle.save()
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
        profile = get_object_or_404(UserProfile, user=request.user)
        vehicle = get_object_or_404(Vehicle, pk=pk, user_profile=profile)
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
        profile = get_object_or_404(UserProfile, user=request.user)
        vehicle = get_object_or_404(Vehicle, pk=pk, user_profile=profile)
        vehicle.status = 'disabled'
        vehicle.save()
        messages.success(request, f'Veículo {vehicle.plate} desativado com sucesso.')
        return redirect('vehicle-list')

class VehicleReactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        vehicle = get_object_or_404(Vehicle, pk=pk, user_profile=profile)
        vehicle.status = 'available'
        vehicle.save()
        messages.success(request, f'Veículo {vehicle.plate} reativado com sucesso.')
        return redirect('vehicle-list')

class VehicleMaintenanceHistoryView(LoginRequiredMixin, View):
    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        vehicle = get_object_or_404(Vehicle, pk=pk, user_profile=profile)
        
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
        profile = get_object_or_404(UserProfile, user=request.user)
        vehicle = get_object_or_404(Vehicle, pk=pk, user_profile=profile)
        
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