import re
from django import forms
from .models import Vehicle, Driver, Maintenance, Route, AlertConfiguration
from django.db.models import Q
from django.forms import modelformset_factory
from django.contrib.auth.models import User
from accounts.models import UserProfile

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
    SERVICE_CHOICES = [
        ('', 'Selecione um tipo de serviço...'),
        ('Revisão Geral', 'Revisão Geral'),
        ('Troca de Óleo e Filtros', 'Troca de Óleo e Filtros'),
        ('Alinhamento e Balanceamento', 'Alinhamento e Balanceamento'),
        ('Troca de Pneus', 'Troca de Pneus'),
        ('Revisão dos Freios', 'Revisão dos Freios'),
        ('Troca da Correia Dentada', 'Troca da Correia Dentada'),
        ('Outro', 'Outro (Especificar)'),
    ]

    service_choice = forms.ChoiceField(
        choices=SERVICE_CHOICES,
        label="Tipo de Serviço",
        required=False,
        widget=forms.Select(attrs={'id': 'id_service_choice'})
    )

    service_type_other = forms.CharField(
        label="Especifique o Serviço",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Especifique o tipo de serviço', 'id': 'id_service_type_other'})
    )

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
            'vehicle',
            'service_choice',
            'service_type_other',
            'start_date',
            'end_date',
            'mechanic_shop_name',
            'estimated_cost',
            'current_mileage'
        ]
        exclude = ['service_type', 'status', 'actual_cost', 'actual_end_date', 'notes', 'user_profile']
        widgets = {
            'current_mileage': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)
        
        if user_profile:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(user_profile=user_profile).exclude(status='disabled')
        else:
            self.fields['vehicle'].queryset = Vehicle.objects.none()

        if self.instance and self.instance.pk:
            service_type = self.instance.service_type
            choice_values = [choice[0] for choice in self.SERVICE_CHOICES]
            if service_type in choice_values:
                self.initial['service_choice'] = service_type
            else:
                self.initial['service_choice'] = 'Outro'
                self.initial['service_type_other'] = service_type

    def clean(self):
        cleaned_data = super().clean()
        service_choice = cleaned_data.get("service_choice")
        service_type_other = cleaned_data.get("service_type_other")
        vehicle = cleaned_data.get("vehicle")

        final_service_type = ""
        if service_choice == 'Outro':
            if not service_type_other:
                self.add_error('service_type_other', "Você deve especificar o tipo de serviço ao selecionar 'Outro'.")
            else:
                final_service_type = service_type_other
        elif service_choice:
            final_service_type = service_choice
        else:
            self.add_error('service_choice', "Este campo é obrigatório.")

        cleaned_data['service_type'] = final_service_type

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and vehicle:
            conflicting_routes = Route.objects.filter(
                vehicle=vehicle,
                start_time__lt=end_date,
                end_time__gt=start_date
            ).exclude(status__in=['completed', 'canceled'])

            if self.instance and self.instance.pk:
                 conflicting_routes = conflicting_routes.exclude(pk=self.instance.pk)

            if conflicting_routes.exists():
                raise forms.ValidationError(
                    f"Conflito: O veículo {vehicle.plate} já tem uma rota agendada ou em andamento neste período."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.service_type = self.cleaned_data['service_type']
        if commit:
            instance.save()
        return instance

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
        fields = ['full_name', 'email', 'license_number', 'admission_date']
        widgets = {
            'admission_date': forms.DateInput(
                attrs={'type': 'text', 'class': 'datepicker', 'placeholder': 'dd/mm/aaaa'}
            ),
            'full_name': forms.TextInput(attrs={'placeholder': 'Nome completo do motorista'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@exemplo.com'}),
            'license_number': forms.TextInput(attrs={'placeholder': 'XXX.XXX.XXX-XX', 'maxlength': '14'}),
        }

    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number')
        if not license_number:
            raise forms.ValidationError("Este campo é obrigatório.")
        
        cleaned_license = re.sub(r'[^0-9]', '', license_number)
        
        if len(cleaned_license) != 11:
            raise forms.ValidationError("A CNH deve conter exatamente 11 dígitos numéricos.")
        
        query = Driver.objects.filter(license_number=cleaned_license, is_active=True)
        
        if self.instance and self.instance.user_profile:
            query = query.filter(user_profile=self.instance.user_profile)

        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise forms.ValidationError("Esta CNH já está registada num motorista ativo.")
        return cleaned_license

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Este campo é obrigatório.")
        
        query = Driver.objects.filter(email=email, is_active=True)

        if self.instance and self.instance.user_profile:
            query = query.filter(user_profile=self.instance.user_profile)

        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise forms.ValidationError("Este endereço de email já está em uso por um motorista ativo.")
        return email


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
        exclude = ['user_profile']
        widgets = {}

    def __init__(self, *args, **kwargs):
        user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)
        
        if user_profile:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(user_profile=user_profile).exclude(status='disabled').filter(average_fuel_consumption__isnull=False)
            self.fields['driver'].queryset = Driver.objects.filter(user_profile=user_profile, is_active=True)
        else:
            self.fields['vehicle'].queryset = Vehicle.objects.none()
            self.fields['driver'].queryset = Driver.objects.none()


    def clean_location(self, location_data):
        pattern = re.compile(r'^.+,\s*[a-zA-Z]{2}$')
        if location_data and not pattern.match(location_data.strip()):
            raise forms.ValidationError("Formato inválido. Use 'Cidade, UF'. Ex: Joinville, SC")
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
                    vehicle=vehicle, start_time__lt=end_time, end_time__gt=start_time
                ).exclude(pk=self.instance.pk if self.instance else None).exclude(status__in=['completed', 'canceled'])
                if conflicting_routes.exists():
                    raise forms.ValidationError(f"Conflito: O veículo {vehicle.plate} já está agendado para outra rota neste período.")
                conflicting_maintenances = Maintenance.objects.filter(
                    vehicle=vehicle, start_date__lt=end_time, end_date__gt=start_time
                ).exclude(status__in=['completed', 'canceled'])
                if conflicting_maintenances.exists():
                    raise forms.ValidationError(f"Conflito: O veículo {vehicle.plate} está agendado para manutenção neste período.")
            if driver:
                conflicting_driver_routes = Route.objects.filter(
                    driver=driver, start_time__lt=end_time, end_time__gt=start_time
                ).exclude(pk=self.instance.pk if self.instance else None).exclude(status__in=['completed', 'canceled'])
                if conflicting_driver_routes.exists():
                    raise forms.ValidationError(f"Conflito: O motorista {driver.full_name} já está alocado a outra rota neste período.")
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

class BaseAlertConfigurationForm(forms.ModelForm):
    class Meta:
        model = AlertConfiguration
        fields = ['service_type', 'km_threshold', 'days_threshold', 'is_active', 'priority']
        widgets = {
            'service_type': forms.HiddenInput(),
            'km_threshold': forms.NumberInput(attrs={'placeholder': 'KM', 'style': 'width: 80px;'}),
            'days_threshold': forms.NumberInput(attrs={'placeholder': 'Dias', 'style': 'width: 80px;'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'alert-active-checkbox'}),
            'priority': forms.Select(attrs={'style': 'padding: 0.4rem; min-width: 90px;'}),
        }
        labels = {
            'km_threshold': '',
            'days_threshold': '',
            'is_active': '',
            'priority': '',
        }

AlertConfigurationFormSet = modelformset_factory(
    AlertConfiguration,
    form=BaseAlertConfigurationForm,
    fields=['service_type', 'km_threshold', 'days_threshold', 'is_active', 'priority'],
    extra=0,
    can_delete=False
)

class UserProfileEditForm(forms.ModelForm):
    username = forms.EmailField(label="Endereço de Email (Login)", required=True)

    class Meta:
        model = User
        fields = ['first_name', 'username']
        labels = {
            'first_name': 'Nome Completo',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este endereço de email já está em uso por outro usuário.")
        self.instance.email = username
        return username

class CompanyProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['company_name', 'cnpj']
        labels = {
            'company_name': 'Nome da Empresa',
            'cnpj': 'CNPJ'
        }
    
    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        if not cnpj:
            raise forms.ValidationError("Este campo é obrigatório.")
        
        cleaned_cnpj = re.sub(r'[^\d]', '', cnpj)
        
        if len(cleaned_cnpj) != 14:
             raise forms.ValidationError("O CNPJ deve conter 14 dígitos.")
        
        query = UserProfile.objects.filter(cnpj=cleaned_cnpj)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise forms.ValidationError("Este CNPJ já está em uso por outra empresa.")
        
        return cleaned_cnpj