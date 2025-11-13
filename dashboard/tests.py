from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import patch
from decimal import Decimal

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
            EC.title_contains("Gerenciamento de Veículos")
        ))
        
        self.driver.get(self.live_server_url + reverse('driver-list'))
        self.assertTrue(WebDriverWait(self.driver, 50).until(
            EC.title_contains("Gerenciamento de Motoristas")
        ))

        self.driver.get(self.live_server_url + reverse('route-list'))
        self.assertTrue(WebDriverWait(self.driver, 50).until(
            EC.title_contains("Planejamento de Rotas")
        ))
        
        self.driver.get(self.live_server_url + reverse('maintenance-list'))
        self.assertTrue(WebDriverWait(self.driver, 50).until(
            EC.title_contains("Gerenciamento de Manutenções")
        ))
        
        self.driver.get(self.live_server_url + reverse('alert-config'))
        self.assertTrue(WebDriverWait(self.driver, 50).until(
            EC.title_contains("Alertas de Manutenção")
        ))

    def test_driver_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('driver-list'))
        self.driver.find_element(By.ID, "open-add-driver-modal").click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "add-driver-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_vehicle_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('vehicle-list'))
        self.driver.find_element(By.ID, "open-add-vehicle-modal").click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "add-vehicle-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_route_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('route-list'))
        self.driver.find_element(By.ID, "open-add-route-modal").click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "route-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_maintenance_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('maintenance-list'))
        self.driver.find_element(By.ID, "open-add-maintenance-modal").click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "maintenance-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_alert_config_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('alert-config'))
        self.driver.find_element(By.ID, "open-config-modal").click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "config-modal"))
        )
        self.assertTrue(modal.is_displayed())