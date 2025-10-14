from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Senha")
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Confirmar Senha")

    company_name = forms.CharField(max_length=100, label="Nome da Empresa")

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
            raise forms.ValidationError(
                "Este endereço de email já está em uso."
            )
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError(
                "As senhas não coincidem. Por favor, tente novamente."
            )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        user.email = user.username

        if commit:
            user.save()
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

    password = forms.CharField(label="Senha (para novos motoristas)", widget=forms.PasswordInput, required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
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