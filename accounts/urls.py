from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    SignUpView,
    DriverCreateView,
    DriverUpdateView,
    DriverDeactivateView
)

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('drivers/add/', DriverCreateView.as_view(), name='driver-add'),
    path('drivers/<int:pk>/update/', DriverUpdateView.as_view(), name='driver-update'),
    path('drivers/<int:pk>/deactivate/', DriverDeactivateView.as_view(), name='driver-deactivate'),
]