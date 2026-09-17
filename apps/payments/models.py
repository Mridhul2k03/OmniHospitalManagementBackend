"""
Payments and Refunds models.
"""
import uuid
from django.db import models
from common.tenancy.models import TenantScopedModel


class Payment(TenantScopedModel):
    METHOD_CHOICES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('UPI', 'UPI'),
        ('NET_BANKING', 'Net Banking'),
        ('WALLET', 'Digital Wallet'),
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Direct Bank Transfer'),
    ]

    GATEWAY_CHOICES = [
        ('MANUAL_CASH', 'Manual Front Desk Cash'),
        ('STRIPE', 'Stripe Gateway'),
        ('RAZORPAY', 'Razorpay Gateway'),
        ('OTHER', 'Other External Gateway'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Authorization'),
        ('AUTHORIZED', 'Authorized'),
        ('PAID', 'Paid / Captured'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
        ('PARTIALLY_REFUNDED', 'Partially Refunded'),
    ]

    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='payments')
    folio = models.ForeignKey('billing.Folio', on_delete=models.CASCADE, related_name='payments')
    reservation = models.ForeignKey('reservations.Reservation', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    guest = models.ForeignKey('guests.GuestProfile', on_delete=models.PROTECT, related_name='payments')

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=32, choices=METHOD_CHOICES, default='CREDIT_CARD')
    gateway = models.CharField(max_length=32, choices=GATEWAY_CHOICES, default='MANUAL_CASH')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='PAID', db_index=True)
    
    transaction_id = models.CharField(max_length=128, unique=True, db_index=True)
    idempotency_key = models.CharField(max_length=128, blank=True, db_index=True)
    gateway_payload = models.JSONField(default=dict, blank=True)
    
    paid_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency} ({self.status})"


class PaymentRefund(TenantScopedModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSED', 'Processed'),
        ('FAILED', 'Failed'),
    ]

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='PROCESSED')
    refund_transaction_id = models.CharField(max_length=128, unique=True)
    processed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Payment Refund"
        verbose_name_plural = "Payment Refunds"

    def __str__(self):
        return f"Refund {self.refund_transaction_id} for {self.payment.transaction_id} - {self.amount}"
