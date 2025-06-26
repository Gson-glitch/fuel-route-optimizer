from django.core.validators import RegexValidator
from rest_framework import serializers

INVALID_LOCATION = (
    "Location must contain only letters, spaces, commas, periods, and hyphens"
)


class RouteOptimizationRequestSerializer(serializers.Serializer):
    start = serializers.CharField(
        max_length=200,
        help_text="Starting location (e.g., 'New York, NY')",
        validators=[
            RegexValidator(regex=r"^[a-zA-Z\s,.-]+$", message=INVALID_LOCATION)
        ],
    )
    end = serializers.CharField(
        max_length=200,
        help_text="Destination location (e.g., 'Los Angeles, CA')",
        validators=[
            RegexValidator(regex=r"^[a-zA-Z\s,.-]+$", message=INVALID_LOCATION)
        ],
    )

    def validate(self, data):
        if data["start"].lower().strip() == data["end"].lower().strip():
            raise serializers.ValidationError(
                "Start and end locations must be different"
            )
        return data
