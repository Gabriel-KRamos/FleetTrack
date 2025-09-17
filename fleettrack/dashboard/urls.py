from django.urls import path
from .views import (
    DashboardView,
    VehicleListView,
    VehicleCreateView,
    VehicleUpdateView,
    VehicleDeactivateView,
    DriverListView,
    DriverCreateView,
    DriverUpdateView,
    DriverDeactivateView,
    MaintenanceCreateView
)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/add/', VehicleCreateView.as_view(), name='vehicle-add'),
    path('vehicles/<int:pk>/update/', VehicleUpdateView.as_view(), name='vehicle-update'),
    path('vehicles/<int:pk>/deactivate/', VehicleDeactivateView.as_view(), name='vehicle-deactivate'),
    path('drivers/', DriverListView.as_view(), name='driver-list'),
    path('drivers/add/', DriverCreateView.as_view(), name='driver-add'),
    path('drivers/<int:pk>/update/', DriverUpdateView.as_view(), name='driver-update'),
    path('drivers/<int:pk>/deactivate/', DriverDeactivateView.as_view(), name='driver-deactivate'),
    path('maintenance/add/', MaintenanceCreateView.as_view(), name='maintenance-add'),
]