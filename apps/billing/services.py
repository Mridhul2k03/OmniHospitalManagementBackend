"""
Billing & Unified Folio services.
"""
import uuid
from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Folio, ChargeEvent


class FolioService:
    @classmethod
    def generate_folio_number(cls, property_code):
        short_id = uuid.uuid4().hex[:6].upper()
        return f"FOL-{property_code}-{short_id}"

    @classmethod
    def get_or_create_folio(cls, reservation):
        """Retrieves or initializes the primary folio for a reservation."""
        total_amount = Decimal(str(reservation.total_amount))
        paid_amount = Decimal(str(reservation.paid_amount))
        balance = total_amount - paid_amount

        folio, created = Folio.objects.get_or_create(
            reservation=reservation,
            defaults={
                'organization': reservation.organization,
                'property': reservation.property,
                'guest': reservation.guest,
                'folio_number': cls.generate_folio_number(reservation.property.code),
                'status': 'OPEN',
                'total_charges': total_amount,
                'total_payments': paid_amount,
                'balance': balance,
                'currency': reservation.currency,
            }
        )
        if created:
            # Post initial room rate charge event
            ChargeEvent.objects.create(
                organization=reservation.organization,
                property=reservation.property,
                folio=folio,
                reservation=reservation,
                guest=reservation.guest,
                event_id=f"EVT-ROOM-{uuid.uuid4().hex[:8].upper()}",
                idempotency_key=f"init-room-rate-{reservation.id}",
                source='ROOM_RATE',
                description=f"Room Charges ({reservation.total_nights} nights)",
                amount=reservation.total_amount,
                tax_amount=Decimal('0.00'),
                total_amount=reservation.total_amount,
                status='POSTED'
            )
        return folio

    @classmethod
    def close_folio(cls, folio):
        """Closes folio only if balance is completely settled."""
        folio.recalculate_balance()
        if folio.balance > Decimal('0.00'):
            raise ValidationError(
                f"Cannot close folio with outstanding balance: {folio.balance} {folio.currency}."
            )
        folio.status = 'CLOSED'
        folio.save(update_fields=['status', 'updated_at'])
        return folio


class ChargeEventService:
    @classmethod
    def post_charge_event(
        cls,
        folio,
        source,
        description,
        amount,
        tax_amount=Decimal('0.00'),
        outlet_code='',
        room=None,
        posted_by=None,
        idempotency_key=None
    ):
        if not idempotency_key:
            idempotency_key = f"evt-{uuid.uuid4().hex}"

        # Check idempotency
        existing = ChargeEvent.objects.filter(
            property=folio.property,
            idempotency_key=idempotency_key
        ).first()
        if existing:
            return existing

        total_amount = Decimal(str(amount)) + Decimal(str(tax_amount))
        event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"

        with transaction.atomic():
            event = ChargeEvent.objects.create(
                organization=folio.organization,
                property=folio.property,
                folio=folio,
                reservation=folio.reservation,
                guest=folio.guest,
                room=room,
                event_id=event_id,
                idempotency_key=idempotency_key,
                source=source,
                outlet_code=outlet_code,
                description=description,
                amount=Decimal(str(amount)),
                tax_amount=Decimal(str(tax_amount)),
                total_amount=total_amount,
                status='POSTED',
                posted_by=posted_by
            )
            folio.recalculate_balance()

        return event
