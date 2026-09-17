"""
Guest Profile and CRM entities.
"""
from django.db import models
from common.tenancy.models import TenantScopedModel


class GuestProfile(TenantScopedModel):
    ID_TYPE_CHOICES = [
        ('PASSPORT', 'Passport'),
        ('NATIONAL_ID', 'National ID Card'),
        ('DRIVING_LICENSE', 'Driving License'),
        ('OTHER', 'Other'),
    ]

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guest_profile'
    )
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    email = models.EmailField(db_index=True)
    phone_number = models.CharField(max_length=32, blank=True)
    
    id_document_type = models.CharField(max_length=32, choices=ID_TYPE_CHOICES, default='PASSPORT')
    id_document_number = models.CharField(max_length=64, blank=True)
    nationality = models.CharField(max_length=64, blank=True)
    vip_status = models.BooleanField(default=False, db_index=True)
    
    # Guest preferences: room/floor, bed type, dietary, smoking preference, pillow type
    preferences = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Guest Profile"
        verbose_name_plural = "Guest Profiles"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
