"""
Room Availability and Inventory Tracking.
"""
import uuid
from django.db import models


class RoomAvailability(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='availability_records')
    room_type = models.ForeignKey('rooms.RoomType', on_delete=models.CASCADE, related_name='availability_records')
    date = models.DateField(db_index=True)
    
    total_rooms = models.PositiveIntegerField(default=0)
    available_rooms = models.PositiveIntegerField(default=0)
    locked_rooms = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('property', 'room_type', 'date')
        ordering = ['date']
        indexes = [
            models.Index(fields=['property', 'room_type', 'date']),
        ]

    def __str__(self):
        return f"{self.property.code} - {self.room_type.code} [{self.date}]: {self.available_rooms}/{self.total_rooms} Free"
