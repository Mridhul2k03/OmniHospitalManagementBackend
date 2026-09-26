import uuid
from django.db import models
from apps.organizations.models import Organization
from apps.rooms.models import RoomType


class DemandBand(models.TextChoices):
    LOW = "low", "Low Demand"
    NORMAL = "normal", "Normal Demand"
    HIGH = "high", "High Demand"
    SURGE = "surge", "Surge Demand"


class DynamicPricingRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="pricing_rules")
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name="pricing_rules")
    demand_band = models.CharField(max_length=20, choices=DemandBand.choices, default=DemandBand.NORMAL)
    surge_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    is_manual_override = models.BooleanField(default=False)
    manual_override_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    override_reason = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.room_type.name} ({self.demand_band}) - {self.calculated_rate}"

    @property
    def calculated_rate(self):
        if self.is_manual_override and self.manual_override_rate:
            return float(self.manual_override_rate)
        base = getattr(self.room_type, 'base_price', getattr(self.room_type, 'base_rate', 250.0))
        return round(float(base) * float(self.surge_multiplier), 2)
