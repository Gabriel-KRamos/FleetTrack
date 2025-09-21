from django import forms
from .models import Vehicle, Driver, Maintenance, Route

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        # O campo 'status' foi REMOVIDO daqui, pois será automático
        fields = ['plate', 'model', 'year', 'acquisition_date', 'mileage']
        widgets = {
            'acquisition_date': forms.DateInput(attrs={'type': 'text', 'class': 'datepicker', 'placeholder': 'dd/mm/aaaa'}),
            'plate': forms.TextInput(attrs={'placeholder': 'ABC-1234'}),
            'model': forms.TextInput(attrs={'placeholder': 'ex: Ford Transit'}),
            'year': forms.NumberInput(attrs={'placeholder': 'ex: 2022'}),
            'mileage': forms.NumberInput(attrs={'placeholder': 'ex: 50000'}),
        }


class MaintenanceForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        label="Início",
        input_formats=['%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'text', 'class': 'datetimepicker', 'placeholder': 'dd/mm/aaaa --:--'})
    )
    end_date = forms.DateTimeField(
        label="Fim",
        input_formats=['%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'text', 'class': 'datetimepicker', 'placeholder': 'dd/mm/aaaa --:--'})
    )

    class Meta:
        model = Maintenance
        fields = [
            'vehicle', 'service_type', 'start_date', 'end_date', 
            'mechanic_shop_name', 'estimated_cost', 'current_mileage', 'notes'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.exclude(status='disabled')


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['full_name', 'email', 'phone_number', 'license_number', 'admission_date']
        widgets = {
            'admission_date': forms.DateInput(
                attrs={'type': 'text', 'class': 'datepicker', 'placeholder': 'dd/mm/aaaa'}
            ),
        }


# FORMULÁRIO DE ROTA CORRIGIDO
class RouteForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        label="Início Programado",
        input_formats=['%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'text', 'class': 'datetimepicker', 'placeholder': 'dd/mm/aaaa --:--'})
    )
    end_time = forms.DateTimeField(
        label="Fim Programado",
        input_formats=['%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'text', 'class': 'datetimepicker', 'placeholder': 'dd/mm/aaaa --:--'})
    )

    class Meta:
        model = Route
        fields = ['start_location', 'end_location', 'vehicle', 'driver', 'start_time', 'end_time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.exclude(status='disabled')
        self.fields['driver'].queryset = Driver.objects.filter(is_active=True)