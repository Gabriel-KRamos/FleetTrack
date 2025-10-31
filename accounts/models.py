from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100, blank=True)
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ", null=True, blank=True)

    def __str__(self):
        return self.user.username