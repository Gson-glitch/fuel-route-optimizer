import unittest
from unittest.mock import Mock, patch

from givenpy import given, then, when
from hamcrest import assert_that, empty, equal_to, greater_than, is_
from .steps import (
    fuel_stations_are_available,
    invalid_location_is_provided,
    long_route_is_configured,
    non_us_location_is_provided,
    route_optimization_service_is_ready,
    short_route_is_configured,
    us_locations_are_provided,
)


class FuelRouteOptimizerTest(unittest.TestCase):

    def test_short_route_should_not_require_fuel_stops(self):
        """Test that short routes don't need fuel stops"""
        with given(
            [
                route_optimization_service_is_ready(),
                us_locations_are_provided(),
                short_route_is_configured(),
            ]
        ) as context:

            with (
                patch.object(context.service, "geocode") as mock_geocode,
                patch.object(context.service, "get_route") as mock_get_route,
            ):

                mock_geocode.side_effect = [context.start_coords, context.end_coords]
                mock_get_route.return_value = context.route_data

                with when("I optimize the route"):
                    context.result = context.service.optimize_route(
                        context.start_location, context.end_location
                    )

                with then("it should return no fuel stops"):
                    assert_that(context.result["fuel_stops"], is_(empty()))
                    assert_that(context.result["total_fuel_cost"], is_(equal_to(0.0)))
                    assert_that(context.result["stops_count"], is_(equal_to(0)))

    def test_long_route_should_require_fuel_stops(self):
        """Test that long routes require fuel stops"""
        with given(
            [
                route_optimization_service_is_ready(),
                us_locations_are_provided("New York, NY", "Los Angeles, CA"),
                long_route_is_configured(),
                fuel_stations_are_available(),
            ]
        ) as context:

            with (
                patch.object(context.service, "geocode") as mock_geocode,
                patch.object(context.service, "get_route") as mock_get_route,
                patch("fuel_optimizer.services.FuelStation") as mock_fuel_station,
            ):

                mock_geocode.side_effect = [context.start_coords, (34.0522, -118.2437)]
                mock_get_route.return_value = context.route_data
                mock_fuel_station.objects.filter.return_value.order_by.return_value = (
                    context.mock_queryset
                )

                with when("I optimize the long route"):
                    context.result = context.service.optimize_route(
                        context.start_location, context.end_location
                    )

                with then("it should return fuel stops"):
                    assert_that(context.result["stops_count"], is_(greater_than(0)))
                    assert_that(
                        context.result["total_fuel_cost"], is_(greater_than(0.0))
                    )

    def test_non_us_location_should_be_rejected(self):
        """Test that non-US locations are rejected"""
        with given(
            [route_optimization_service_is_ready(), non_us_location_is_provided()]
        ) as context:

            with patch.object(context.service, "geocode") as mock_geocode:
                mock_geocode.side_effect = ValueError(
                    "Location must be within the USA. 'Toronto, Canada' is in CAN"
                )

                with when("I try to optimize route with non-US location"):
                    context.exception = None
                    try:
                        context.service.optimize_route(
                            context.start_location, context.end_location
                        )
                    except ValueError as e:
                        context.exception = e

                with then("it should reject the location"):
                    assert_that(
                        str(context.exception),
                        is_(
                            equal_to(
                                "Location must be within the USA. 'Toronto, Canada' is in CAN"
                            )
                        ),
                    )

    def test_invalid_location_should_be_rejected(self):
        """Test that invalid locations are rejected"""
        with given(
            [route_optimization_service_is_ready(), invalid_location_is_provided()]
        ) as context:

            with patch.object(context.service, "geocode") as mock_geocode:
                mock_geocode.side_effect = ValueError(
                    "Location not found: Invalid City"
                )

                with when("I try to optimize route with invalid location"):
                    context.exception = None
                    try:
                        context.service.optimize_route(
                            context.start_location, context.end_location
                        )
                    except ValueError as e:
                        context.exception = e

                with then("it should reject the location"):
                    assert_that(
                        str(context.exception),
                        is_(equal_to("Location not found: Invalid City")),
                    )

    def test_cheapest_station_should_be_selected(self):
        """Test that the cheapest station is selected from available options"""
        with given([route_optimization_service_is_ready()]) as context:

            # Create mock stations with different prices
            expensive_station = Mock()
            expensive_station.retail_price = 3.75
            expensive_station.name = "Expensive Station"

            cheap_station = Mock()
            cheap_station.retail_price = 3.25
            cheap_station.name = "Cheap Station"

            context.stations = [expensive_station, cheap_station]

            with when("I find the cheapest station"):
                context.result = context.service.find_cheapest_station(context.stations)

            with then("it should select the cheapest one"):
                assert_that(context.result.name, is_(equal_to("Cheap Station")))
                assert_that(context.result.retail_price, is_(equal_to(3.25)))


if __name__ == "__main__":
    unittest.main()
