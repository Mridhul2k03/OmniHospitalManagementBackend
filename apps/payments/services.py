"""
Payment processing and reconciliation services.
"""
import uuid
from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Payment, PaymentRefund


class PaymentService:
    @classmethod
    def record_payment(
        cls,
        folio,
        amount,
        payment_method='CREDIT_CARD',
        gateway='MANUAL_CASH',
        transaction_id=None,
        idempotency_key=None,
        recorded_by=None,
        gateway_payload=None
    ):
        dec_amount = Decimal(str(amount))
        if dec_amount <= Decimal('0.00'):
            raise ValidationError("Payment amount must be greater than zero.")

        # Idempotency check
        if idempotency_key:
            existing = Payment.objects.filter(
                property=folio.property,
                idempotency_key=idempotency_key
            ).first()
            if existing:
                return existing

        if not transaction_id:
            transaction_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"

        with transaction.atomic():
            payment = Payment.objects.create(
                organization=folio.organization,
                property=folio.property,
                folio=folio,
                reservation=folio.reservation,
                guest=folio.guest,
                amount=dec_amount,
                currency=folio.currency,
                payment_method=payment_method,
                gateway=gateway,
                status='PAID',
                transaction_id=transaction_id,
                idempotency_key=idempotency_key or '',
                gateway_payload=gateway_payload or {},
                recorded_by=recorded_by
            )

            folio.recalculate_balance()

            if folio.reservation:
                folio.reservation.paid_amount += dec_amount
                folio.reservation.save(update_fields=['paid_amount', 'updated_at'])

        return payment

    @classmethod
    def process_refund(cls, payment, amount, reason, processed_by=None):
        dec_amount = Decimal(str(amount))
        if dec_amount <= Decimal('0.00'):
            raise ValidationError("Refund amount must be greater than zero.")
        if dec_amount > payment.amount:
            raise ValidationError(f"Refund cannot exceed payment total ({payment.amount}).")

        refund_tx_id = f"REF-{uuid.uuid4().hex[:10].upper()}"

        with transaction.atomic():
            refund = PaymentRefund.objects.create(
                organization=payment.organization,
                property=payment.property,
                payment=payment,
                amount=dec_amount,
                reason=reason,
                status='PROCESSED',
                refund_transaction_id=refund_tx_id,
                processed_by=processed_by
            )

            payment.status = 'REFUNDED' if dec_amount == payment.amount else 'PARTIALLY_REFUNDED'
            payment.save(update_fields=['status', 'updated_at'])

            payment.folio.recalculate_balance()

            if payment.folio.reservation:
                payment.folio.reservation.paid_amount = max(
                    Decimal('0.00'),
                    payment.folio.reservation.paid_amount - dec_amount
                )
                payment.folio.reservation.save(update_fields=['paid_amount', 'updated_at'])

        return refund
