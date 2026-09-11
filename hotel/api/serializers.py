from rest_framework import serializers


class HotelDestinationCitySerializer(serializers.Serializer):
    """One city suggestion in the GET /api/v1/hotels/destinations/ response."""

    city = serializers.CharField()
    country = serializers.CharField()
    hotel_count = serializers.IntegerField()


class HotelDestinationHotelSerializer(serializers.Serializer):
    """One hotel suggestion in the GET /api/v1/hotels/destinations/ response."""

    tj_hotel_id = serializers.CharField()
    name = serializers.CharField()
    city = serializers.CharField()
