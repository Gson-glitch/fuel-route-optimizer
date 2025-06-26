from unittest.mock import Mock

from fuel_optimizer.services import RouteOptimizationService


def route_optimization_service_is_ready():
    """Step to create route optimization service"""

    def step(context):
        context.service = RouteOptimizationService()

    return step


def us_locations_are_provided(start="New York, NY", end="Philadelphia, PA"):
    """Step to provide US locations for geocoding"""

    def step(context):
        context.start_location = start
        context.end_location = end
        context.start_coords = (40.7128, -74.0060)
        context.end_coords = (39.9526, -75.1652)

    return step


def short_route_is_configured():
    """Step to configure a short route (< 500 miles)"""

    def step(context):
        context.route_data = {
            "geometry": {"type": "LineString", "coordinates": []},
            "distance_miles": 95.0,
            "coordinates": [],
        }

    return step


def long_route_is_configured():
    """Step to configure a long route (> 500 miles)"""

    def step(context):
        context.route_data = {
            "geometry": {"type": "LineString", "coordinates": []},
            "distance_miles": 2800.0,
            "coordinates": [[-74.0, 40.7], [-118.2, 34.0]],
        }

    return step


def fuel_stations_are_available():
    """Step to mock fuel stations in database"""

    def step(context):
        mock_station = Mock()
        mock_station.name = "Test Station"
        mock_station.city = "Denver"
        mock_station.state = "CO"
        mock_station.retail_price = 3.50
        mock_station.coordinates = (39.7392, -104.9903)

        # Create proper mock queryset
        mock_queryset = Mock()
        mock_queryset.exists.return_value = True
        mock_queryset.__iter__ = Mock(return_value=iter([mock_station]))

        context.mock_queryset = mock_queryset
        context.mock_station = mock_station

    return step


def non_us_location_is_provided():
    """Step to provide non-US location"""

    def step(context):
        context.start_location = "Toronto, Canada"
        context.end_location = "New York, NY"

    return step


def invalid_location_is_provided():
    """Step to provide invalid location"""

    def step(context):
        context.start_location = "Invalid City"
        context.end_location = "Los Angeles, CA"

    return step
