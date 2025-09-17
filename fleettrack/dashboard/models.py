from django.db import models
from django.contrib.auth.models import User


class Driver(models.Model):
    full_name = models.CharField(max_length=100, verbose_name="Nome Completo")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    license_number = models.CharField(max_length=30, unique=True, verbose_name="Número da CNH")
    admission_date = models.DateField(verbose_name="Data de Admissão")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    demission_date = models.DateField(null=True, blank=True, verbose_name="Data de Demissão")

    def __str__(self):
        return self.full_name

class Vehicle(models.Model):
    STATUS_CHOICES = [
        ('available', 'Disponível'),
        ('on_route', 'Em Rota'),
        ('maintenance', 'Em Manutenção'),
        ('disabled', 'Desativado'),
    ]
    plate = models.CharField(max_length=10, unique=True, verbose_name="Placa")
    model = models.CharField(max_length=50, verbose_name="Modelo")
    year = models.PositiveIntegerField(verbose_name="Ano")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name="Status")
    mileage = models.PositiveIntegerField(verbose_name="Quilometragem")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Motorista")
    acquisition_date = models.DateField(verbose_name="Data de Aquisição")

    def __str__(self):
        return f"{self.model} - {self.plate}"

class Maintenance(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Agendada'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluída'),
    ]
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, verbose_name="Veículo")
    service_type = models.CharField(max_length=100, verbose_name="Tipo de Serviço")
    start_date = models.DateTimeField(verbose_name="Data de Início")
    end_date = models.DateTimeField(verbose_name="Data de Fim")
    mechanic_shop_name = models.CharField(max_length=100, verbose_name="Nome da Mecânica")
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Custo Estimado")
    current_mileage = models.PositiveIntegerField(verbose_name="Quilometragem Atual")
    notes = models.TextField(blank=True, verbose_name="Observações")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="Status")

    def __str__(self):
        return f"{self.service_type} - {self.vehicle.plate}"