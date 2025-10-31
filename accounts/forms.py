from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
import re
from django.contrib.auth import password_validation

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Senha")
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Confirmar Senha")
    company_name = forms.CharField(max_length=100, label="Nome da Empresa")
    cnpj = forms.CharField(max_length=18, label="CNPJ")

    class Meta:
        model = User
        fields = ['first_name', 'username', 'password']
        labels = {
            'first_name': 'Nome Completo',
            'username': 'Endereço de Email',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este endereço de email já está em uso.")
        return username

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        if not cnpj:
            raise forms.ValidationError("Este campo é obrigatório.")
        
        cleaned_cnpj = re.sub(r'[^\d]', '', cnpj)
        
        if len(cleaned_cnpj) != 14:
             raise forms.ValidationError("O CNPJ deve conter 14 dígitos.")
        
        if UserProfile.objects.filter(cnpj=cleaned_cnpj).exists():
            raise forms.ValidationError("Este CNPJ já está em uso.")
        
        return cleaned_cnpj

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            password_validation.validate_password(password, self.instance)
        except forms.ValidationError as error:
            self.add_error('password', error)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("As senhas não coincidem. Por favor, tente novamente.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.email = user.username
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                company_name=self.cleaned_data.get('company_name'),
                cnpj=self.cleaned_data.get('cnpj')
            )
        return user