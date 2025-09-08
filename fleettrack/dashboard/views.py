# dashboard/views.py (VERSÃO CORRIGIDA)

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User  # ADICIONADO: Import do modelo User
from django.contrib import messages
from .models import Vehicle
from .forms import VehicleForm, DeactivateVehicleForm
from accounts.forms import DriverForm, DeactivateDriverForm

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

# A View de Lista agora faz a busca no banco e envia os formulários para os modais
class VehicleListView(LoginRequiredMixin, View):
    def get(self, request):
        # Busca apenas os veículos ativos, ordenados pelo ano
        vehicles = Vehicle.objects.filter(is_active=True).order_by('-year')
        
        # Formulários vazios para os modais de "Adicionar" e "Desativar"
        add_form = VehicleForm()
        deactivate_form = DeactivateVehicleForm()
        
        context = {
            'vehicles': vehicles,
            'add_form': add_form,
            'deactivate_form': deactivate_form
        }
        return render(request, 'dashboard/vehicles.html', context)

# View para CRIAR um novo veículo
class VehicleCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo adicionado com sucesso!')
        else:
            # Transforma os erros do formulário em mensagens
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
        return redirect('vehicle-list')

# View para ATUALIZAR um veículo existente
class VehicleUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        # Passamos a 'instance' para o formulário saber qual veículo editar
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo atualizado com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{vehicle.plate} - {form.fields[field].label}: {error}")
        return redirect('vehicle-list')

# View para DESATIVAR um veículo
class VehicleDeactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        form = DeactivateVehicleForm(request.POST)

        if form.is_valid():
            vehicle.is_active = False
            vehicle.deactivation_date = form.cleaned_data['deactivation_date']
            vehicle.save()
            messages.success(request, f'Veículo {vehicle.plate} desativado com sucesso.')
        else:
            messages.error(request, 'Data de desativação inválida.')
            
        return redirect('vehicle-list')

# REMOVIDA: Classe DriverListView duplicada e simples que estava aqui.

# Versão correta e final da DriverListView
class DriverListView(LoginRequiredMixin, View):
    def get(self, request):
        # Busca usuários ativos que não sejam superusuários
        drivers = User.objects.filter(is_active=True, is_superuser=False)
        
        context = {
            'drivers': drivers,
            'add_form': DriverForm(), # Formulário para o modal de adicionar
            'deactivate_form': DeactivateDriverForm(), # Formulário para o modal de desativar
        }
        return render(request, 'dashboard/drivers.html', context)