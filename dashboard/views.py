from .core_views import DashboardView, UserProfileView
from .vehicle_views import (
    VehicleListView, VehicleCreateView, VehicleUpdateView,
    VehicleDeactivateView, VehicleReactivateView, 
    VehicleMaintenanceHistoryView, VehicleRouteHistoryView
)
from .driver_views import (
    DriverListView, DriverCreateView, DriverUpdateView, 
    DriverDeactivateView, DriverRouteHistoryView
)
from .maintenance_views import (
    MaintenanceCreateView, MaintenanceListView, MaintenanceUpdateView, 
    MaintenanceCancelView, MaintenanceCompleteView
)
from .route_views import (
    RouteCreateView, RouteListView, RouteUpdateView, 
    RouteCancelView, RouteReactivateView, RouteCompleteView
)
from .alert_views import AlertConfigView