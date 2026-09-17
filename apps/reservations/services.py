"""
Reservation Service: Atomic transactional booking engine with idempotency & row locking.
"""
import uuid
from decimal import Decimal
from datetime import datetime
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Reservation, ReservationRoom
from apps.availability.services import AvailabilityService
from apps.rooms.models import RoomType, Room


class ReservationService:
    @classmethod
    def generate_confirmation_code(cls, property_code):
        short_id = uuid.uuid4().hex[:6].upper()
        date_str = datetime.now().strftime('%Y%m%d')
        return f"RES-{property_code}-{date_str}-{short_id}"

    @classmethod
    def create_reservation(
        cls,
        organization,
        property_obj,
        guest,
        room_type_id,
        check_in_date,
        check_out_date,
        total_adults=1,
        total_children=0,
        source='DIRECT',
        special_requests='',
        idempotency_key=None
    ):
        # 1. Idempotency Check
        if idempotency_key:
            existing = Reservation.objects.filter(
                property=property_obj,
                idempotency_key=idempotency_key
            ).first()
            if existing:
                return existing

        # 2. Date validation
        if check_out_date <= check_in_date:
            raise ValidationError("Check-out date must be after check-in date.")

        room_type = RoomType.objects.get(id=room_type_id, property=property_obj)
        num_nights = (check_out_date - check_in_date).days
        total_amount = room_type.base_price * num_nights

        # 3. Concurrency-safe atomic transaction
        with transaction.atomic():
            # Ensure availability matrix exists and lock row
            AvailabilityService.ensure_availability_records(property_obj, room_type, check_in_date, check_out_date)
            AvailabilityService.lock_inventory(
                property_id=property_obj.id,
                room_type_id=room_type.id,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                requested_count=1
            )

            code = cls.generate_confirmation_code(property_obj.code)

            reservation = Reservation.objects.create(
                organization=organization,
                property=property_obj,
                confirmation_code=code,
                guest=guest,
                source=source,
                status='CONFIRMED',
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                total_adults=total_adults,
                total_children=total_children,
                total_amount=total_amount,
                paid_amount=Decimal('0.00'),
                currency=property_obj.currency,
                special_requests=special_requests,
                idempotency_key=idempotency_key or ''
            )

            ReservationRoom.objects.create(
                reservation=reservation,
                room_type=room_type,
                nightly_rate=room_type.base_price
            )

        return reservation

    @classmethod
    def cancel_reservation(cls, reservation):
        if reservation.status == 'CANCELLED':
            return reservation

        with transaction.atomic():
            # Release locked inventory back to available pool
            for res_room in reservation.reservation_rooms.all():
                AvailabilityService.release_inventory(
                    property_id=reservation.property_id,
                    room_type_id=res_room.room_type_id,
                    check_in_date=reservation.check_in_date,
                    check_out_date=reservation.check_out_date,
                    requested_count=1
                )

            reservation.status = 'CANCELLED'
            reservation.save(update_fields=['status', 'updated_at'])

        return reservation
