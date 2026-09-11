from django.contrib import admin
from flight.models import Airport

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    
    list_display = ("code", "city", "airport_name", "country", "is_popular", "is_active")
    list_filter = ("is_active", "is_popular", "country")
    search_fields = ("code", "city", "airport_name")