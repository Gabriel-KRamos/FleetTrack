from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Maintenance, Vehicle
from accounts.models import UserProfile
from .forms import (
    MaintenanceForm, MaintenanceCompletionForm
)


class MaintenanceCreateView(LoginRequiredMixin, View):
    def post(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        form = MaintenanceForm(request.POST, user_profile=profile)
        if form.is_valid():
            new_maint = form.save(commit=False)
            new_maint.user_profile = profile
            new_maint.save()
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
        profile = get_object_or_404(UserProfile, user=request.user)
        maintenance = get_object_or_404(Maintenance, pk=pk, user_profile=profile)
        form = MaintenanceForm(request.POST, instance=maintenance, user_profile=profile)
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
        profile = get_object_or_404(UserProfile, user=request.user)
        maintenance = get_object_or_404(Maintenance, pk=pk, user_profile=profile)
        maintenance.status = 'canceled'
        maintenance.save()
        messages.warning(request, f'Manutenção para o veículo {maintenance.vehicle.plate} foi cancelada.')
        return redirect('maintenance-list')

class MaintenanceCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        profile = get_object_or_404(UserProfile, user=request.user)
        maintenance = get_object_or_404(Maintenance, pk=pk, user_profile=profile)
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
        profile = get_object_or_404(UserProfile, user=request.user)
        
        queryset = Maintenance.objects.filter(user_profile=profile).select_related('vehicle').order_by('-start_date')
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
            'total': Maintenance.objects.filter(user_profile=profile).count(),
            'scheduled': Maintenance.objects.filter(user_profile=profile, status__in=['scheduled', 'in_progress'], start_date__gt=now).count(),
            'in_progress': Maintenance.objects.filter(user_profile=profile, status__in=['scheduled', 'in_progress'], start_date__lte=now, end_date__gte=now).count(),
            'completed': Maintenance.objects.filter(user_profile=profile, status='completed').count(),
        }
        
        status_choices_for_filter = list(Maintenance.STATUS_CHOICES)
        status_choices_for_filter.append(('overdue', 'Atrasada'))
        
        all_active_vehicles = Vehicle.objects.filter(user_profile=profile).exclude(status='disabled').order_by('plate')
        
        context = {
            'maintenances': queryset, 'add_form': MaintenanceForm(user_profile=profile),
            'completion_form': MaintenanceCompletionForm(), 'stats': stats,
            'search_query': search_query, 'status_choices': status_choices_for_filter,
            'status_filter': status_filter, 'all_active_vehicles': all_active_vehicles,
        }
        return render(request, 'dashboard/maintenance.html', context)