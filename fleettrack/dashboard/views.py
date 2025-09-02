from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(TemplateView):
    template_name = 'dashboard/dashboard.html'

class VehicleListView(TemplateView):
    template_name = 'dashboard/vehicles.html'

class DriverListView(TemplateView):
    template_name = 'dashboard/drivers.html'