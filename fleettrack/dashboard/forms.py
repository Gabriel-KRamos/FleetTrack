# dashboard/forms.py
from django import forms
from .models import Vehicle

class VehicleForm(forms.ModelForm):
    """
    Formulário para criar e editar veículos.
    """
    class Meta:
        model = Vehicle
        # Campos que o usuário poderá preencher
        fields = ['plate', 'model', 'year', 'acquisition_date', 'status']
        
        # Rótulos em português para os campos
        labels = {
            'plate': 'Placa',
            'model': 'Modelo',
            'year': 'Ano',
            'acquisition_date': 'Data de Aquisição',
            'status': 'Status Inicial',
        }
        
        # Adiciona classes CSS e placeholders aos campos do formulário
        widgets = {
            'acquisition_date': forms.DateInput(
                attrs={'type': 'text', 'class': 'datepicker', 'placeholder': 'dd/mm/aaaa'}
            ),
            'plate': forms.TextInput(attrs={'placeholder': 'ABC-1234'}),
            'model': forms.TextInput(attrs={'placeholder': 'ex: Ford Transit'}),
            'year': forms.NumberInput(attrs={'placeholder': 'ex: 2022'}),
        }

class DeactivateVehicleForm(forms.Form):
    """
    Formulário simples para a data de desativação.
    """
    deactivation_date = forms.DateField(
        label="Data de Desativação",
        widget=forms.DateInput(attrs={'type': 'text', 'class': 'datepicker', 'placeholder': 'dd/mm/aaaa'}),
        required=True
    )