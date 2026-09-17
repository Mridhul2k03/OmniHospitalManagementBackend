"""
Property, Building, and Floor models representing physical hotel infrastructure.
"""
import uuid
from django.db import models
from common.tenancy.models import TenantScopedModel


class Property(TenantScopedModel):
    PROPERTY_TYPE_CHOICES = [
        ('HOTEL', 'Hotel'),
        ('RESORT', 'Resort'),
        ('BOUTIQUE', 'Boutique Hotel'),
        ('BUSINESS_HOTEL', 'Business Hotel'),
        ('MOTEL', 'Motel'),
        ('VILLA', 'Villa / Apartments'),
    ]

    region = models.ForeignKey(
        'corporate.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='properties'
    )
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=64, help_text="Property code e.g. GRAND-NYC")
    property_type = models.CharField(max_length=32, choices=PROPERTY_TYPE_CHOICES, default='HOTEL')
    
    address = models.TextField()
    city = models.CharField(max_length=128)
    state = models.CharField(max_length=128)
    country = models.CharField(max_length=64, default='US')
    postal_code = models.CharField(max_length=32)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=32)
    currency = models.CharField(max_length=3, default='USD')
    check_in_time = models.TimeField(default='14:00')
    check_out_time = models.TimeField(default='11:00')

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Property"
        verbose_name_plural = "Properties"
        unique_together = ('organization', 'code')

    def __str__(self):
        return f"{self.name} [{self.code}]"


class Building(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='buildings')
    name = models.CharField(max_length=128)
    code = models.SlugField(max_length=32)

    class Meta:
        unique_together = ('property', 'code')

    def __str__(self):
        return f"{self.name} ({self.property.name})"


class Floor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='floors')
    floor_number = models.IntegerField()
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ['floor_number']
        unique_together = ('building', 'floor_number')

    def __str__(self):
        return f"{self.name} (Floor {self.floor_number}) - {self.building.name}"
