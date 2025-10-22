from django.db import models
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.text import slugify

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
    initial_mileage = models.PositiveIntegerField(verbose_name="Quilometragem Inicial")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Motorista")
    acquisition_date = models.DateField(verbose_name="Data de Aquisição")
    average_fuel_consumption = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name="Consumo Médio (Km/L)"
    )

    @property
    def mileage(self):
        completed_routes_mileage = self.route_set.filter(status='completed').aggregate(
            total=Sum(Coalesce('actual_distance', 'estimated_distance'), output_field=models.DecimalField())
        )['total'] or 0
        
        return self.initial_mileage + int(completed_routes_mileage)

    def __str__(self):
        return f"{self.model} - {self.plate}"

    @property
    def dynamic_status(self):
        now = timezone.now()
        if self.status == 'disabled': return "Desativado"
        active_maintenance = Q(start_date__lte=now, end_date__gte=now)
        overdue_maintenance = Q(end_date__lt=now)
        is_in_maintenance = self.maintenance_set.filter(
            (active_maintenance | overdue_maintenance),
            status__in=['scheduled', 'in_progress']
        ).exists()
        if is_in_maintenance: return "Em Manutenção"
        if self.route_set.filter(
            start_time__lte=now, end_time__gte=now
        ).exclude(
            status__in=['completed', 'canceled']
        ).exists(): return "Em Rota"
        return "Disponível"

    @property
    def dynamic_status_slug(self):
        status = self.dynamic_status
        if status == "Em Manutenção": return 'maintenance'
        if status == "Em Rota": return 'on_route'
        if status == "Desativado": return 'disabled'
        return 'available'

    @property
    def current_route_driver(self):
        now = timezone.now()
        current_route = self.route_set.filter(
            start_time__lte=now, end_time__gte=now
        ).exclude(
            status__in=['completed', 'canceled']
        ).select_related('driver').first()
        if current_route and current_route.driver: return current_route.driver
        return None

class Maintenance(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Agendada'), ('in_progress', 'Em Andamento'),
        ('completed', 'Concluída'), ('canceled', 'Cancelada'),
    ]
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, verbose_name="Veículo")
    service_type = models.CharField(max_length=100, verbose_name="Tipo de Serviço")
    start_date = models.DateTimeField(verbose_name="Data de Início")
    end_date = models.DateTimeField(verbose_name="Data de Fim")
    mechanic_shop_name = models.CharField(max_length=100, verbose_name="Nome da Mecânica")
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Custo Estimado")
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Custo Final")
    actual_end_date = models.DateTimeField(null=True, blank=True, verbose_name="Data de Conclusão Real")
    current_mileage = models.PositiveIntegerField(verbose_name="Quilometragem Atual")
    notes = models.TextField(blank=True, verbose_name="Observações")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="Status")

    def __str__(self): return f"{self.service_type} - {self.vehicle.plate}"
    @property
    def dynamic_status(self):
        now = timezone.now()
        if self.status in ['completed', 'canceled']: return self.get_status_display()
        if self.end_date < now: return "Atrasada"
        if self.start_date <= now < self.end_date: return "Em Andamento"
        return "Agendada"
    @property
    def dynamic_status_slug(self):
        status = self.dynamic_status
        if status == "Atrasada": return "overdue"
        if status == "Em Andamento": return "in_progress"
        if status == "Agendada": return "scheduled"
        if status == "Concluída": return "completed"
        if status == "Cancelada": return "canceled"
        return slugify(status)

class Route(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Agendada'), ('in_progress', 'Em Andamento'),
        ('completed', 'Concluída'), ('canceled', 'Cancelada'),
    ]
    start_location = models.CharField(max_length=255, verbose_name="Local de Partida")
    end_location = models.CharField(max_length=255, verbose_name="Local de Chegada")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, verbose_name="Veículo")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, verbose_name="Motorista")
    start_time = models.DateTimeField(verbose_name="Início Programado")
    end_time = models.DateTimeField(verbose_name="Fim Programado")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="Status")
    estimated_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Distância Estimada (km)")
    actual_distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Distância Real (km)")
    fuel_price_per_liter = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Preço Combustível (R$/L)")
    estimated_toll_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Custo Pedágio (Est.)")

    @property
    def dynamic_status(self):
        now = timezone.now()
        if self.status in ['completed', 'canceled']: return self.get_status_display()
        if self.end_time < now: return "Concluída"
        if self.start_time <= now < self.end_time: return "Em Andamento"
        return "Agendada"
    @property
    def dynamic_status_slug(self):
        status = self.dynamic_status
        if status == "Em Andamento": return "in_progress"
        if status == "Agendada": return "scheduled"
        if status == "Concluída": return "completed"
        if status == "Cancelada": return "canceled"
        return slugify(status)
    @property
    def progress_percentage(self):
        if self.status == 'completed': return 100
        if self.status == 'canceled': return 0
        now = timezone.now()
        if now >= self.end_time: return 100
        if now < self.start_time: return 0
        total_duration = (self.end_time - self.start_time).total_seconds()
        if total_duration <= 0: return 100
        elapsed_duration = (now - self.start_time).total_seconds()
        percentage = (elapsed_duration / total_duration) * 100
        return min(100, int(percentage))
    @property
    def estimated_fuel_cost(self):
        if self.estimated_distance and self.vehicle and self.vehicle.average_fuel_consumption and self.fuel_price_per_liter:
            try:
                liters_needed = self.estimated_distance / self.vehicle.average_fuel_consumption
                return liters_needed * self.fuel_price_per_liter
            except: return None
        return None
    def __str__(self): return f"Rota de {self.start_location} para {self.end_location} ({self.start_time.strftime('%d/%m/%Y')})"
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.actual_distance:
            self.status = 'scheduled' if timezone.now() < self.start_time else 'in_progress'
        super().save(*args, **kwargs)