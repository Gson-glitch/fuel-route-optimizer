import hashlib
import logging
from typing import Dict, List, Optional, Tuple

import openrouteservice
from django.conf import settings
from django.core.cache import cache
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import ArcGIS

from .models import FuelStation

logger = logging.getLogger("fuel_optimizer")


class RouteOptimizationService:
    """Route optimization service"""

    def __init__(self):
        self.ors_client = openrouteservice.Client(key=settings.OPENROUTE_API_KEY)
        self.geocoder = ArcGIS(timeout=10)

    def optimize_route(self, start_location: str, end_location: str) -> Dict:
        """Main optimization method"""
        try:
            # Geocode locations
            start_coords = self.geocode(start_location)
            end_coords = self.geocode(end_location)

            # Get route
            route_data = self.get_route(start_coords, end_coords)

            # Find fuel stops
            fuel_stops = self.find_fuel_stops(route_data)

            # Calculate costs
            result = self.calculate_costs(route_data, fuel_stops)
            logger.info(
                f"Route optimized: {start_location} -> {end_location}, "
                f"{len(fuel_stops)} stops, ${result['total_fuel_cost']:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Route optimization failed: {e}")
            raise

    def geocode(self, address: str) -> Tuple[float, float]:
        """Geocode address and validate it's in the USA using reverse geocoding"""
        cache_key = (
            f"geocode_{hashlib.md5(address.lower().strip().encode()).hexdigest()}"
        )
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        try:
            # First, geocode the address to get coordinates
            location = self.geocoder.geocode(address, timeout=10)

            if not location:
                raise ValueError(f"Location not found: {address}")

            coords = (location.latitude, location.longitude)

            # Reverse geocode to get country information
            reverse_location = self.geocoder.reverse(coords, timeout=5)
            country_code = reverse_location[0].rsplit(",", maxsplit=1)[-1].strip()
            usa_codes = ["USA", "US", "UNITED STATES", "UNITED STATES OF AMERICA"]

            if country_code.upper() not in usa_codes:
                raise ValueError(
                    f"Location must be within the USA. '{address}' is in {country_code}"
                )

            # Cache the result
            cache.set(cache_key, coords, settings.GEOCODING_CACHE_TIMEOUT)
            return coords

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding failed for '{address}': {e}")
            raise ValueError("Unable to find location")
        except ValueError as e:
            if "Location must be within the USA" in str(
                e
            ) or "Location not found" in str(e):
                raise  # Re-raise specific errors
            else:
                logger.error(f"Unexpected geocoding error for '{address}': {e}")
                raise ValueError("Geocoding service unavailable")
        except Exception as e:
            # If reverse geocoding fails or any other error, treat as non-US
            logger.error(f"Unexpected geocoding error for '{address}': {e}")
            raise ValueError(f"Location must be within the USA: {address}")

    def get_route(
        self, start_coords: Tuple[float, float], end_coords: Tuple[float, float]
    ) -> Dict:
        """Get route between two points"""
        route_key = f"{start_coords}:{end_coords}"
        cache_key = f"route_{hashlib.md5(route_key.encode()).hexdigest()}"
        route = cache.get(cache_key)

        if route:
            return route

        try:
            coordinates = [
                [start_coords[1], start_coords[0]],  # OpenRouteService wants (lng, lat)
                [end_coords[1], end_coords[0]],
            ]

            routes = self.ors_client.directions(
                coordinates=coordinates, profile="driving-car", format="geojson"
            )

            if not routes.get("features"):
                raise ValueError("No route found")

            feature = routes["features"][0]
            properties = feature["properties"]

            route = {
                "geometry": feature["geometry"],
                "distance_miles": properties["segments"][0]["distance"]
                * settings.METERS_TO_MILES,
                "coordinates": feature["geometry"]["coordinates"],
            }

            cache.set(cache_key, route, settings.ROUTE_CACHE_TIMEOUT)
            return route

        except openrouteservice.exceptions.ApiError as e:
            logger.error(f"OpenRouteService API error: {e}")
            raise ValueError("Unable to calculate route")
        except Exception as e:
            logger.error(f"Unexpected routing error: {e}")
            raise ValueError("Routing service unavailable")

    def find_fuel_stops(self, route_data: Dict) -> List[Dict]:
        """Find optimal fuel stops along route"""
        distance_miles = route_data["distance_miles"]

        # No stops needed for short trips
        if distance_miles <= settings.VEHICLE_RANGE_MILES:
            return []

        try:
            # Get all stations within route bounding box
            coordinates = route_data["coordinates"]
            min_lat = min(coord[1] for coord in coordinates)
            max_lat = max(coord[1] for coord in coordinates)
            min_lng = min(coord[0] for coord in coordinates)
            max_lng = max(coord[0] for coord in coordinates)

            stations = FuelStation.objects.filter(
                latitude__gte=min_lat,
                latitude__lte=max_lat,
                longitude__gte=min_lng,
                longitude__lte=max_lng,
            ).order_by("retail_price")

            if not stations.exists():
                logger.warning("No fuel stations found in route area")
                return []

            # Calculate number of fuel stops needed
            stops_needed = max(1, int(distance_miles / settings.VEHICLE_RANGE_MILES))

            # Find the cheapest station for each stop
            fuel_stops = []
            for _ in range(stops_needed):
                station = self.find_cheapest_station(stations)
                if station:
                    fuel_stops.append(
                        {
                            "name": station.name,
                            "city": station.city,
                            "state": station.state,
                            "price": float(station.retail_price),
                            "coordinates": list(station.coordinates),
                        }
                    )

            return fuel_stops

        except Exception as e:
            logger.error(f"Error finding fuel stops: {e}")
            return []

    def find_cheapest_station(self, stations) -> Optional[FuelStation]:
        """Find cheapest fuel station from available stations"""
        cheapest, min_price = None, float("inf")
        for st in stations:
            if st.retail_price < min_price:
                cheapest, min_price = st, st.retail_price
        return cheapest

    def calculate_costs(self, route_data: Dict, fuel_stops: List[Dict]) -> Dict:
        """Calculate trip costs"""
        distance_miles = route_data["distance_miles"]
        total_gallons = distance_miles / settings.VEHICLE_MPG

        if not fuel_stops:
            # No stops → no cost
            total_cost = 0.0
        else:
            avg_price = sum(stop["price"] for stop in fuel_stops) / len(fuel_stops)
            total_cost = total_gallons * avg_price

        return {
            "route_geometry": route_data["geometry"],
            "fuel_stops": fuel_stops,
            "total_distance_miles": round(distance_miles, 1),
            "total_fuel_cost": round(total_cost, 2),
            "estimated_gallons": round(total_gallons, 1),
            "stops_count": len(fuel_stops),
        }
