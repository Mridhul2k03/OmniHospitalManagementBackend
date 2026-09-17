"""
Front Office operational services: Check-in, Check-out, Room Transfers.
"""
from datetime import datetime, timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import StayLog
from apps.billing.services import FolioService
from apps.rooms.models import Room


class FrontOfficeService:
    @classmethod
    def check_in(cls, reservation, room, checked_in_by=None, is_id_verified=False, signature_url='', key_cards_issued=1):
        if reservation.status not in ('CONFIRMED', 'PENDING'):
            raise ValidationError(f"Reservation cannot be checked in. Current status: {reservation.status}")

        if room.status not in ('AVAILABLE', 'INSPECTION'):
            raise ValidationError(f"Room {room.room_number} is not ready for check-in. Current status: {room.status}")

        with transaction.atomic():
            # Update Room status to OCCUPIED
            room.status = 'OCCUPIED'
            room.save(update_fields=['status'])

            # Update Reservation status to IN_HOUSE
            reservation.status = 'IN_HOUSE'
            reservation.save(update_fields=['status', 'updated_at'])

            # Assign physical room to ReservationRoom
            res_room = reservation.reservation_rooms.first()
            if res_room:
                res_room.allocated_room = room
                res_room.save(update_fields=['allocated_room'])

            # Initialize / ensure primary Folio exists
            FolioService.get_or_create_folio(reservation)

            # Record StayLog
            stay_log, _ = StayLog.objects.get_or_create(
                reservation=reservation,
                defaults={
                    'organization': reservation.organization,
                    'property': reservation.property,
                    'guest': reservation.guest,
                    'room': room,
                    'is_id_verified': is_id_verified,
                    'signature_url': signature_url,
                    'key_cards_issued': key_cards_issued,
                    'checked_in_by': checked_in_by
                }
            )

        return stay_log

    @classmethod
    def check_out(cls, reservation, checked_out_by=None):
        if reservation.status != 'IN_HOUSE':
            raise ValidationError(f"Cannot check out reservation with status {reservation.status}. Must be IN_HOUSE.")

        # Authoritative Folio Balance Validation
        folio = getattr(reservation, 'folio', None)
        if folio:
            folio.recalculate_balance()
            if folio.balance > 0:
                raise ValidationError(
                    f"Settlement required before check-out. Outstanding balance: {folio.balance} {folio.currency}."
                )

        stay_log = getattr(reservation, 'stay_log', None)
        room = stay_log.room if stay_log else None

        with transaction.atomic():
            # Close Folio
            if folio:
                FolioService.close_folio(folio)

            # Update Reservation status
            reservation.status = 'CHECKED_OUT'
            reservation.save(update_fields=['status', 'updated_at'])

            # Transition room status to DIRTY (ready for Housekeeping workflow)
            if room:
                room.status = 'DIRTY'
                room.save(update_fields=['status'])

            # Update StayLog
            if stay_log:
                stay_log.check_out_time = datetime.now(timezone.utc)
                stay_log.checked_out_by = checked_out_by
                stay_log.save(update_fields=['check_out_time', 'checked_out_by', 'updated_at'])

        return stay_log

    @classmethod
    def transfer_room(cls, reservation, new_room):
        if reservation.status != 'IN_HOUSE':
            raise ValidationError("Room transfer is only allowed for in-house guests.")

        if new_room.status not in ('AVAILABLE', 'INSPECTION'):
            raise ValidationError(f"Target Room {new_room.room_number} is not available (Status: {new_room.status}).")

        stay_log = getattr(reservation, 'stay_log', None)
        old_room = stay_log.room if stay_log else None

        with transaction.atomic():
            if old_room:
                old_room.status = 'DIRTY'
                old_room.save(update_fields=['status'])

            new_room.status = 'OCCUPIED'
            new_room.save(update_fields=['status'])

            res_room = reservation.reservation_rooms.first()
            if res_room:
                res_room.allocated_room = new_room
                res_room.save(update_fields=['allocated_room'])

            if stay_log:
                stay_log.room = new_room
                stay_log.save(update_fields=['room', 'updated_at'])

        return stay_log
