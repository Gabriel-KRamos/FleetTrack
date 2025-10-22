from django.contrib import admin
from .models import Vehicle, Driver, Maintenance, Route

class RouteAdmin(admin.ModelAdmin):
    list_display = ('start_location', 'end_location', 'estimated_distance', 'status', 'vehicle', 'driver')
    list_filter = ('status',)
    search_fields = ('start_location', 'end_location', 'vehicle__plate', 'driver__full_name')

admin.site.register(Vehicle)
admin.site.register(Driver)
admin.site.register(Maintenance)
admin.site.register(Route, RouteAdmin)