# dashboard/models.py
from django.db import models
from django.contrib.auth.models import User

class Vehicle(models.Model):
    """
    Representa um veículo na frota.
    """
    
    # Opções para o campo 'status'
    STATUS_CHOICES = [
        ('available', 'Disponível'),
        ('on_route', 'Em Rota'),
        ('maintenance', 'Em Manutenção'),
    ]

    plate = models.CharField(max_length=10, unique=True, verbose_name="Placa")
    model = models.CharField(max_length=50, verbose_name="Modelo")
    year = models.PositiveIntegerField(verbose_name="Ano")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name="Status")
    mileage = models.PositiveIntegerField(verbose_name="Quilometragem")
    
    # Relaciona o veículo a um motorista (usuário). Pode ser nulo se não houver motorista.
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Motorista")
    
    acquisition_date = models.DateField(verbose_name="Data de Aquisição")
    
    # Campos para a "exclusão suave" (soft delete)
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    deactivation_date = models.DateField(null=True, blank=True, verbose_name="Data de Desativação")

    def __str__(self):
        return f"{self.model} - {self.plate}"