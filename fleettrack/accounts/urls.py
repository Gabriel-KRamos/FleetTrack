# accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView # 1. Importe a TemplateView

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    
    path(
        'signup/', 
        TemplateView.as_view(template_name='accounts/signup.html'), 
        name='signup'
    ),
]