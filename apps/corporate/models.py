"""
Corporate governance models: Regions, Property Groups, Executive Scopes,
Shareholder Profiles, Dividends, and Financial Reports.
"""
import uuid
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


class ShareholderProfile(TenantScopedModel):
    """Strictly read-only profile for accredited shareholders."""
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='shareholder_profile'
    )
    ownership_units = models.PositiveIntegerField(default=0)
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    investment_date = models.DateField(null=True, blank=True)
    dividend_entitlement = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Shareholder Profile"
        verbose_name_plural = "Shareholder Profiles"

    def __str__(self):
        return f"{self.user.full_name} - {self.ownership_percentage}% ({self.ownership_units} units)"


class DividendDistribution(TenantScopedModel):
    """Historical and pending dividend distribution disbursements."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DISBURSED', 'Disbursed'),
        ('CANCELLED', 'Cancelled'),
    ]

    shareholder = models.ForeignKey(
        ShareholderProfile, on_delete=models.CASCADE, related_name='dividends'
    )
    period_label = models.CharField(max_length=64, help_text="e.g. Q3 2026, FY 2025-26")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='PENDING')
    disbursement_date = models.DateField(null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Dividend Distribution"
        verbose_name_plural = "Dividend Distributions"

    def __str__(self):
        return f"{self.shareholder.user.full_name} - {self.period_label}: {self.amount} {self.currency}"


class FinancialReport(TenantScopedModel):
    """Certified financial statements available for download."""
    REPORT_TYPE_CHOICES = [
        ('BALANCE_SHEET', 'Balance Sheet'),
        ('PROFIT_LOSS', 'Profit & Loss'),
        ('CASH_FLOW', 'Cash Flow Statement'),
        ('AUDIT_OPINION', 'Audit Opinion'),
        ('ANNUAL_REPORT', 'Annual Report'),
    ]

    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=32, choices=REPORT_TYPE_CHOICES)
    period_label = models.CharField(max_length=64)
    publish_date = models.DateField()
    pdf_url = models.URLField(blank=True)
    is_certified = models.BooleanField(default=False)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Financial Report"
        verbose_name_plural = "Financial Reports"
        ordering = ['-publish_date']

    def __str__(self):
        return f"{self.title} ({self.report_type}) - {self.period_label}"
