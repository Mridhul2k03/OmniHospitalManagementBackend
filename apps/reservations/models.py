"""
Reservation and Stay lifecycle models.
"""
import uuid
import builtins
from django.db import models
from common.tenancy.models import TenantScopedModel


class Reservation(TenantScopedModel):
    SOURCE_CHOICES = [
        ('DIRECT', 'Direct Website'),
        ('GUEST_APP', 'Guest Mobile App'),
        ('WALK_IN', 'Walk-in'),
        ('PHONE', 'Phone Booking'),
        ('EMAIL', 'Email Booking'),
        ('OTA_BOOKING_COM', 'Booking.com'),
        ('OTA_AGODA', 'Agoda'),
        ('OTA_EXPEDIA', 'Expedia'),
        ('CORPORATE', 'Corporate Partner'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment / Guarantee'),
        ('CONFIRMED', 'Confirmed'),
        ('CHECKED_IN', 'Checked In'),
        ('IN_HOUSE', 'In-House'),
        ('CHECKED_OUT', 'Checked Out'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    ]

    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='reservations')
    confirmation_code = models.CharField(max_length=32, unique=True, db_index=True)
    guest = models.ForeignKey('guests.GuestProfile', on_delete=models.PROTECT, related_name='reservations')
    
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, default='DIRECT')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    check_in_date = models.DateField(db_index=True)
    check_out_date = models.DateField(db_index=True)
    total_adults = models.PositiveIntegerField(default=1)
    total_children = models.PositiveIntegerField(default=0)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    
    special_requests = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=128, blank=True, db_index=True)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        indexes = [
            models.Index(fields=['property', 'status', 'check_in_date']),
        ]

    def __str__(self):
        return f"{self.confirmation_code} - {self.guest.full_name} ({self.status})"

    @builtins.property
    def total_nights(self):
        return (self.check_out_date - self.check_in_date).days


class ReservationRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='reservation_rooms')
    room_type = models.ForeignKey('rooms.RoomType', on_delete=models.PROTECT, related_name='reservation_rooms')
    allocated_room = models.ForeignKey('rooms.Room', on_delete=models.SET_NULL, null=True, blank=True, related_name='reservation_rooms')
    nightly_rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        room_label = self.allocated_room.room_number if self.allocated_room else "Unassigned"
        return f"{self.reservation.confirmation_code} - {self.room_type.name} (Room: {room_label})"
