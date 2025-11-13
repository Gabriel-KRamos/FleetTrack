from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from .models import Route
from accounts.models import UserProfile
from .forms import RouteForm, RouteCompletionForm
from .services import calculate_route_details, get_diesel_price

import re


class RouteCreateView(LoginRequiredMixin, View):
    def post(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        form = RouteForm(request.POST, user_profile=profile)
        if form.is_valid():
            route = form.save(commit=False)
            route.user_profile = profile
            
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
        profile = get_object_or_404(UserProfile, user=request.user)
        
        all_routes = list(Route.objects.filter(user_profile=profile).select_related('driver', 'vehicle').order_by('-start_time'))
        search_query = request.GET.get('search', '')
        if search_query:
            all_routes = [route for route in all_routes if search_query.lower() in route.start_location.lower() or search_query.lower() in route.end_location.lower() or (route.driver and search_query.lower() in route.driver.full_name.lower()) or (route.vehicle and search_query.lower() in route.vehicle.plate.lower())]
        
        stats = {'total': Route.objects.filter(user_profile=profile).count(), 'active': 0, 'planned': 0, 'completed': 0, 'cancelled': 0}
        for r in Route.objects.filter(user_profile=profile):
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
            'status_filter': status_filter, 'add_form': RouteForm(user_profile=profile),
            'completion_form': RouteCompletionForm()
        }
        return render(request, 'dashboard/routes.html', context)

class RouteUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        route = get_object_or_404(Route, pk=pk, user_profile=profile)
        form = RouteForm(request.POST, instance=route, user_profile=profile)
        
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
        profile = get_object_or_404(UserProfile, user=request.user)
        route = get_object_or_404(Route, pk=pk, user_profile=profile)
        route.status = 'canceled'
        route.save()
        messages.success(request, f'Rota de {route.start_location} para {route.end_location} cancelada.')
        return redirect('route-list')

class RouteReactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        route = get_object_or_404(Route, pk=pk, user_profile=profile)
        route.status = 'scheduled'
        route.save()
        messages.success(request, 'Rota reativada com sucesso.')
        return redirect('route-list')


class RouteCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        route = get_object_or_404(Route, pk=pk, user_profile=profile)
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