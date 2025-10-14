# accounts/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100, blank=True)
    
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    license_number = models.CharField(max_length=30, blank=True, verbose_name="Número da CNH")
    demission_date = models.DateField(null=True, blank=True, verbose_name="Data de Demissão")

    def __str__(self):
        return self.user.username