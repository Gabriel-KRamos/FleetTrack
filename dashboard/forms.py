import re
from django import forms
from .models import Vehicle, Driver, Maintenance, Route
from django.db.models import Q

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['plate', 'model', 'year', 'acquisition_date', 'initial_mileage', 'average_fuel_consumption']
        widgets = {
            'acquisition_date': forms.DateInput(attrs={'type': 'text', 'class': 'datepicker', 'placeholder': 'dd/mm/aaaa'}),
            'plate': forms.TextInput(attrs={'placeholder': 'ABC-1234'}),
            'model': forms.TextInput(attrs={'placeholder': 'ex: Ford Transit'}),
            'year': forms.NumberInput(attrs={'placeholder': 'ex: 2022'}),
            'initial_mileage': forms.NumberInput(attrs={'placeholder': 'ex: 50000'}),
            'average_fuel_consumption': forms.NumberInput(attrs={'placeholder': 'Ex: 10.5'}),
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
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
            'current_mileage': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.exclude(status='disabled')

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        vehicle = cleaned_data.get("vehicle")

        if start_date and end_date and vehicle:
            conflicting_routes = Route.objects.filter(
                vehicle=vehicle,
                start_time__lt=end_date,
                end_time__gt=start_date
            ).exclude(status__in=['completed', 'canceled'])
            
            if conflicting_routes.exists():
                raise forms.ValidationError(
                    f"Conflito: O veículo {vehicle.plate} já tem uma rota agendada ou em andamento neste período."
                )

        return cleaned_data

class MaintenanceCompletionForm(forms.ModelForm):
    actual_end_date = forms.DateTimeField(
        label="Data de Conclusão Real",
        input_formats=['%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'text', 'class': 'datetimepicker', 'placeholder': 'dd/mm/aaaa --:--'})
    )
    class Meta:
        model = Maintenance
        fields = ['actual_cost', 'actual_end_date']
        labels = {
            'actual_cost': 'Custo Final'
        }


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['full_name', 'email', 'phone_number', 'license_number', 'admission_date']
        widgets = {
            'admission_date': forms.DateInput(
                attrs={'type': 'text', 'class': 'datepicker', 'placeholder': 'dd/mm/aaaa'}
            ),
        }

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
        
        widgets = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['vehicle'].queryset = Vehicle.objects.exclude(status='disabled').filter(average_fuel_consumption__isnull=False)

        self.fields['driver'].queryset = Driver.objects.filter(is_active=True)

    def clean_location(self, location_data):
        pattern = re.compile(r'^.+,\s*[a-zA-Z]{2}$')
        if location_data and not pattern.match(location_data.strip()):
            raise forms.ValidationError(
                "Formato inválido. Use 'Cidade, UF'. Ex: Joinville, SC"
            )
        return location_data

    def clean_start_location(self):
        start_location = self.cleaned_data.get('start_location')
        return self.clean_location(start_location)

    def clean_end_location(self):
        end_location = self.cleaned_data.get('end_location')
        return self.clean_location(end_location)

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        vehicle = cleaned_data.get("vehicle")
        driver = cleaned_data.get("driver")

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("A data de fim deve ser posterior à data de início.")

            if vehicle:
                conflicting_routes = Route.objects.filter(
                    vehicle=vehicle,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exclude(pk=self.instance.pk if self.instance else None).exclude(status__in=['completed', 'canceled'])
                
                if conflicting_routes.exists():
                    raise forms.ValidationError(
                        f"Conflito: O veículo {vehicle.plate} já está agendado para outra rota neste período."
                    )
                
                conflicting_maintenances = Maintenance.objects.filter(
                    vehicle=vehicle,
                    start_date__lt=end_time,
                    end_date__gt=start_time
                ).exclude(status__in=['completed', 'canceled'])
                
                if conflicting_maintenances.exists():
                    raise forms.ValidationError(
                        f"Conflito: O veículo {vehicle.plate} está agendado para manutenção neste período."
                    )

            if driver:
                conflicting_driver_routes = Route.objects.filter(
                    driver=driver,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exclude(pk=self.instance.pk if self.instance else None).exclude(status__in=['completed', 'canceled'])
                
                if conflicting_driver_routes.exists():
                    raise forms.ValidationError(
                        f"Conflito: O motorista {driver.full_name} já está alocado a outra rota neste período."
                    )
        return cleaned_data


class RouteCompletionForm(forms.ModelForm):
    actual_distance = forms.DecimalField(
        label="Distância Real da Viagem (km)", 
        required=True, 
        widget=forms.NumberInput(attrs={'placeholder': 'Ex: 1150.5'})
    )
    class Meta:
        model = Route
        fields = ['actual_distance']