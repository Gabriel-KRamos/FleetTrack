# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class SignUpForm(forms.ModelForm):
    # Campos extras que não estão no modelo User, como a confirmação de senha
    password = forms.CharField(widget=forms.PasswordInput(), label="Senha")
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Confirmar Senha")

    # Campo do nosso modelo de perfil
    company_name = forms.CharField(max_length=100, label="Nome da Empresa")

    class Meta:
        # Diz ao formulário para usar o modelo User como base
        model = User
        # Campos que queremos do modelo User
        fields = ['first_name', 'username', 'password']
        labels = {
            'first_name': 'Nome Completo',
            'username': 'Endereço de Email', # Usaremos o email como nome de usuário
        }

    def clean(self):
        # Método especial para validações customizadas
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            # Se as senhas não coincidirem, gera um erro de validação
            raise forms.ValidationError(
                "As senhas não coincidem. Por favor, tente novamente."
            )

        # Garante que o email (username) não esteja em uso
        if User.objects.filter(username=cleaned_data.get('username')).exists():
            raise forms.ValidationError(
                "Este endereço de email já está em uso."
            )

    def save(self, commit=True):
        # Sobrescrevemos o método save para lidar com nossos campos extras
        user = super().save(commit=False)
        # Criptografa a senha antes de salvar
        user.set_password(self.cleaned_data["password"])

        # O Django exige um email no campo de email, então copiamos o username
        user.email = user.username

        if commit:
            user.save()
            # Cria o perfil do usuário com o nome da empresa
            UserProfile.objects.create(
                user=user,
                company_name=self.cleaned_data.get('company_name')
            )
        return user
class DriverForm(forms.Form):
    """
    Formulário para criar e editar motoristas (usuários).
    Lida com campos de User e UserProfile.
    """
    full_name = forms.CharField(label="Nome Completo")
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(label="Telefone", required=False)
    license_number = forms.CharField(label="Número da CNH", required=False)

    # A senha só é obrigatória na criação
    password = forms.CharField(label="Senha (para novos motoristas)", widget=forms.PasswordInput, required=False)

    def clean_email(self):
        # Validação para garantir que o email não esteja duplicado (ignorando o usuário atual na edição)
        email = self.cleaned_data.get('email')
        # O 'instance' é injetado pela view durante a edição para sabermos qual usuário estamos editando
        user_instance = self.instance
        
        query = User.objects.filter(username=email)
        if user_instance:
            query = query.exclude(pk=user_instance.pk) # Exclui o próprio usuário da busca na edição

        if query.exists():
            raise forms.ValidationError("Este endereço de email já está em uso.")
        return email


class DeactivateDriverForm(forms.Form):
    demission_date = forms.DateField(
        label="Data de Demissão",
        widget=forms.DateInput(attrs={'type': 'text', 'class': 'datepicker', 'placeholder': 'dd/mm/aaaa'}),
        required=True
    )