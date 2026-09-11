from rest_framework import serializers

class AirportSerializer(serializers.Serializer):
    code = serializers.CharField()
    city = serializers.CharField()
    airport = serializers.CharField()


class FlightSegmentRequestSerializer(serializers.Serializer):
    origin = serializers.CharField()
    destination = serializers.CharField()
    departure_date = serializers.CharField()


class FlightSearchRequestSerializer(serializers.Serializer):
    """
        Validates the *shape* of the incoming request only (types present).
        Business validation (airport existence, date ordering, pax limits,
        multi-city segment rules) is done by flight.services.validators,
        which is shared with the existing web view so both entry points
        enforce identical rules.
    """

    trip_type = serializers.ChoiceField(choices=["oneway", "roundtrip", "multicity"])
    origin = serializers.CharField(required=False, allow_blank=True)
    destination = serializers.CharField(required=False, allow_blank=True)
    departure_date = serializers.CharField(required=False, allow_blank=True)
    return_date = serializers.CharField(required=False, allow_blank=True)
    segments = FlightSegmentRequestSerializer(many=True, required=False)
    adults = serializers.IntegerField(required=False, default=1)
    children = serializers.IntegerField(required=False, default=0)
    infants = serializers.IntegerField(required=False, default=0)
    cabin_class = serializers.CharField(required=False, default="economy")
    special_fare = serializers.CharField(required=False, default="regular")


class BaggageInfoSerializer(serializers.Serializer):
    cabin = serializers.CharField(allow_null=True)
    checkin = serializers.CharField(allow_null=True)


class FareOptionSerializer(serializers.Serializer):
    fare_id = serializers.CharField(allow_null=True)
    fare_type = serializers.CharField(allow_null=True)
    cabin_class = serializers.CharField(allow_null=True)
    booking_class = serializers.CharField(allow_null=True)
    fare_basis = serializers.CharField(allow_null=True)
    base_fare = serializers.FloatField(allow_null=True)
    taxes = serializers.FloatField(allow_null=True)
    total_fare = serializers.FloatField(allow_null=True)
    net_fare = serializers.FloatField(allow_null=True)
    currency = serializers.CharField(allow_null=True)
    seats_available = serializers.IntegerField(allow_null=True)
    meal_included = serializers.BooleanField(allow_null=True)
    refundable = serializers.BooleanField(allow_null=True)
    refund_type_code = serializers.IntegerField(allow_null=True)
    baggage = BaggageInfoSerializer(allow_null=True)
    fare_rules_reference = serializers.CharField(allow_null=True)


class FlightSegmentSerializer(serializers.Serializer):
    
    segment_id = serializers.CharField(allow_null=True)
    airline_code = serializers.CharField(allow_null=True)
    airline_name = serializers.CharField(allow_null=True)
    is_lcc = serializers.BooleanField(allow_null=True)
    flight_number = serializers.CharField(allow_null=True)
    aircraft_type = serializers.CharField(allow_null=True)
    origin = serializers.CharField(allow_null=True)
    origin_city = serializers.CharField(allow_null=True)
    origin_terminal = serializers.CharField(allow_null=True)
    destination = serializers.CharField(allow_null=True)
    destination_city = serializers.CharField(allow_null=True)
    destination_terminal = serializers.CharField(allow_null=True)
    departure_time = serializers.CharField(allow_null=True)
    arrival_time = serializers.CharField(allow_null=True)
    duration_minutes = serializers.IntegerField(allow_null=True)
    technical_stops = serializers.IntegerField(allow_null=True)
    stopovers = serializers.ListField(child=serializers.DictField(), required=False)


class NormalizedFlightSerializer(serializers.Serializer):
    provider = serializers.CharField()
    provider_reference = serializers.CharField(allow_null=True)
    leg_label = serializers.CharField(allow_null=True)
    segments = FlightSegmentSerializer(many=True)
    stops = serializers.IntegerField(allow_null=True)
    total_duration_minutes = serializers.IntegerField(allow_null=True)
    fares = FareOptionSerializer(many=True)
