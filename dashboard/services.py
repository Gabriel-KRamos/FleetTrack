from django.shortcuts import get_object_or_404
from datetime import date, datetime
from django.utils import timezone
from .models import Vehicle, Maintenance, AlertConfiguration
from accounts.models import UserProfile
from django.conf import settings
from typing import Optional, List, Dict, Any, Union

import requests
import re
from collections import Counter


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


def get_vehicle_alerts(user_profile: UserProfile, limit: Optional[int] = None) -> List[VehicleAlert]:
    alerts = []
    now = timezone.now()
    today = now.date()
    
    if not user_profile:
        return []

    active_vehicles = Vehicle.objects.filter(user_profile=user_profile).exclude(status='disabled')
    active_rules = AlertConfiguration.objects.filter(user_profile=user_profile, is_active=True)
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


def calculate_route_details(start_location: str, end_location: str) -> Union[Dict[str, float], str]:
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


def get_diesel_price(uf: str) -> Union[float, str]:
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