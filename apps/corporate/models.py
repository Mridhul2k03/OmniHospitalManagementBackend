"""
Corporate governance models: Regions, Property Groups, and Executive Scopes.
"""
from django.db import models
from common.tenancy.models import TenantScopedModel


class Region(TenantScopedModel):
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=64)
    description = models.TextField(blank=True)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Region"
        verbose_name_plural = "Regions"
        unique_together = ('organization', 'code')

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class PropertyGroup(TenantScopedModel):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='property_groups')
    name = models.CharField(max_length=255)
    code = models.SlugField(max_length=64)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Property Group"
        verbose_name_plural = "Property Groups"
        unique_together = ('organization', 'code')

    def __str__(self):
        return f"{self.name} - {self.region.name}"


class ExecutiveAssignment(TenantScopedModel):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='executive_assignments')
    role = models.CharField(
        max_length=32,
        choices=[
            ('PRESIDENT', 'President'),
            ('VICE_PRESIDENT', 'Vice President'),
            ('CEO', 'CEO'),
            ('OPERATIONS_DIRECTOR', 'Operations Director'),
        ]
    )
    assigned_regions = models.ManyToManyField(Region, blank=True, related_name='assigned_executives')
    is_active = models.BooleanField(default=True)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Executive Assignment"
        verbose_name_plural = "Executive Assignments"

    def __str__(self):
        return f"{self.user.full_name} - {self.role}"
