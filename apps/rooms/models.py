"""
Rooms, Room Types, Amenities, Rate Plans, and Pricing models.
"""
import uuid
from django.db import models


class RoomAmenity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    icon = models.CharField(max_length=64, blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Room Amenity"
        verbose_name_plural = "Room Amenities"

    def __str__(self):
        return self.name


class RoomType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='room_types')
    name = models.CharField(max_length=128)
    code = models.SlugField(max_length=32)
    base_occupancy = models.PositiveIntegerField(default=2)
    max_occupancy = models.PositiveIntegerField(default=4)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    amenities = models.ManyToManyField(RoomAmenity, blank=True, related_name='room_types')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('property', 'code')
        ordering = ['base_price']

    def __str__(self):
        return f"{self.name} - {self.property.name}"


class Room(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('RESERVED', 'Reserved'),
        ('OCCUPIED', 'Occupied'),
        ('DIRTY', 'Dirty'),
        ('CLEANING', 'Cleaning'),
        ('INSPECTION', 'Inspection'),
        ('OUT_OF_ORDER', 'Out of Order'),
        ('MAINTENANCE', 'Maintenance'),
        ('BLOCKED', 'Blocked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='rooms')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')
    floor = models.ForeignKey('properties.Floor', on_delete=models.SET_NULL, null=True, blank=True, related_name='rooms')
    room_number = models.CharField(max_length=32, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='AVAILABLE', db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('property', 'room_number')
        ordering = ['room_number']

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.name}) - {self.property.name}"


class RatePlan(models.Model):
    MEAL_PLAN_CHOICES = [
        ('RO', 'Room Only'),
        ('BB', 'Bed & Breakfast'),
        ('HB', 'Half Board'),
        ('FB', 'Full Board'),
        ('AI', 'All Inclusive'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='rate_plans')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rate_plans')
    name = models.CharField(max_length=128)
    code = models.SlugField(max_length=32)
    meal_plan = models.CharField(max_length=4, choices=MEAL_PLAN_CHOICES, default='RO')
    cancellation_policy = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('property', 'room_type', 'code')

    def __str__(self):
        return f"{self.name} ({self.room_type.name})"


class RoomRate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE, related_name='rates')
    date = models.DateField(db_index=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('rate_plan', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.rate_plan.name} @ {self.date}: {self.rate}"
