"""
Multi-tenant base models and scoped managers.
"""
import uuid
from django.db import models


class TenantScopedQuerySet(models.QuerySet):
    def for_organization(self, organization):
        if not organization:
            return self.none()
        return self.filter(organization=organization)

    def for_user(self, user):
        if not user or not user.is_authenticated:
            return self.none()
        if user.is_superuser:
            return self.all()
        if hasattr(user, 'organization') and user.organization:
            return self.filter(organization=user.organization)
        return self.none()


class TenantScopedManager(models.Manager):
    def get_queryset(self):
        return TenantScopedQuerySet(self.model, using=self._db)

    def for_organization(self, organization):
        return self.get_queryset().for_organization(organization)

    def for_user(self, user):
        return self.get_queryset().for_user(user)


class TenantScopedModel(models.Model):
    """
    Abstract base model enforcing UUID primary key, organization scoping,
    and audit timestamps.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        db_index=True,
        help_text="The tenant/organization that owns this record."
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    objects = TenantScopedManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']
