"""
Front Office and In-House Stay tracking models.
"""
from django.db import models
from common.tenancy.models import TenantScopedModel


class StayLog(TenantScopedModel):
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='stay_logs')
    reservation = models.OneToOneField('reservations.Reservation', on_delete=models.CASCADE, related_name='stay_log')
    guest = models.ForeignKey('guests.GuestProfile', on_delete=models.PROTECT)
    room = models.ForeignKey('rooms.Room', on_delete=models.PROTECT, related_name='stay_logs')
    
    check_in_time = models.DateTimeField(auto_now_add=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    
    is_id_verified = models.BooleanField(default=False)
    signature_url = models.URLField(blank=True)
    key_cards_issued = models.PositiveIntegerField(default=1)
    
    checked_in_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='checkins_handled')
    checked_out_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='checkouts_handled')

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Stay Log"
        verbose_name_plural = "Stay Logs"

    def __str__(self):
        return f"Stay: {self.guest.full_name} in Room {self.room.room_number} ({self.reservation.confirmation_code})"
