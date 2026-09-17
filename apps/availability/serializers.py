"""
Availability search serializers.
"""
from rest_framework import serializers


class AvailableRoomTypeSerializer(serializers.Serializer):
    room_type_id = serializers.UUIDField()
    name = serializers.CharField()
    code = serializers.CharField()
    base_occupancy = serializers.IntegerField()
    max_occupancy = serializers.IntegerField()
    nightly_rate = serializers.FloatField()
    total_nights = serializers.IntegerField()
    estimated_total = serializers.FloatField()


class AvailabilitySearchResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    property_id = serializers.UUIDField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    total_nights = serializers.IntegerField()
    available_room_types = AvailableRoomTypeSerializer(many=True)
