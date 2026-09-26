"""
Multi-tenant base models and scoped managers.
Implements Recipe B from the Multi-Tenant SaaS Architecture Blueprint.
"""
import uuid
from django.db import models
from django.utils import timezone
from common.context import get_current_tenant


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeletableManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def unscoped(self):
        return super().get_queryset()


class SoftDeletableModel(models.Model):
    is_active = models.BooleanField(default=True, db_index=True)

    objects = SoftDeletableManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def restore(self):
        self.is_active = True
        self.save(update_fields=["is_active", "updated_at"])


class TenantScopedQuerySet(models.QuerySet):
    def for_organization(self, organization):
        if not organization:
            return self.none()
        return self.filter(organization=organization)

    def for_user(self, user):
        if not user or not user.is_authenticated:
            return self.none()
        if getattr(user, 'is_superuser', False) or getattr(user, 'role', '') == 'SUPER_ADMIN':
            return self.all()
        if hasattr(user, 'organization') and user.organization:
            return self.filter(organization=user.organization)
        return self.none()


class TenantScopedManager(models.Manager):
    def get_queryset(self):
        qs = TenantScopedQuerySet(self.model, using=self._db)
        tenant = get_current_tenant()
        if tenant is not None:
            return qs.filter(organization=tenant)
        return qs

    def for_organization(self, organization):
        return TenantScopedQuerySet(self.model, using=self._db).for_organization(organization)

    def for_user(self, user):
        return TenantScopedQuerySet(self.model, using=self._db).for_user(user)

    def unscoped(self):
        """Bypasses tenant filtering for background tasks or SuperAdmin analytics."""
        return TenantScopedQuerySet(self.model, using=self._db)


TenantManager = TenantScopedManager


class TenantScopedModel(UUIDModel, TimeStampedModel, SoftDeletableModel):
    """
    Abstract base model enforcing UUID primary key, organization scoping,
    and audit timestamps with automatic thread-safe tenant assignment.
    """
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        db_index=True,
        help_text="The tenant/organization that owns this record."
    )

    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    @property
    def tenant(self):
        """Alias for organization in line with SaaS Blueprint."""
        return self.organization

    @tenant.setter
    def tenant(self, value):
        self.organization = value

    def save(self, *args, **kwargs):
        # Auto-inject tenant from thread context if not explicitly set
        if not self.organization_id:
            current = get_current_tenant()
            if current:
                self.organization = current
        super().save(*args, **kwargs)
