from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Driver, Vehicle, Route
from datetime import date
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile 

class VehicleViewsTestCase(TestCase):
    """Suite de testes para as views relacionadas a Veículos."""


    def setUp(self):

        self.user = User.objects.create_user(username='testuser', password='password123')

        self.user_profile = UserProfile.objects.create(
            user=self.user, 
            company_name="Empresa de Teste"
        )

        self.client = Client()

        self.driver = Driver.objects.create(
            user_profile=self.user_profile,
            full_name='Motorista de Teste',
            email='teste@email.com',
            license_number='123456789',
            admission_date=date(2024, 1, 1)
        )

        self.vehicle = Vehicle.objects.create(
            user_profile=self.user_profile,
            plate='TST-1234',
            model='Modelo de Teste',
            year=2024,
            initial_mileage=10000, 
            acquisition_date=date(2024, 1, 1)
        )


        now = timezone.now()
        Route.objects.create(
            user_profile=self.user_profile,
            vehicle=self.vehicle,
            driver=self.driver,
            start_location="Origem Teste",
            end_location="Destino Teste",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status='in_progress'
        )


        self.list_url = reverse('vehicle-list')


    def test_vehicle_list_view_redirects_for_not_logged_in_user(self):
        """
        Teste 1: Verifica se um utilizador não autenticado é redirecionado.
        """
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/accounts/login/?next={self.list_url}')


    def test_vehicle_list_view_for_logged_in_user(self):
        """
        Teste 2: Verifica se um utilizador autenticado acede à página com sucesso.
        """
        self.client.login(username='testuser', password='password123')

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'dashboard/vehicles.html')


    def test_vehicle_list_view_displays_vehicle_information(self):
        """
        Teste 3: Verifica se a página exibe as informações do veículo que criámos.
        """
        self.client.login(username='testuser', password='password123')

        response = self.client.get(self.list_url)

        self.assertContains(response, self.vehicle.plate, status_code=200) 
        self.assertContains(response, self.vehicle.model)
        
        self.assertContains(response, self.driver.full_name)