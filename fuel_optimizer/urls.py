from django.urls import path

from .views import HealthCheckView, RouteOptimizationView

urlpatterns = [
    path("optimize/", RouteOptimizationView.as_view(), name="optimize"),
    path("health/", HealthCheckView.as_view(), name="health"),
]
