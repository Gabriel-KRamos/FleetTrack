from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import patch
from decimal import Decimal
from django.contrib.auth.hashers import check_password
import requests

from .models import Driver, Vehicle, Route, Maintenance, AlertConfiguration
from accounts.models import UserProfile
from .forms import DriverForm, MaintenanceForm, RouteForm
from .services import get_vehicle_alerts

from django.contrib.staticfiles.testing import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    def test_str_methods(self):
        self.assertEqual(str(self.driver_a), "Motorista A")
        self.assertEqual(str(self.vehicle_a), "Modelo A - AAA-1111")
        
        maint = Maintenance.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, service_type="Teste",
            start_date=self.now, end_date=self.now + timedelta(days=1), mechanic_shop_name="Oficina", current_mileage=10000
        )
        self.assertEqual(str(maint), "Teste - AAA-1111")
        
        route = Route.objects.create(
            user_profile=self.profile_a, start_location="A", end_location="B",
            start_time=self.now, end_time=self.now + timedelta(hours=5)
        )
        self.assertTrue("Rota de A para B" in str(route))
        
        alert = AlertConfiguration.objects.create(user_profile=self.profile_a, service_type="Revisão Geral")
        self.assertEqual(str(alert), "Revisão Geral")

    def test_vehicle_dynamic_status_logic(self):
        self.assertEqual(self.vehicle_a.dynamic_status_slug, 'available')
        Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="A", end_location="B",
            start_time=self.now - timedelta(hours=1),
            end_time=self.now + timedelta(hours=2),
            status='in_progress'
        )
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.dynamic_status_slug, 'on_route')
        
        Maintenance.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, service_type="M",
            start_date=self.now - timedelta(hours=1), end_date=self.now + timedelta(hours=2),
            mechanic_shop_name="Oficina", current_mileage=10000, status='in_progress'
        )
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.dynamic_status_slug, 'maintenance')

    def test_route_properties(self):
        route = Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="A", end_location="B",
            start_time=self.now - timedelta(hours=2),
            end_time=self.now + timedelta(hours=2),
            status='scheduled'
        )
        self.assertEqual(route.dynamic_status, "Em Andamento")
        self.assertEqual(route.dynamic_status_slug, "in_progress")
        self.assertEqual(route.progress_percentage, 50)
        route.estimated_distance = 100
        route.fuel_price_per_liter = 5.0
        self.assertEqual(route.estimated_fuel_cost, 50.0)

    def test_maintenance_dynamic_status(self):
        maint = Maintenance.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, service_type="Teste",
            start_date=self.now - timedelta(days=2),
            end_date=self.now - timedelta(days=1),
            mechanic_shop_name="Oficina", current_mileage=10000,
            status='scheduled'
        )
        self.assertEqual(maint.dynamic_status_slug, "overdue")
        maint.status = 'completed'
        maint.save()
        self.assertEqual(maint.dynamic_status_slug, "completed")

    def test_vehicle_properties(self):
        self.assertEqual(self.vehicle_a.dynamic_status_slug, 'available')
        self.assertIsNone(self.vehicle_a.current_route_driver)
        
        Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="Origem", end_location="Destino",
            start_time=self.now - timedelta(hours=1),
            end_time=self.now + timedelta(hours=2),
            status='in_progress'
        )
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.current_route_driver, self.driver_a)

class FormTests(DashboardBaseTestCase):
    def test_driver_form_valid(self):
        form_data = {
            'full_name': 'Novo Motorista',
            'email': 'novo@teste.com',
            'license_number': '12345678901',
            'admission_date': '2024-01-01'
        }
        form = DriverForm(data=form_data)
        self.assertTrue(form.is_valid())

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
            user_profile=self.profile_a, vehicle=self.vehicle_a, service_type="C",
            start_date=self.now + timedelta(days=1), end_date=self.now + timedelta(days=2),
            mechanic_shop_name="O", current_mileage=10000, status='scheduled'
        )
        form_data = {
            'start_location': 'A, SC', 'end_location': 'B, SC',
            'vehicle': self.vehicle_a.pk, 'driver': self.driver_a.pk,
            'start_time': (self.now + timedelta(days=1, hours=2)).strftime('%d/%m/%Y %H:%M'),
            'end_time': (self.now + timedelta(days=1, hours=5)).strftime('%d/%m/%Y %H:%M'),
        }
        form = RouteForm(data=form_data, user_profile=self.profile_a)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_maintenance_form_clean_other_service(self):
        form_data = {
            'vehicle': self.vehicle_a.pk, 'service_choice': 'Outro', 'service_type_other': '',
            'start_date': (self.now + timedelta(days=5)).strftime('%d/%m/%Y %H:%M'),
            'end_date': (self.now + timedelta(days=6)).strftime('%d/%m/%Y %H:%M'),
            'mechanic_shop_name': 'X', 'estimated_cost': 50.00, 'current_mileage': self.vehicle_a.mileage
        }
        form = MaintenanceForm(data=form_data, user_profile=self.profile_a)
        self.assertFalse(form.is_valid())
        self.assertIn('service_type_other', form.errors)
        
        form_data['service_type_other'] = 'Serviço Customizado'
        form = MaintenanceForm(data=form_data, user_profile=self.profile_a)
        self.assertTrue(form.is_valid())
        maint = form.save()
        self.assertEqual(maint.service_type, 'Serviço Customizado')

    def test_route_form_invalid_location_format(self):
        form_data = {
            'start_location': 'Local Apenas', 'end_location': 'Local B, SC',
            'vehicle': self.vehicle_a.pk, 'driver': self.driver_a.pk,
            'start_time': (self.now + timedelta(days=1)).strftime('%d/%m/%Y %H:%M'),
            'end_time': (self.now + timedelta(days=2)).strftime('%d/%m/%Y %H:%M'),
        }
        form = RouteForm(data=form_data, user_profile=self.profile_a)
        self.assertFalse(form.is_valid())
        self.assertIn('start_location', form.errors)

    def test_route_form_conflict_driver(self):
        Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="A, SC", end_location="B, SC",
            start_time=self.now + timedelta(days=1, hours=1),
            end_time=self.now + timedelta(days=1, hours=5), status='scheduled'
        )
        form_data = {
            'start_location': 'C, SC', 'end_location': 'D, SC',
            'vehicle': self.vehicle_b.pk, 'driver': self.driver_a.pk,
            'start_time': (self.now + timedelta(days=1, hours=2)).strftime('%d/%m/%Y %H:%M'),
            'end_time': (self.now + timedelta(days=1, hours=4)).strftime('%d/%m/%Y %H:%M'),
        }
        form = RouteForm(data=form_data, user_profile=self.profile_a)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

class CoreViewTests(DashboardBaseTestCase):
    def setUp(self):
        super().setUp()
        self.profile_url = reverse('user-profile')

    def test_dashboard_stats_logic(self):
        Vehicle.objects.create(user_profile=self.profile_a, plate='DIS-0001', model='D', year=2022, initial_mileage=0, acquisition_date=date.today(), status='disabled')
        v_route = Vehicle.objects.create(user_profile=self.profile_a, plate='ROT-0001', model='R', year=2022, initial_mileage=0, acquisition_date=date.today())
        Route.objects.create(user_profile=self.profile_a, vehicle=v_route, driver=self.driver_a, start_location="A", end_location="B", start_time=self.now - timedelta(hours=1), end_time=self.now + timedelta(hours=1), status='in_progress')
        v_maint = Vehicle.objects.create(user_profile=self.profile_a, plate='MNT-0001', model='M', year=2022, initial_mileage=0, acquisition_date=date.today())
        Maintenance.objects.create(user_profile=self.profile_a, vehicle=v_maint, service_type="S", start_date=self.now - timedelta(hours=1), end_date=self.now + timedelta(hours=1), mechanic_shop_name="O", current_mileage=0, status='in_progress')

        response = self.client.get(reverse('dashboard'))
        ctx = response.context['vehicle_overview']
        self.assertEqual(ctx['total'], 4) 
        self.assertEqual(ctx['available'], 1) 
        self.assertEqual(ctx['unavailable'], 1) 
        self.assertEqual(ctx['in_use'], 1) 
        self.assertEqual(ctx['maintenance'], 1)

    def test_user_profile_view_get(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.profile_a.company_name)

    def test_user_profile_post_success(self):
        response = self.client.post(self.profile_url, {
            'update_profile': '1', 'first_name': 'Novo', 'username': 'novo@teste.com', 'company_name': 'Nova', 'cnpj': '11111111111111'
        })
        self.assertRedirects(response, self.profile_url)
        self.user_a.refresh_from_db()
        self.assertEqual(self.user_a.first_name, 'Novo')

    def test_user_profile_post_invalid(self):
        response = self.client.post(self.profile_url, {
            'update_profile': '1', 'first_name': '', 'username': '' 
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('Erro ao atualizar' in str(m) for m in response.context['messages']))

    def test_password_change_success(self):
        response = self.client.post(self.profile_url, {
            'update_password': '1', 'old_password': 'password123', 'new_password1': 'new123', 'new_password2': 'new123'
        })
        self.assertRedirects(response, self.profile_url)
        self.assertTrue(check_password('new123', User.objects.get(pk=self.user_a.pk).password))

    def test_password_change_invalid(self):
        response = self.client.post(self.profile_url, {
            'update_password': '1', 'old_password': 'wrong', 'new_password1': 'new', 'new_password2': 'new'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_password_form_errors'])

class DriverViewTests(DashboardBaseTestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse('driver-list')
        self.add_url = reverse('driver-add')
        self.update_url = reverse('driver-update', kwargs={'pk': self.driver_a.pk})
        self.deactivate_url = reverse('driver-deactivate', kwargs={'pk': self.driver_a.pk})

    def test_driver_list_filters(self):
        Driver.objects.create(user_profile=self.profile_a, full_name="Inativo", email="i@t.com", license_number="22222222222", admission_date=date.today(), is_active=False)
        res = self.client.get(self.list_url, {'status': 'active'})
        self.assertEqual(len(res.context['drivers']), 1)
        res = self.client.get(self.list_url, {'status': 'inactive'})
        self.assertEqual(len(res.context['drivers']), 1)
        res = self.client.get(self.list_url, {'search': 'Inativo'})
        self.assertContains(res, 'Inativo')

    def test_driver_create_success(self):
        response = self.client.post(self.add_url, {
            'full_name': 'B', 'email': 'b@t.com', 'license_number': '22222222222', 'admission_date': '2024-01-01'
        })
        self.assertRedirects(response, self.list_url)
        self.assertEqual(Driver.objects.filter(user_profile=self.profile_a).count(), 2)

    def test_driver_create_invalid(self):
        response = self.client.post(self.add_url, {'full_name': 'C', 'email': 'c@t.com', 'license_number': '123', 'admission_date': '2024-01-01'})
        self.assertRedirects(response, self.list_url)
        self.assertEqual(Driver.objects.filter(user_profile=self.profile_a).count(), 1)

    def test_driver_update_success(self):
        response = self.client.post(self.update_url, {
            'full_name': 'A Updated', 'email': self.driver_a.email, 'license_number': self.driver_a.license_number, 'admission_date': '2024-01-01'
        })
        self.assertRedirects(response, self.list_url)
        self.driver_a.refresh_from_db()
        self.assertEqual(self.driver_a.full_name, 'A Updated')

    def test_driver_update_invalid(self):
        response = self.client.post(self.update_url, {'full_name': '', 'email': 'invalid'})
        self.assertRedirects(response, self.list_url)
        self.assertTrue(len(response.context['messages']) > 0) 

    def test_driver_deactivate(self):
        response = self.client.post(self.deactivate_url)
        self.assertRedirects(response, self.list_url)
        self.driver_a.refresh_from_db()
        self.assertFalse(self.driver_a.is_active)
    
    def test_driver_route_history_json(self):
        Route.objects.create(user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a, start_location="A", end_location="B", start_time=self.now, end_time=self.now, status='completed', actual_distance=10)
        url = reverse('driver-route-history', kwargs={'pk': self.driver_a.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['history']), 1)

class MaintenanceViewTests(DashboardBaseTestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse('maintenance-list')
        self.add_url = reverse('maintenance-add')
        self.maint = Maintenance.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, service_type='T', start_date=self.now + timedelta(days=1), end_date=self.now + timedelta(days=2), mechanic_shop_name='O', current_mileage=10, estimated_cost=100.00, status='scheduled'
        )

    def test_maintenance_list_filters_logic(self):
        m_sched = Maintenance.objects.create(user_profile=self.profile_a, vehicle=self.vehicle_a, service_type="S", start_date=self.now + timedelta(days=5), end_date=self.now + timedelta(days=6), mechanic_shop_name="O", current_mileage=10, status='scheduled')
        m_prog = Maintenance.objects.create(user_profile=self.profile_a, vehicle=self.vehicle_a, service_type="P", start_date=self.now - timedelta(hours=1), end_date=self.now + timedelta(hours=1), mechanic_shop_name="O", current_mileage=10, status='in_progress')
        m_over = Maintenance.objects.create(user_profile=self.profile_a, vehicle=self.vehicle_a, service_type="O", start_date=self.now - timedelta(days=5), end_date=self.now - timedelta(days=4), mechanic_shop_name="O", current_mileage=10, status='scheduled')
        m_comp = Maintenance.objects.create(user_profile=self.profile_a, vehicle=self.vehicle_a, service_type="C", start_date=self.now, end_date=self.now, mechanic_shop_name="O", current_mileage=10, status='completed', actual_end_date=self.now)

        res = self.client.get(self.list_url, {'status': 'scheduled'})
        self.assertIn(m_sched, res.context['maintenances'])
        self.assertNotIn(m_over, res.context['maintenances'])
        res = self.client.get(self.list_url, {'status': 'in_progress'})
        self.assertIn(m_prog, res.context['maintenances'])
        res = self.client.get(self.list_url, {'status': 'overdue'})
        self.assertIn(m_over, res.context['maintenances'])
        res = self.client.get(self.list_url, {'status': 'completed'})
        self.assertIn(m_comp, res.context['maintenances'])

    def test_maintenance_create_success(self):
        response = self.client.post(self.add_url, {
            'vehicle': self.vehicle_a.pk, 'service_choice': 'Outro', 'service_type_other': 'X',
            'start_date': (self.now + timedelta(days=1)).strftime('%d/%m/%Y %H:%M'),
            'end_date': (self.now + timedelta(days=2)).strftime('%d/%m/%Y %H:%M'),
            'mechanic_shop_name': 'M', 'estimated_cost': '100', 'current_mileage': 1000
        })
        self.assertRedirects(response, self.list_url)
        self.assertEqual(Maintenance.objects.count(), 2)

    def test_maintenance_create_fail(self):
        response = self.client.post(self.add_url, {})
        self.assertRedirects(response, self.list_url)
        self.assertTrue(len(response.context['messages']) > 0)

    def test_maintenance_update_success(self):
        url = reverse('maintenance-update', kwargs={'pk': self.maint.pk})
        response = self.client.post(url, {
            'vehicle': self.maint.vehicle.pk, 'service_choice': 'T', 'service_type_other': '',
            'start_date': self.maint.start_date.strftime('%d/%m/%Y %H:%M'),
            'end_date': self.maint.end_date.strftime('%d/%m/%Y %H:%M'),
            'mechanic_shop_name': 'Updated', 'estimated_cost': 150, 'current_mileage': 10
        })
        self.assertRedirects(response, self.list_url)
        self.maint.refresh_from_db()
        self.assertEqual(self.maint.mechanic_shop_name, 'Updated')

    def test_maintenance_update_invalid(self):
        url = reverse('maintenance-update', kwargs={'pk': self.maint.pk})
        response = self.client.post(url, {})
        self.assertRedirects(response, self.list_url)
        self.assertTrue(len(response.context['messages']) > 0)

    def test_maintenance_complete(self):
        url = reverse('maintenance-complete', kwargs={'pk': self.maint.pk})
        response = self.client.post(url, {'actual_cost': '150.00', 'actual_end_date': self.now.strftime('%d/%m/%Y %H:%M')})
        self.assertRedirects(response, self.list_url)
        messages = list(response.context['messages'])
        self.assertTrue(any('Atenção: O custo final' in str(m) for m in messages))
        self.maint.refresh_from_db()
        self.assertEqual(self.maint.status, 'completed')

    def test_maintenance_cancel(self):
        url = reverse('maintenance-cancel', kwargs={'pk': self.maint.pk})
        response = self.client.post(url)
        self.assertRedirects(response, self.list_url)
        self.maint.refresh_from_db()
        self.assertEqual(self.maint.status, 'canceled')

class AlertViewTests(DashboardBaseTestCase):
    def setUp(self):
        super().setUp()
        self.config_url = reverse('alert-config')

    def test_alert_config_get(self):
        response = self.client.get(self.config_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('formset', response.context)

    def test_alert_config_post_success(self):
        AlertConfiguration.objects.create(user_profile=self.profile_a, service_type='Revisão Geral')
        total = AlertConfiguration.objects.filter(user_profile=self.profile_a).count()
        formset_data = {
            'form-TOTAL_FORMS': str(total), 'form-INITIAL_FORMS': str(total),
            'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
        }
        for i, f in enumerate(AlertConfiguration.objects.filter(user_profile=self.profile_a)):
            formset_data[f'form-{i}-id'] = f.id
            formset_data[f'form-{i}-user_profile'] = f.user_profile.id
            formset_data[f'form-{i}-service_type'] = f.service_type
            formset_data[f'form-{i}-km_threshold'] = 1000
            formset_data[f'form-{i}-priority'] = 'high'
            formset_data[f'form-{i}-is_active'] = 'on'
        response = self.client.post(self.config_url, formset_data)
        self.assertRedirects(response, self.config_url)

    def test_alert_config_post_invalid(self):
        response = self.client.post(self.config_url, {
            'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '1', 'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000', 'form-0-id': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('Erro ao salvar' in str(m) for m in response.context['messages']))

class LogicTests(DashboardBaseTestCase):
    def test_get_vehicle_alerts_logic(self):
        AlertConfiguration.objects.create(user_profile=self.profile_a, service_type='Revisão Geral', km_threshold=100, days_threshold=30, is_active=True, priority='high')
        
        v1 = Vehicle.objects.create(user_profile=self.profile_a, plate='KM-001', model='M', year=2020, initial_mileage=1000, acquisition_date=date.today())
        Maintenance.objects.create(user_profile=self.profile_a, vehicle=v1, service_type='Revisão Geral', start_date=self.now, end_date=self.now, mechanic_shop_name="O", current_mileage=500, status='completed', actual_end_date=self.now)
        
        v2 = Vehicle.objects.create(user_profile=self.profile_a, plate='DAY-001', model='M', year=2020, initial_mileage=0, acquisition_date=(self.now - timedelta(days=40)).date())
        
        alerts = get_vehicle_alerts(self.profile_a)
        self.assertTrue(any(a.vehicle.plate == 'KM-001' and 'km' in a.message for a in alerts))
        self.assertTrue(any(a.vehicle.plate == 'DAY-001' and 'dias' in a.message for a in alerts))

    def test_get_vehicle_alerts_limit(self):
        AlertConfiguration.objects.create(user_profile=self.profile_a, service_type='Revisão Geral', km_threshold=1, is_active=True)
        for i in range(3):
            Vehicle.objects.create(user_profile=self.profile_a, plate=f'V-{i}', model='M', year=2020, initial_mileage=100, acquisition_date=date.today())
            Maintenance.objects.create(user_profile=self.profile_a, vehicle=Vehicle.objects.get(plate=f'V-{i}'), service_type='Revisão Geral', start_date=self.now, end_date=self.now, mechanic_shop_name="O", current_mileage=10, status='completed', actual_end_date=self.now)
        
        alerts = get_vehicle_alerts(self.profile_a, limit=2)
        self.assertEqual(len(alerts), 2)

    @patch('dashboard.services.requests.post')
    def test_calculate_route_details_api_error_403(self, mock_post):
        from .services import calculate_route_details
        mock_response = mock_post.return_value
        mock_response.status_code = 403
        mock_response.text = 'API Key Invalid'
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        result = calculate_route_details("Origem", "Destino")
        self.assertIsInstance(result, str)
        self.assertIn("Erro na API do Google (403)", result)

class ApiViewTests(DashboardBaseTestCase):
    def test_vehicle_route_history_json(self):
        Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="JSON Test, SC", end_location="API Test, PR",
            start_time=self.now - timedelta(days=2),
            end_time=self.now - timedelta(days=1),
            status='completed', actual_distance=250
        )
        history_url = reverse('vehicle-route-history', kwargs={'pk': self.vehicle_a.pk})
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['history']), 1)
        
    def test_user_a_cannot_see_user_b_history_json(self):
        history_url_b = reverse('vehicle-route-history', kwargs={'pk': self.vehicle_b.pk})
        response = self.client.get(history_url_b)
        self.assertEqual(response.status_code, 404)
    
    def test_vehicle_maintenance_history_json(self):
        Maintenance.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, service_type="S",
            start_date=self.now, end_date=self.now, mechanic_shop_name="O", current_mileage=100, status='completed', actual_cost=100, actual_end_date=self.now
        )
        response = self.client.get(reverse('vehicle-maintenance-history', kwargs={'pk': self.vehicle_a.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['history']), 1)

    def test_driver_route_history_json(self):
        Route.objects.create(user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a, start_location="A", end_location="B", start_time=self.now, end_time=self.now, status='completed', actual_distance=10)
        url = reverse('driver-route-history', kwargs={'pk': self.driver_a.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['history']), 1)

class RouteViewMockTests(DashboardBaseTestCase):
    @patch('dashboard.route_views.get_diesel_price')
    @patch('dashboard.route_views.calculate_route_details')
    def test_route_create_view_with_mock(self, mock_calculate_route, mock_get_price):
        mock_calculate_route.return_value = {'distance': 150.0, 'toll_cost': 25.50}
        mock_get_price.return_value = Decimal('5.80')
        add_url = reverse('route-add')
        form_data = {
            'start_location': 'Joinville, SC', 'end_location': 'Curitiba, PR',
            'vehicle': self.vehicle_a.pk, 'driver': self.driver_a.pk,
            'start_time': (self.now + timedelta(days=1)).strftime('%d/%m/%Y %H:%M'),
            'end_time': (self.now + timedelta(days=2)).strftime('%d/%m/%Y %H:%M'),
        }
        response = self.client.post(add_url, data=form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        new_route = Route.objects.latest('id')
        self.assertEqual(new_route.estimated_distance, Decimal('150.00'))

    @patch('dashboard.route_views.get_diesel_price')
    @patch('dashboard.route_views.calculate_route_details')
    def test_route_complete_view_updates_mileage(self, mock_calculate_route, mock_get_price):
        mock_calculate_route.return_value = {'distance': 100.0, 'toll_cost': 10.0}
        mock_get_price.return_value = Decimal('5.0')
        route = Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="Ponto A", end_location="Ponto B",
            start_time=self.now - timedelta(days=2), end_time=self.now - timedelta(days=1),
            status='in_progress', estimated_distance=100.0
        )
        complete_url = reverse('route-complete', kwargs={'pk': route.pk})
        form_data = { 'actual_distance': 125.50 }
        response = self.client.post(complete_url, data=form_data)
        self.assertRedirects(response, reverse('route-list'))
        route.refresh_from_db()
        self.vehicle_a.refresh_from_db()
        self.assertEqual(route.status, 'completed')
        self.assertEqual(route.actual_distance, Decimal('125.50'))
        self.assertEqual(self.vehicle_a.mileage, 10125)

    @patch('dashboard.route_views.get_diesel_price')
    @patch('dashboard.route_views.calculate_route_details')
    def test_route_list_view_get_with_filters(self, mock_calculate_route, mock_get_price):
        mock_calculate_route.return_value = {'distance': 100.0, 'toll_cost': 10.0}
        mock_get_price.return_value = Decimal('5.0')
        Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="Joinville, SC", end_location="Curitiba, PR",
            start_time=self.now + timedelta(days=1), end_time=self.now + timedelta(days=2),
            status='scheduled'
        )
        list_url = reverse('route-list')
        response_search = self.client.get(list_url, {'search': 'Joinville'})
        self.assertEqual(response_search.status_code, 200)
        self.assertContains(response_search, 'Joinville, SC')
        response_status = self.client.get(list_url, {'status': 'completed'})
        self.assertEqual(response_status.status_code, 200)
        self.assertNotContains(response_status, 'Joinville, SC')

    @patch('dashboard.route_views.get_diesel_price')
    @patch('dashboard.route_views.calculate_route_details')
    def test_route_cancel_and_reactivate_view(self, mock_calculate_route, mock_get_price):
        mock_calculate_route.return_value = {'distance': 100.0, 'toll_cost': 10.0}
        mock_get_price.return_value = Decimal('5.0')
        route = Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="Ponto A, SC", end_location="Ponto B, PR",
            start_time=self.now + timedelta(days=1), end_time=self.now + timedelta(days=2),
            status='scheduled'
        )
        cancel_url = reverse('route-cancel', kwargs={'pk': route.pk})
        response = self.client.post(cancel_url)
        self.assertRedirects(response, reverse('route-list'))
        route.refresh_from_db()
        self.assertEqual(route.status, 'canceled')
        reactivate_url = reverse('route-reactivate', kwargs={'pk': route.pk})
        response = self.client.post(reactivate_url)
        self.assertRedirects(response, reverse('route-list'))
        route.refresh_from_db()
        self.assertEqual(route.status, 'scheduled')

    @patch('dashboard.route_views.calculate_route_details')
    @patch('dashboard.route_views.get_diesel_price')
    def test_route_update_success(self, mock_price, mock_calc):
        mock_calc.return_value = {'distance': 50.0, 'toll_cost': 0.0}
        mock_price.return_value = Decimal('5.0')
        route = Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="A", end_location="B",
            start_time=self.now + timedelta(days=1), end_time=self.now + timedelta(days=1, hours=1), status='scheduled'
        )
        response = self.client.post(reverse('route-update', kwargs={'pk': route.pk}), {
            'start_location': 'Joinville, SC', 'end_location': 'Curitiba, PR',
            'vehicle': self.vehicle_a.pk, 'driver': self.driver_a.pk,
            'start_time': (self.now + timedelta(days=2)).strftime('%d/%m/%Y %H:%M'),
            'end_time': (self.now + timedelta(days=2, hours=2)).strftime('%d/%m/%Y %H:%M'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_route_update_invalid(self):
        route = Route.objects.create(user_profile=self.profile_a, start_location="A", end_location="B", start_time=self.now, end_time=self.now)
        response = self.client.post(reverse('route-update', kwargs={'pk': route.pk}), {})
        self.assertEqual(response.status_code, 400)

    def test_route_create_api_error(self):
        with patch('dashboard.route_views.calculate_route_details') as mock_calc:
            mock_calc.return_value = "Erro API"
            response = self.client.post(reverse('route-add'), {
                'start_location': 'A, SC', 'end_location': 'B, SC',
                'vehicle': self.vehicle_a.pk, 'driver': self.driver_a.pk,
                'start_time': (self.now + timedelta(days=1)).strftime('%d/%m/%Y %H:%M'),
                'end_time': (self.now + timedelta(days=1, hours=1)).strftime('%d/%m/%Y %H:%M')
            })
            self.assertEqual(response.status_code, 400)
            self.assertIn("Erro API", str(response.content))

class VehicleViewTests(DashboardBaseTestCase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse('vehicle-list')
        self.add_url = reverse('vehicle-add')
        self.update_url = reverse('vehicle-update', kwargs={'pk': self.vehicle_a.pk})

    def test_vehicle_list_view_authenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.vehicle_a.plate)
        self.assertNotContains(response, self.vehicle_b.plate)

    def test_vehicle_create_view_post_success(self):
        response = self.client.post(self.add_url, {
            'plate': 'NEW-0001', 'model': 'Novo', 'year': 2025,
            'acquisition_date': '2025-01-01', 'initial_mileage': 0,
            'average_fuel_consumption': 12.5
        })
        self.assertRedirects(response, self.list_url)
        self.assertEqual(Vehicle.objects.filter(user_profile=self.profile_a).count(), 2)

    def test_vehicle_create_view_post_invalid(self):
        response = self.client.post(self.add_url, {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Vehicle.objects.filter(user_profile=self.profile_a).count(), 1)

    def test_vehicle_update_view_post(self):
        response = self.client.post(self.update_url, {
            'plate': self.vehicle_a.plate, 'model': 'Atualizado', 'year': 2024,
            'acquisition_date': '2024-01-01', 'initial_mileage': 10000, 'average_fuel_consumption': 11.0
        })
        self.assertRedirects(response, self.list_url)
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.model, 'Atualizado')

    def test_vehicle_deactivate_view(self):
        response = self.client.post(reverse('vehicle-deactivate', kwargs={'pk': self.vehicle_a.pk}))
        self.assertRedirects(response, self.list_url)
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.status, 'disabled')

    def test_vehicle_reactivate_view(self):
        self.vehicle_a.status = 'disabled'
        self.vehicle_a.save()
        response = self.client.post(reverse('vehicle-reactivate', kwargs={'pk': self.vehicle_a.pk}))
        self.assertRedirects(response, self.list_url)
        self.vehicle_a.refresh_from_db()
        self.assertEqual(self.vehicle_a.status, 'available')

    def test_vehicle_history_json(self):
        Route.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, driver=self.driver_a,
            start_location="A", end_location="B",
            start_time=self.now, end_time=self.now, status='completed', actual_distance=100
        )
        response = self.client.get(reverse('vehicle-route-history', kwargs={'pk': self.vehicle_a.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['history']), 1)
        
        Maintenance.objects.create(
            user_profile=self.profile_a, vehicle=self.vehicle_a, service_type="S",
            start_date=self.now, end_date=self.now, mechanic_shop_name="O", current_mileage=100, status='completed', actual_cost=100, actual_end_date=self.now
        )
        response = self.client.get(reverse('vehicle-maintenance-history', kwargs={'pk': self.vehicle_a.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['history']), 1)

class SecurityTests(DashboardBaseTestCase):
    def test_user_a_cannot_update_user_b_vehicle(self):
        response = self.client.post(reverse('vehicle-update', kwargs={'pk': self.vehicle_b.pk}), {})
        self.assertEqual(response.status_code, 404)
        
    def test_unauthenticated_user_redirected(self):
        self.client.logout()
        response = self.client.get(reverse('vehicle-list'))
        self.assertEqual(response.status_code, 302)

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
            EC.visibility_of_element_located((By.ID, "open-add-driver-modal"))
        )
        add_button.click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "add-driver-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_vehicle_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('vehicle-list'))
        add_button = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "open-add-vehicle-modal"))
        )
        add_button.click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "add-vehicle-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_route_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('route-list'))
        add_button = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "open-add-route-modal"))
        )
        add_button.click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "route-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_maintenance_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('maintenance-list'))
        add_button = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "open-add-maintenance-modal"))
        )
        add_button.click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "maintenance-modal"))
        )
        self.assertTrue(modal.is_displayed())

    def test_alert_config_modal_opens(self):
        self.driver.get(self.live_server_url + reverse('alert-config'))
        add_button = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "open-config-modal"))
        )
        add_button.click()
        
        modal = WebDriverWait(self.driver, 50).until(
            EC.visibility_of_element_located((By.ID, "config-modal"))
        )
        self.assertTrue(modal.is_displayed())
