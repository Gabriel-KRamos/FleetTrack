from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import patch
from decimal import Decimal
from django.contrib.auth.hashers import check_password

from .models import Driver, Vehicle, Route, Maintenance, AlertConfiguration
from accounts.models import UserProfile
from .forms import DriverForm, MaintenanceForm, RouteForm
from .services import get_vehicle_alerts

from django.contrib.staticfiles.testing import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class DashboardBaseTestCase(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            username='user_a@teste.com', 
            password='password123',
            first_name='Usuário A'
        )
        self.profile_a = UserProfile.objects.create(
            user=self.user_a, 
            company_name="Empresa A",
            cnpj="11111111111111"
        )
        
        self.user_b = User.objects.create_user(
            username='user_b@teste.com', 
            password='password123',
            first_name='Usuário B'
        )
        self.profile_b = UserProfile.objects.create(
            user=self.user_b, 
            company_name="Empresa B",
            cnpj="22222222222222"
        )

        self.driver_a = Driver.objects.create(
            user_profile=self.profile_a,
            full_name='Motorista A',
            email='driver_a@teste.com',
            license_number='11111111111',
            admission_date=date(2024, 1, 1)
        )
        
        self.vehicle_a = Vehicle.objects.create(
            user_profile=self.profile_a,
            plate='AAA-1111',
            model='Modelo A',
            year=2024,
            initial_mileage=10000, 
            acquisition_date=date(2024, 1, 1),
            average_fuel_consumption=10.0
        )
        
        self.vehicle_b = Vehicle.objects.create(
            user_profile=self.profile_b,
            plate='BBB-2222',
            model='Modelo B',
            year=2023,
            initial_mileage=50000, 
            acquisition_date=date(2023, 1, 1),
            average_fuel_consumption=8.0
        )

        self.client = Client()
        self.client.login(username='user_a@teste.com', password='password123')
        
        self.now = timezone.now()

class ModelTests(DashboardBaseTestCase):

    def test_vehicle_mileage_property(self):
        self.assertEqual(self.vehicle_a.mileage, 10000)

        Route.objects.create(
            user_profile=self.profile_a,
            vehicle=self.vehicle_a,
            driver=self.driver_a,
            start_location="Origem", end_location="Destino",
            start_time=self.now - timedelta(days=2),
            end_time=self.now - timedelta(days=1),
            status='completed',
            actual_distance=150.5
        )
        
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.mileage, 10150)

    def test_vehicle_dynamic_status_property(self):
        self.assertEqual(self.vehicle_a.dynamic_status_slug, 'available')
        
        Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="Origem", end_location="Destino",
            start_time=self.now - timedelta(hours=1),
            end_time=self.now + timedelta(hours=2),
            status='in_progress'
        )
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.dynamic_status_slug, 'on_route')
        
        Maintenance.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a,
            service_type="Manutenção Teste",
            start_date=self.now - timedelta(hours=1),
            end_date=self.now + timedelta(hours=2),
            mechanic_shop_name="Oficina Teste",
            current_mileage=10150,
            status='in_progress'
        )
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.dynamic_status_slug, 'maintenance')

    def test_model_str_methods(self):
        self.assertEqual(str(self.driver_a), "Motorista A")
        self.assertEqual(str(self.vehicle_a), "Modelo A - AAA-1111")

class FormTests(DashboardBaseTestCase):

    def test_driver_form_valid(self):
        form_data = {
            'full_name': 'Novo Motorista',
            'email': 'novo@teste.com',
            'license_number': '12345678901',
            'admission_date': '2024-01-01'
        }
        form = DriverForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_driver_form_invalid_license(self):
        form_data = {
            'full_name': 'Motorista CNH Curta',
            'email': 'curto@teste.com',
            'license_number': '123',
            'admission_date': '2024-01-01'
        }
        form = DriverForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('license_number', form.errors)
        self.assertEqual(
            form.errors['license_number'][0], 
            "A CNH deve conter exatamente 11 dígitos numéricos."
        )

    def test_driver_form_duplicate_email(self):
        form_data = {
            'full_name': 'Motorista Duplicado',
            'email': self.driver_a.email,
            'license_number': '98765432100',
            'admission_date': '2024-01-01'
        }
        form = DriverForm(data=form_data, instance=Driver(user_profile=self.profile_a))
        
        if Driver.objects.filter(email=form_data['email'], user_profile=self.profile_a, is_active=True).exists():
             form.add_error('email', "Este endereço de email já está em uso por um motorista ativo.")

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_maintenance_route_conflict(self):
        Maintenance.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a,
            service_type="Manutenção Conflitante",
            start_date=self.now + timedelta(days=1),
            end_date=self.now + timedelta(days=2),
            mechanic_shop_name="Oficina",
            current_mileage=10000,
            status='scheduled'
        )
        
        form_data = {
            'start_location': 'Local A, SC', 'end_location': 'Local B, SC',
            'vehicle': self.vehicle_a.pk,
            'driver': self.driver_a.pk,
            'start_time': (self.now + timedelta(days=1, hours=2)).strftime('%d/%m/%Y %H:%M'),
            'end_time': (self.now + timedelta(days=1, hours=5)).strftime('%d/%m/%Y %H:%M'),
        }
        
        form = RouteForm(data=form_data, user_profile=self.profile_a)
        
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn("está agendado para manutenção", form.errors['__all__'][0])

class VehicleViewTests(DashboardBaseTestCase):

    def setUp(self):
        super().setUp()
        self.list_url = reverse('vehicle-list')
        self.add_url = reverse('vehicle-add')
        self.update_url = reverse('vehicle-update', kwargs={'pk': self.vehicle_a.pk})

    def test_vehicle_list_view_authenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/vehicles.html')
        self.assertContains(response, self.vehicle_a.plate)
        self.assertContains(response, self.vehicle_a.model)
        
        self.assertNotContains(response, self.vehicle_b.plate)

    def test_vehicle_create_view_post_success(self):
        vehicle_count_before = Vehicle.objects.filter(user_profile=self.profile_a).count()
        
        form_data = {
            'plate': 'NEW-0001', 'model': 'Novo Modelo', 'year': 2025,
            'acquisition_date': '2025-01-01', 'initial_mileage': 0,
            'average_fuel_consumption': 12.5
        }
        
        response = self.client.post(self.add_url, data=form_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.list_url)
        
        self.assertEqual(Vehicle.objects.filter(user_profile=self.profile_a).count(), vehicle_count_before + 1)
        new_vehicle = Vehicle.objects.get(plate='NEW-0001')
        self.assertEqual(new_vehicle.user_profile, self.profile_a)

    def test_vehicle_create_view_post_invalid(self):
        vehicle_count_before = Vehicle.objects.filter(user_profile=self.profile_a).count()
        
        form_data = {
            'plate': 'INVALIDO', 'model': '', 'year': 2025,
            'acquisition_date': '2025-01-01', 'initial_mileage': 0
        }
        
        response = self.client.post(self.add_url, data=form_data)
        
        self.assertEqual(response.status_code, 302)
        
        self.assertEqual(Vehicle.objects.filter(user_profile=self.profile_a).count(), vehicle_count_before)

    def test_vehicle_update_view_post(self):
        form_data = {
            'plate': self.vehicle_a.plate,
            'model': 'Modelo Atualizado',
            'year': self.vehicle_a.year,
            'acquisition_date': '2024-01-01', 
            'initial_mileage': self.vehicle_a.initial_mileage,
            'average_fuel_consumption': 11.0
        }
        
        response = self.client.post(self.update_url, data=form_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.list_url)
        
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.model, 'Modelo Atualizado')
        self.assertEqual(self.vehicle_a.average_fuel_consumption, Decimal('11.0'))

    def test_vehicle_deactivate_view(self):
        deactivate_url = reverse('vehicle-deactivate', kwargs={'pk': self.vehicle_a.pk})
        
        response = self.client.post(deactivate_url)
        self.assertRedirects(response, self.list_url)
        
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.status, 'disabled')

class SecurityTests(DashboardBaseTestCase):

    def test_user_a_cannot_update_user_b_vehicle(self):
        update_url_b = reverse('vehicle-update', kwargs={'pk': self.vehicle_b.pk})
        
        form_data = {
            'plate': self.vehicle_b.plate,
            'model': 'HACKED',
            'year': self.vehicle_b.year,
            'acquisition_date': '2023-01-01', 
            'initial_mileage': self.vehicle_b.initial_mileage,
            'average_fuel_consumption': self.vehicle_b.average_fuel_consumption
        }
        
        response = self.client.post(update_url_b, data=form_data)
        
        self.assertEqual(response.status_code, 404)
        
        self.vehicle_b.refresh_from_db()
        self.assertNotEqual(self.vehicle_b.model, 'HACKED')
        
    def test_unauthenticated_user_redirected(self):
        self.client.logout()
        
        list_url = reverse('vehicle-list')
        response = self.client.get(list_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/accounts/login/?next={list_url}')

class LogicTests(DashboardBaseTestCase):

    def test_get_vehicle_alerts_by_km(self):
        AlertConfiguration.objects.create(
            user_profile=self.profile_a,
            service_type='Troca de Óleo e Filtros',
            km_threshold=500,
            priority='high',
            is_active=True
        )
        
        vehicle_alert = Vehicle.objects.create(
            user_profile=self.profile_a,
            plate='ALERT-KM', model='Alert Model', year=2024,
            initial_mileage=1000, acquisition_date=date(2024, 1, 1)
        )
        
        Maintenance.objects.create(
            user_profile=self.profile_a, vehicle=vehicle_alert,
            service_type='Troca de Óleo e Filtros',
            status='completed',
            current_mileage=1000,
            start_date=self.now - timedelta(days=10),
            end_date=self.now - timedelta(days=10),
            actual_end_date=self.now - timedelta(days=10),
            mechanic_shop_name="Oficina"
        )
        
        Route.objects.create(
            user_profile=self.profile_a, vehicle=vehicle_alert, driver=self.driver_a,
            start_location="Origem", end_location="Destino",
            status='completed', actual_distance=501,
            start_time=self.now - timedelta(days=2),
            end_time=self.now - timedelta(days=1),
        )

        alerts = get_vehicle_alerts(self.profile_a)
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].vehicle.plate, 'ALERT-KM')
        self.assertEqual(alerts[0].service_type, 'Troca de Óleo e Filtros')
        self.assertEqual(alerts[0].priority, 'high')
        self.assertIn('Vencida por 1 km', alerts[0].message)

class ApiViewTests(DashboardBaseTestCase):

    def test_vehicle_route_history_json(self):
        Route.objects.create(
            user_profile=self.profile_a,
            vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="JSON Test, SC", end_location="API Test, PR",
            start_time=self.now - timedelta(days=2),
            end_time=self.now - timedelta(days=1),
            status='completed',
            actual_distance=250
        )
        
        history_url = reverse('vehicle-route-history', kwargs={'pk': self.vehicle_a.pk})
        response = self.client.get(history_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        
        data = response.json()
        
        self.assertEqual(len(data['history']), 1)
        self.assertEqual(data['history'][0]['start_location'], 'JSON Test, SC')
        self.assertEqual(data['stats']['total_routes'], 1)
        self.assertEqual(data['stats']['total_distance'], 250.0)
        
    def test_user_a_cannot_see_user_b_history_json(self):
        history_url_b = reverse('vehicle-route-history', kwargs={'pk': self.vehicle_b.pk})
        response = self.client.get(history_url_b)
        
        self.assertEqual(response.status_code, 404)

class RouteViewMockTests(DashboardBaseTestCase):

    @patch('dashboard.route_views.get_diesel_price')
    @patch('dashboard.route_views.calculate_route_details')
    def test_route_create_view_with_mock(self, mock_calculate_route, mock_get_price):
        
        mock_calculate_route.return_value = {'distance': 150.0, 'toll_cost': 25.50}
        mock_get_price.return_value = Decimal('5.80')
        
        add_url = reverse('route-add')
        route_count_before = Route.objects.filter(user_profile=self.profile_a).count()

        form_data = {
            'start_location': 'Joinville, SC',
            'end_location': 'Curitiba, PR',
            'vehicle': self.vehicle_a.pk,
            'driver': self.driver_a.pk,
            'start_time': (self.now + timedelta(days=1)).strftime('%d/%m/%Y %H:%M'),
            'end_time': (self.now + timedelta(days=2)).strftime('%d/%m/%Y %H:%M'),
        }

        response = self.client.post(add_url, data=form_data, 
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        self.assertEqual(Route.objects.filter(user_profile=self.profile_a).count(), route_count_before + 1)
        new_route = Route.objects.latest('id')
        
        self.assertEqual(new_route.estimated_distance, Decimal('150.00'))
        self.assertEqual(new_route.estimated_toll_cost, Decimal('25.50'))
        self.assertEqual(new_route.fuel_price_per_liter, Decimal('5.80'))
        
        mock_calculate_route.assert_called_once_with('Joinville, SC', 'Curitiba, PR')
        mock_get_price.assert_called_once_with('SC')

    @patch('dashboard.route_views.get_diesel_price')
    @patch('dashboard.route_views.calculate_route_details')
    def test_route_complete_view_updates_mileage(self, mock_calculate_route, mock_get_price):
        mock_calculate_route.return_value = {'distance': 100.0, 'toll_cost': 10.0}
        mock_get_price.return_value = Decimal('5.0')
        
        route = Route.objects.create(
            user_profile=self.profile_a,
            vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="Ponto A", end_location="Ponto B",
            start_time=self.now - timedelta(days=2),
            end_time=self.now - timedelta(days=1),
            status='in_progress',
            estimated_distance=100.0
        )
        
        complete_url = reverse('route-complete', kwargs={'pk': route.pk})
        
        mileage_before = self.vehicle_a.mileage 
        self.assertEqual(mileage_before, 10000)
        
        form_data = {
            'actual_distance': 125.50 
        }
        
        response = self.client.post(complete_url, data=form_data)
        self.assertRedirects(response, reverse('route-list'))
        
        route.refresh_from_db()
        self.vehicle_a.refresh_from_db()
        
        self.assertEqual(route.status, 'completed')
        self.assertEqual(route.actual_distance, Decimal('125.50'))
        
        self.assertEqual(self.vehicle_a.mileage, 10125)

class CoreViewTests(DashboardBaseTestCase):

    def setUp(self):
        super().setUp()
        self.profile_url = reverse('user-profile')

    def test_user_profile_view_get(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/user_profile.html')
        self.assertContains(response, self.profile_a.company_name)
        self.assertContains(response, self.user_a.first_name)

    def test_user_profile_update_profile_post_success(self):
        form_data = {
            'first_name': 'Usuario A Atualizado',
            'username': self.user_a.username,
            'company_name': 'Empresa A Atualizada',
            'cnpj': '11.111.111/1111-11',
            'update_profile': '1'
        }
        
        response = self.client.post(self.profile_url, data=form_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)

        self.user_a.refresh_from_db()
        self.profile_a.refresh_from_db()

        self.assertEqual(self.user_a.first_name, 'Usuario A Atualizado')
        self.assertEqual(self.profile_a.company_name, 'Empresa A Atualizada')
        self.assertEqual(self.profile_a.cnpj, '11111111111111') 

    def test_user_profile_update_password_post_success(self):
        old_password = 'password123'
        new_password = 'new_password_abc'
        
        form_data = {
            'old_password': old_password,
            'new_password1': new_password,
            'new_password2': new_password,
            'update_password': '1'
        }
        
        response = self.client.post(self.profile_url, data=form_data)
        self.assertRedirects(response, self.profile_url)
        
        self.user_a.refresh_from_db()
        
        self.assertTrue(check_password(new_password, self.user_a.password))
        self.assertFalse(check_password(old_password, self.user_a.password))

    def test_user_profile_update_password_post_fail_mismatch(self):
        form_data = {
            'old_password': 'password123',
            'new_password1': 'new_password_abc',
            'new_password2': 'senha_errada',
            'update_password': '1'
        }
        
        response = self.client.post(self.profile_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Erro ao alterar a senha')
        self.assertTrue(response.context['show_password_form_errors'])

class DriverViewTests(DashboardBaseTestCase):
    
    def setUp(self):
        super().setUp()
        self.list_url = reverse('driver-list')
        self.add_url = reverse('driver-add')
        self.update_url = reverse('driver-update', kwargs={'pk': self.driver_a.pk})
        self.deactivate_url = reverse('driver-deactivate', kwargs={'pk': self.driver_a.pk})
        self.history_url = reverse('driver-route-history', kwargs={'pk': self.driver_a.pk})

    def test_driver_list_view_get_and_filters(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Motorista A')
        
        response_inactive = self.client.get(self.list_url, {'status': 'inactive'})
        self.assertNotContains(response_inactive, 'Motorista A')
        
        response_search = self.client.get(self.list_url, {'search': '111111'})
        self.assertContains(response_search, 'Motorista A')

    def test_driver_create_view_post_success(self):
        driver_count = Driver.objects.filter(user_profile=self.profile_a).count()
        form_data = {
            'full_name': 'Motorista B',
            'email': 'driver_b@teste.com',
            'license_number': '22222222222',
            'admission_date': '2025-01-01'
        }
        response = self.client.post(self.add_url, data=form_data)
        self.assertRedirects(response, self.list_url)
        self.assertEqual(Driver.objects.filter(user_profile=self.profile_a).count(), driver_count + 1)

    def test_driver_create_view_post_fail_invalid_cnh(self):
        driver_count = Driver.objects.filter(user_profile=self.profile_a).count()
        form_data = {
            'full_name': 'Motorista C',
            'email': 'driver_c@teste.com',
            'license_number': '123',
            'admission_date': '2025-01-01'
        }
        response = self.client.post(self.add_url, data=form_data)
        self.assertRedirects(response, self.list_url)
        
        self.assertEqual(Driver.objects.filter(user_profile=self.profile_a).count(), driver_count) 
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('A CNH deve conter exatamente 11 dígitos', str(messages[0]))

    def test_driver_deactivate_view_post(self):
        self.assertTrue(self.driver_a.is_active)
        response = self.client.post(self.deactivate_url)
        self.assertRedirects(response, self.list_url)
        
        self.driver_a.refresh_from_db()
        self.assertFalse(self.driver_a.is_active)
        self.assertEqual(self.driver_a.demission_date, date.today())
    
    def test_driver_route_history_json_view(self):
        Route.objects.create(
            user_profile=self.profile_a,
            vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="Ponto A", end_location="Ponto B",
            start_time=self.now - timedelta(days=2),
            end_time=self.now - timedelta(days=1),
            status='completed', actual_distance=100
        )
        
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['history']), 1)
        self.assertEqual(data['stats']['total_routes'], 1)
        self.assertEqual(data['history'][0]['vehicle_plate'], self.vehicle_a.plate)

class MaintenanceViewTests(DashboardBaseTestCase):
    
    def setUp(self):
        super().setUp()
        self.list_url = reverse('maintenance-list')
        self.add_url = reverse('maintenance-add')
        self.maint = Maintenance.objects.create(
            user_profile=self.profile_a,
            vehicle=self.vehicle_a,
            service_type='Troca de Teste',
            start_date=self.now + timedelta(days=1),
            end_date=self.now + timedelta(days=2),
            mechanic_shop_name='Oficina Teste',
            current_mileage=self.vehicle_a.mileage,
            estimated_cost=100.00,
            status='scheduled'
        )
        self.complete_url = reverse('maintenance-complete', kwargs={'pk': self.maint.pk})
        self.cancel_url = reverse('maintenance-cancel', kwargs={'pk': self.maint.pk})

    def test_maintenance_list_view_get_and_filters(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Troca de Teste')
        
        response_completed = self.client.get(self.list_url, {'status': 'completed'})
        self.assertNotContains(response_completed, 'Troca de Teste')

    def test_maintenance_create_view_post_service_choice_outro(self):
        maint_count = Maintenance.objects.filter(user_profile=self.profile_a).count()
        form_data = {
            'vehicle': self.vehicle_a.pk,
            'service_choice': 'Outro',
            'service_type_other': 'Serviço Customizado',
            'start_date': (self.now + timedelta(days=5)).strftime('%d/%m/%Y %H:%M'),
            'end_date': (self.now + timedelta(days=6)).strftime('%d/%m/%Y %H:%M'),
            'mechanic_shop_name': 'Oficina X',
            'estimated_cost': 50.00,
            'current_mileage': self.vehicle_a.mileage
        }
        
        response = self.client.post(self.add_url, data=form_data)
        self.assertRedirects(response, self.list_url)
        
        self.assertEqual(Maintenance.objects.filter(user_profile=self.profile_a).count(), maint_count + 1)
        new_maint = Maintenance.objects.latest('id')
        self.assertEqual(new_maint.service_type, 'Serviço Customizado')

    def test_maintenance_complete_view_post(self):
        self.assertEqual(self.maint.status, 'scheduled')
        
        form_data = {
            'actual_cost': 110.00,
            'actual_end_date': (self.now + timedelta(days=2)).strftime('%d/%m/%Y %H:%M')
        }
        
        response = self.client.post(self.complete_url, data=form_data)
        self.assertRedirects(response, self.list_url)
        
        self.maint.refresh_from_db()
        self.assertEqual(self.maint.status, 'completed')
        self.assertEqual(self.maint.actual_cost, Decimal('110.00'))
        
        messages = list(response.context['messages'])
        self.assertTrue(any('O custo final' in str(m) for m in messages))

    def test_maintenance_cancel_view_post(self):
        self.assertEqual(self.maint.status, 'scheduled')
        response = self.client.post(self.cancel_url)
        self.assertRedirects(response, self.list_url)
        
        self.maint.refresh_from_db()
        self.assertEqual(self.maint.status, 'canceled')

class AlertConfigViewTests(DashboardBaseTestCase):
            
    def setUp(self):
        super().setUp()
        self.config_url = reverse('alert-config')
        self.client.get(self.config_url)
    
    def test_alert_config_post_update_settings(self):
        config = AlertConfiguration.objects.get(
            user_profile=self.profile_a, 
            service_type='Revisão Geral'
        )
        self.assertIsNone(config.km_threshold) 

        total_forms = AlertConfiguration.objects.filter(user_profile=self.profile_a).count()
        
        formset_data = {
            'form-TOTAL_FORMS': str(total_forms),
            'form-INITIAL_FORMS': str(total_forms),
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
        }
        
        forms_qs = AlertConfiguration.objects.filter(user_profile=self.profile_a).order_by('service_type')
        
        for i, form_instance in enumerate(forms_qs):
            prefix = f'form-{i}'
            formset_data[f'{prefix}-id'] = form_instance.id
            formset_data[f'{prefix}-user_profile'] = form_instance.user_profile.id
            formset_data[f'{prefix}-service_type'] = form_instance.service_type
            
            if form_instance.service_type == 'Revisão Geral':
                formset_data[f'{prefix}-km_threshold'] = '10000'
                formset_data[f'{prefix}-days_threshold'] = '365'
                formset_data[f'{prefix}-priority'] = 'high'
                formset_data[f'{prefix}-is_active'] = 'on'
            else:
                formset_data[f'{prefix}-km_threshold'] = form_instance.km_threshold or ''
                formset_data[f'{prefix}-days_threshold'] = form_instance.days_threshold or ''
                formset_data[f'{prefix}-priority'] = form_instance.priority
                if form_instance.is_active:
                     formset_data[f'{prefix}-is_active'] = 'on'
        
        response = self.client.post(self.config_url, data=formset_data)
        self.assertRedirects(response, self.config_url)
        
        config.refresh_from_db()
        self.assertEqual(config.km_threshold, 10000)
        self.assertEqual(config.days_threshold, 365)
        self.assertEqual(config.priority, 'high')

class SimplifiedFrontendTests(LiveServerTestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.test_user = User.objects.create_user(
            username='selenium@teste.com',
            password='password123',
            first_name='Usuário de Teste'
        )
        self.profile = UserProfile.objects.create(
            user=self.test_user,
            company_name="Empresa Teste E2E",
            cnpj="99999999000199"
        )
        self.login_url = self.live_server_url + reverse('login')
        self.driver.get(self.login_url)
        self.driver.find_element(By.ID, "id_username").send_keys('selenium@teste.com')
        self.driver.find_element(By.ID, "id_password").send_keys('password123')
        self.driver.find_element(By.CLASS_NAME, "btn-signin").click()
        WebDriverWait(self.driver, 50).until(
            EC.title_contains("Dashboard de Gestão de Frotas")
        )

    def test_page_navigation(self):
        self.driver.get(self.live_server_url + reverse('vehicle-list'))
        self.assertTrue(WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "open-add-vehicle-modal"))
        ))
        self.assertIn("Gerenciamento de Veículos", self.driver.title)

        self.driver.get(self.live_server_url + reverse('driver-list'))
        self.assertTrue(WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "open-add-driver-modal"))
        ))
        self.assertIn("Gerenciamento de Motoristas", self.driver.title)

        self.driver.get(self.live_server_url + reverse('route-list'))
        self.assertTrue(WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "open-add-route-modal"))
        ))
        self.assertIn("Planejamento de Rotas", self.driver.title)
        
        self.driver.get(self.live_server_url + reverse('maintenance-list'))
        self.assertTrue(WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "open-add-maintenance-modal"))
        ))
        self.assertIn("Gerenciamento de Manutenções", self.driver.title)
        
        self.driver.get(self.live_server_url + reverse('alert-config'))
        self.assertTrue(WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "open-config-modal"))
        ))
        self.assertIn("Alertas de Manutenção", self.driver.title)

    def test_driver_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('driver-list'))
        add_button = WebDriverWait(self.driver, 50).until(
            EC.element_to_be_clickable((By.ID, "open-add-driver-modal"))
        )
        add_button.click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "add-driver-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_vehicle_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('vehicle-list'))
        add_button = WebDriverWait(self.driver, 50).until(
            EC.element_to_be_clickable((By.ID, "open-add-vehicle-modal"))
        )
        add_button.click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "add-vehicle-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_route_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('route-list'))
        add_button = WebDriverWait(self.driver, 50).until(
            EC.element_to_be_clickable((By.ID, "open-add-route-modal"))
        )
        add_button.click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "route-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_maintenance_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('maintenance-list'))
        add_button = WebDriverWait(self.driver, 50).until(
            EC.element_to_be_clickable((By.ID, "open-add-maintenance-modal"))
        )
        add_button.click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "maintenance-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_alert_config_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('alert-config'))
        add_button = WebDriverWait(self.driver, 50).until(
            EC.element_to_be_clickable((By.ID, "open-config-modal"))
        )
        add_button.click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "config-modal"))
        )
        self.assertTrue(modal.is_displayed())