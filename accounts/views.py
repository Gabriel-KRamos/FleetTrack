from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login
from django.contrib import messages
from .forms import SignUpForm

class SignUpView(View):
    def get(self, request):
        form = SignUpForm()
        return render(request, 'accounts/signup.html', {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado com sucesso! Por favor, faça o login.')
            return redirect('login')
        return render(request, 'accounts/signup.html', {'form': form})