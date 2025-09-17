from django import forms
from .models import Vehicle, Driver, Maintenance

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['plate', 'model', 'year', 'acquisition_date', 'mileage', 'status']

class MaintenanceForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        label="Início",
        input_formats=['%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'type': 'text', 
            'class': 'datetimepicker', 
            'placeholder': 'dd/mm/aaaa --:--'
        })
    )
    end_date = forms.DateTimeField(
        label="Fim",
        input_formats=['%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'type': 'text', 
            'class': 'datetimepicker', 
            'placeholder': 'dd/mm/aaaa --:--'
        })
    )

    class Meta:
        model = Maintenance
        fields = [
            'vehicle', 'service_type', 'start_date', 'end_date', 
            'mechanic_shop_name', 'estimated_cost', 'current_mileage', 'notes'
        ]
        widgets = { 
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_vehicles = Vehicle.objects.exclude(status='disabled')
        self.fields['vehicle'].queryset = active_vehicles

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['full_name', 'email', 'phone_number', 'license_number', 'admission_date']
        labels = {
            'full_name': 'Nome Completo',
            'email': 'Email',
            'phone_number': 'Telefone',
            'license_number': 'Número da CNH',
            'admission_date': 'Data de Admissão',
        }
        widgets = {
            'admission_date': forms.DateInput(
                attrs={'type': 'text', 'class': 'datepicker', 'placeholder': 'dd/mm/aaaa'}
            ),
            'full_name': forms.TextInput(attrs={'placeholder': 'ex: João da Silva'}),
            'email': forms.EmailInput(attrs={'placeholder': 'ex: joao.silva@email.com'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'ex: (47) 99999-9999'}),
            'license_number': forms.TextInput(attrs={'placeholder': 'Insira o número da CNH'}),
        }