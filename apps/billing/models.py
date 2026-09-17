"""
Unified Folio and Financial Charge-Event Layer models.
"""
import uuid
import builtins
from decimal import Decimal
from django.db import models
from common.tenancy.models import TenantScopedModel


class Folio(TenantScopedModel):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('SETTLED', 'Settled'),
        ('SUSPENDED', 'Suspended'),
    ]

    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='folios')
    reservation = models.OneToOneField('reservations.Reservation', on_delete=models.CASCADE, related_name='folio')
    guest = models.ForeignKey('guests.GuestProfile', on_delete=models.PROTECT, related_name='folios')
    folio_number = models.CharField(max_length=64, unique=True, db_index=True)
    
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    total_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Folio"
        verbose_name_plural = "Folios"

    def __str__(self):
        return f"{self.folio_number} - {self.guest.full_name} (Balance: {self.balance} {self.currency})"

    def recalculate_balance(self):
        """Authoritatively recomputes folio balance from charge events and payments."""
        charges_sum = self.charge_events.filter(status='POSTED').aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        payments_sum = self.payments.filter(status='PAID').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        self.total_charges = charges_sum
        self.total_payments = payments_sum
        self.balance = charges_sum - payments_sum
        if self.balance <= 0 and self.status == 'OPEN' and self.total_payments > 0:
            self.status = 'SETTLED'
        elif self.balance > 0 and self.status == 'SETTLED':
            self.status = 'OPEN'
        self.save(update_fields=['total_charges', 'total_payments', 'balance', 'status', 'updated_at'])
        return self.balance


class ChargeEvent(TenantScopedModel):
    SOURCE_CHOICES = [
        ('ROOM_RATE', 'Room Rate Charge'),
        ('POS_RESTAURANT', 'Restaurant / Bar POS'),
        ('ROOM_SERVICE', 'Room Service'),
        ('SPA', 'Spa Treatment'),
        ('ACTIVITIES', 'Activities / Tours'),
        ('LAUNDRY', 'Laundry Service'),
        ('MINIBAR', 'Minibar Consumption'),
        ('BANQUET', 'Banquet / Event'),
        ('DAMAGE', 'Damage Penalty'),
        ('OTHER', 'Other Amenity'),
    ]

    STATUS_CHOICES = [
        ('POSTED', 'Posted'),
        ('ADJUSTED', 'Adjusted'),
        ('VOIDED', 'Voided'),
        ('REVERSED', 'Reversed'),
    ]

    event_id = models.CharField(max_length=64, unique=True, db_index=True)
    idempotency_key = models.CharField(max_length=128, db_index=True)
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='charge_events')
    folio = models.ForeignKey(Folio, on_delete=models.CASCADE, related_name='charge_events')
    reservation = models.ForeignKey('reservations.Reservation', on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey('rooms.Room', on_delete=models.SET_NULL, null=True, blank=True)
    guest = models.ForeignKey('guests.GuestProfile', on_delete=models.PROTECT)

    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, default='OTHER')
    outlet_code = models.CharField(max_length=64, blank=True)
    description = models.CharField(max_length=255)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='POSTED', db_index=True)
    posted_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Charge Event"
        verbose_name_plural = "Charge Events"
        unique_together = ('property', 'idempotency_key')
        indexes = [
            models.Index(fields=['folio', 'status']),
        ]

    def __str__(self):
        return f"{self.event_id} [{self.source}] - {self.total_amount} ({self.status})"


class Invoice(TenantScopedModel):
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='invoices')
    folio = models.ForeignKey(Folio, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=64, unique=True, db_index=True)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    pdf_url = models.URLField(blank=True)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def __str__(self):
        return f"{self.invoice_number} - Total: {self.total}"
