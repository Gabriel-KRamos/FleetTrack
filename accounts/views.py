# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignUpForm, DriverForm, DeactivateDriverForm
from .models import UserProfile

class SignUpView(View):
    # Método para lidar com requisições GET (quando o usuário acessa a página)
    def get(self, request):
        form = SignUpForm()
        return render(request, 'accounts/signup.html', {'form': form})

    # Método para lidar com requisições POST (quando o usuário envia o formulário)
    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # Adiciona uma mensagem de sucesso
            messages.success(request, 'Cadastro realizado com sucesso! Por favor, faça o login.')
            # Redireciona para a página de login
            return redirect('login')

        # Se o formulário não for válido, renderiza a página novamente com os erros
        return render(request, 'accounts/signup.html', {'form': form})
class DriverCreateView(View):
    def post(self, request):
        form = DriverForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if not data.get('password'):
                messages.error(request, 'O campo de senha é obrigatório para novos motoristas.')
                return redirect('driver-list')

            user = User.objects.create_user(
                username=data['email'],
                email=data['email'],
                first_name=data['full_name'],
                password=data['password']
            )
            UserProfile.objects.create(
                user=user,
                phone_number=data['phone_number'],
                license_number=data['license_number']
            )
            messages.success(request, 'Motorista adicionado com sucesso!')
        else:
            # Lidar com erros de formulário
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
        return redirect('driver-list')


class DriverUpdateView(View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = DriverForm(request.POST)
        form.instance = user # Passa a instância do usuário para a validação do formulário

        if form.is_valid():
            data = form.cleaned_data
            user.username = data['email']
            user.email = data['email']
            user.first_name = data['full_name']
            # Opcional: alterar senha se o campo for preenchido
            if data.get('password'):
                user.set_password(data['password'])
            user.save()

            # Atualiza ou cria o perfil
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone_number = data['phone_number']
            profile.license_number = data['license_number']
            profile.save()
            
            messages.success(request, 'Motorista atualizado com sucesso!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{user.first_name} - {form.fields[field].label}: {error}")
        return redirect('driver-list')


class DriverDeactivateView(View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = DeactivateDriverForm(request.POST)

        if form.is_valid():
            user.is_active = False
            user.save()
            
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.demission_date = form.cleaned_data['demission_date']
            profile.save()
            
            messages.success(request, f'Motorista {user.first_name} desativado com sucesso.')
        else:
            messages.error(request, 'Data de demissão inválida.')
            
        return redirect('driver-list')