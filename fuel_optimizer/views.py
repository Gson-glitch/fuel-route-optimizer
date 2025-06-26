import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RouteOptimizationRequestSerializer
from .services import RouteOptimizationService

logger = logging.getLogger("fuel_optimizer")


class RouteOptimizationView(APIView):
    """Route optimization endpoint"""

    def post(self, request):
        """Optimize route with fuel stops"""
        serializer = RouteOptimizationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = RouteOptimizationService()
            result = service.optimize_route(
                serializer.validated_data["start"], serializer.validated_data["end"]
            )
            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class HealthCheckView(APIView):
    """Health check endpoint"""

    def get(self, request):
        return Response({"status": "healthy"})
