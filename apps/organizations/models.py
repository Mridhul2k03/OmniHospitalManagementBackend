"""
Organization / Tenant entity for multi-tenancy.
"""
import uuid
from django.db import models


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    code = models.SlugField(max_length=64, unique=True, help_text="Unique organizational slug/subdomain identifier")
    legal_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    subscription_tier = models.CharField(
        max_length=32,
        choices=[
            ('STARTER', 'Starter'),
            ('PROFESSIONAL', 'Professional'),
            ('ENTERPRISE', 'Enterprise'),
        ],
        default='ENTERPRISE'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
