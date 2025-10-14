from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Driver, Vehicle
from datetime import date

class VehicleViewsTestCase(TestCase):
    """Suite de testes para as views relacionadas a Veículos."""


    def setUp(self):

        self.user = User.objects.create_user(username='testuser', password='password123')


        self.client = Client()


        self.driver = Driver.objects.create(
            full_name='Motorista de Teste',
            email='teste@email.com',
            license_number='123456789',
            admission_date=date(2024, 1, 1)
        )

        self.vehicle = Vehicle.objects.create(
            plate='TST-1234',
            model='Modelo de Teste',
            year=2024,
            mileage=10000,
            driver=self.driver,
            acquisition_date=date(2024, 1, 1)
        )

        self.list_url = reverse('vehicle-list')


    def test_vehicle_list_view_redirects_for_not_logged_in_user(self):
        """
        Teste 1: Verifica se um utilizador não autenticado é redirecionado.
        As suas páginas do dashboard exigem login, então este teste garante
        que a proteção está a funcionar.
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
        Este é um teste de conteúdo. Ele garante que os dados do banco de dados
        estão a ser corretamente apresentados no template.
        """
        self.client.login(username='testuser', password='password123')

        response = self.client.get(self.list_url)

        self.assertContains(response, self.vehicle.plate) 
        self.assertContains(response, self.vehicle.model)
        self.assertContains(response, self.driver.full_name)