from django.contrib import admin

from .models import FuelStation


@admin.register(FuelStation)
class FuelStationAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "state", "retail_price"]
    list_filter = ["state"]
    search_fields = ["name", "city"]
