from rest_framework import serializers
from .models import DynamicPricingRule


class DynamicPricingRuleSerializer(serializers.ModelSerializer):
    roomTypeId = serializers.CharField(source="room_type.id", read_only=True)
    roomTypeName = serializers.CharField(source="room_type.name", read_only=True)
    baseRate = serializers.DecimalField(source="room_type.base_price", max_digits=10, decimal_places=2, read_only=True)
    calculatedRate = serializers.SerializerMethodField()
    demandBand = serializers.CharField(source="demand_band")
    occupancyPace = serializers.SerializerMethodField()
    isManualOverride = serializers.BooleanField(source="is_manual_override")
    manualOverrideRate = serializers.DecimalField(source="manual_override_rate", max_digits=10, decimal_places=2, allow_null=True)
    overrideReason = serializers.CharField(source="override_reason", read_only=True)

    class Meta:
        model = DynamicPricingRule
        fields = [
            "id", "roomTypeId", "roomTypeName", "baseRate", "calculatedRate",
            "demandBand", "occupancyPace", "isManualOverride", "manualOverrideRate",
            "overrideReason",
        ]

    def get_calculatedRate(self, obj):
        return obj.calculated_rate

    def get_occupancyPace(self, obj):
        pace_map = {
            "surge": "94% Booked (High Velocity)",
            "high": "82% Booked",
            "normal": "65% Booked",
            "low": "38% Booked (Promotional Pace)"
        }
        return pace_map.get(obj.demand_band, "60% Booked")
