from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from datetime import date
from .models import Vehicle, Driver, Maintenance 
from .forms import VehicleForm, DriverForm, MaintenanceForm


class DashboardView(LoginRequiredMixin, View):
    # Esta view foi alterada para carregar os formulários dos modais
    def get(self, request):
        # Passa os formulários vazios para os modais do dashboard
        context = {
            'maintenance_form': MaintenanceForm(),
            # Adicione aqui outros formulários se precisar deles nos modais do dashboard
        }
        return render(request, 'dashboard/dashboard.html', context)


class VehicleListView(LoginRequiredMixin, View):
    def get(self, request):
        vehicles = Vehicle.objects.all().order_by('status', '-year')
        maintenances = Maintenance.objects.all().order_by('-start_date')
        context = {
            'vehicles': vehicles,
            'add_form': VehicleForm(),
            'maintenances': maintenances,
        }
        return render(request, 'dashboard/vehicles.html', context)

class VehicleCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo adicionado com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
        return redirect('vehicle-list')

class VehicleUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo atualizado com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{vehicle.plate} - {form.fields[field].label}: {error}")
        return redirect('vehicle-list')

class VehicleDeactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle.status = 'disabled'
        vehicle.save()
        messages.success(request, f'Veículo {vehicle.plate} desativado com sucesso.')
        return redirect('vehicle-list')

# --- VIEWS DE MOTORISTAS ---

class DriverListView(LoginRequiredMixin, View):
    def get(self, request):
        drivers = Driver.objects.all().order_by('-is_active', 'full_name')
        context = {
            'drivers': drivers,
            'add_form': DriverForm(),
        }
        return render(request, 'dashboard/drivers.html', context)

class DriverCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista adicionado com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro ao adicionar motorista: {error}")
        return redirect('driver-list')

class DriverUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista atualizado com sucesso!')
        return redirect('driver-list')

class DriverDeactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        driver.is_active = False
        driver.demission_date = date.today()
        driver.save()
        messages.success(request, f'Motorista {driver.full_name} desativado com sucesso.')
        return redirect('driver-list')

# --- VIEW DE MANUTENÇÃO ---

class MaintenanceCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Manutenção agendada com sucesso!')
        else:
            # Em caso de erro, é útil exibir os erros específicos
            error_text = ""
            for field, errors in form.errors.items():
                error_text += f"{field}: {', '.join(errors)} "
            messages.error(request, f"Erro no agendamento: {error_text}")
        return redirect('dashboard')