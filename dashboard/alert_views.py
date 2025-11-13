from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from collections import Counter
from .models import Maintenance, AlertConfiguration
from accounts.models import UserProfile
from .forms import AlertConfigurationFormSet
from .services import get_vehicle_alerts


class AlertConfigView(LoginRequiredMixin, View):
    def get(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        
        for choice_val, choice_disp in Maintenance.SERVICE_CHOICES_ALERT_CONFIG:
            AlertConfiguration.objects.get_or_create(
                user_profile=profile,
                service_type=choice_val,
                defaults={'priority': 'medium'}
                )

        queryset = AlertConfiguration.objects.filter(user_profile=profile).all().order_by('service_type')
        formset = AlertConfigurationFormSet(queryset=queryset)
        
        all_alerts = get_vehicle_alerts(profile)

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
        profile = get_object_or_404(UserProfile, user=request.user)
        queryset = AlertConfiguration.objects.filter(user_profile=profile)
        formset = AlertConfigurationFormSet(request.POST, queryset=queryset)
        
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Configurações de alerta salvas com sucesso!')
            return redirect('alert-config')
        else:
            all_alerts = get_vehicle_alerts(profile)

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