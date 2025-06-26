from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class FuelStation(models.Model):
    """Fuel station with geocoded coordinates"""

    opis_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=2, db_index=True)
    retail_price = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )

    # Geocoded coordinates
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["retail_price"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state} (${self.retail_price})"

    @property
    def coordinates(self):
        return (float(self.latitude), float(self.longitude))
