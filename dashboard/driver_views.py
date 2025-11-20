from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from datetime import date
from django.db.models import Q, Sum, Count
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from .models import Driver, Route
from accounts.models import UserProfile
from .forms import DriverForm

class DriverBaseView(LoginRequiredMixin, View):
    def handle_form_errors(self, request, form):
        for field, errors in form.errors.items():
            for error in errors:
                label = form.fields.get(field).label if field != '__all__' else ''
                message = f"{label}: {error}" if label else str(error)
                messages.error(request, message)

class DriverListView(DriverBaseView):
    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        
        queryset = Driver.objects.filter(user_profile=profile).order_by('full_name')
        search_query = request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(Q(full_name__icontains=search_query) | Q(email__icontains=search_query) | Q(license_number__icontains=search_query))
        
        status_filter = request.GET.get('status', '')
        if status_filter == 'active': queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive': queryset = queryset.filter(is_active=False)
        
        stats = {
            'total': Driver.objects.filter(user_profile=profile).count(),
            'active': Driver.objects.filter(user_profile=profile, is_active=True).count(),
            'inactive': Driver.objects.filter(user_profile=profile, is_active=False).count()
        }
        
        context = {
            'drivers': queryset, 'add_form': DriverForm(), 'stats': stats,
            'search_query': search_query, 'status_filter': status_filter
        }
        return render(request, 'dashboard/drivers.html', context)

class DriverCreateView(DriverBaseView):
    def post(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        form = DriverForm(request.POST)
        if form.is_valid():
            new_driver = form.save(commit=False)
            new_driver.user_profile = profile
            new_driver.save()
            messages.success(request, 'Motorista adicionado com sucesso!')
        else:
            self.handle_form_errors(request, form)
        return redirect('driver-list')

class DriverUpdateView(DriverBaseView):
    def post(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        driver = get_object_or_404(Driver, pk=pk, user_profile=profile)
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista atualizado com sucesso!')
        else:
            self.handle_form_errors(request, form)
        return redirect('driver-list')

class DriverDeactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        driver = get_object_or_404(Driver, pk=pk, user_profile=profile)
        driver.is_active = False
        driver.demission_date = date.today()
        driver.save()
        messages.success(request, f'Motorista {driver.full_name} desativado com sucesso.')
        return redirect('driver-list')

class DriverRouteHistoryView(LoginRequiredMixin, View):
    def get(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        driver = get_object_or_404(Driver, pk=pk, user_profile=profile)
        
        routes = Route.objects.filter(driver=driver, status='completed').select_related('vehicle').order_by('-end_time')
        stats = routes.aggregate(
            total_distance=Sum(Coalesce('actual_distance', 'estimated_distance')),
            total_routes=Count('id'), total_toll=Sum('estimated_toll_cost')
        )
        
        total_distance = float(stats['total_distance'] or 0.0)
        total_routes = stats['total_routes'] or 0
        total_toll_cost = float(stats['total_toll'] or 0.0)
        
        history_list = []
        total_fuel_cost = 0.0
        
        for r in routes:
            route_fuel = float(r.estimated_fuel_cost or 0.0)
            total_fuel_cost += route_fuel
            
            history_list.append({
                'start_location': r.start_location, 
                'end_location': r.end_location,
                'end_time': r.end_time.strftime('%d/%m/%Y %H:%M'),
                'distance': float(r.actual_distance or r.estimated_distance or 0.0),
                'fuel_cost': route_fuel, 
                'toll_cost': float(r.estimated_toll_cost or 0.0),
                'vehicle_plate': r.vehicle.plate if r.vehicle else 'N/A',
            })
            
        return JsonResponse({
            'history': history_list,
            'stats': {
                'total_distance': total_distance, 'total_routes': total_routes,
                'total_fuel_cost': total_fuel_cost, 'total_toll_cost': total_toll_cost,
            }
        })