
from django.urls import path
from .views import (
    DashboardView,
    VehicleListView,
    DriverListView,
    VehicleCreateView,
    VehicleUpdateView,
    VehicleDeactivateView
)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    
    # URLs de Veículos
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/add/', VehicleCreateView.as_view(), name='vehicle-add'),
    path('vehicles/<int:pk>/update/', VehicleUpdateView.as_view(), name='vehicle-update'),
    path('vehicles/<int:pk>/deactivate/', VehicleDeactivateView.as_view(), name='vehicle-deactivate'),

    # URL da Lista de Motoristas
    path('drivers/', DriverListView.as_view(), name='driver-list'),
]