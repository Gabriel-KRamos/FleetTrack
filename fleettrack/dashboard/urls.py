from django.urls import path
from .views import DashboardView, VehicleListView, DriverListView

urlpatterns = [
        path('', DashboardView.as_view(), name='dashboard'),
        path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
        path('drivers/', DriverListView.as_view(), name='driver-list'),
]