"""
Availability Service: Concurrency-safe inventory checking and row-level locking.
"""
from datetime import timedelta
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import RoomAvailability
from apps.rooms.models import RoomType, Room


class AvailabilityService:
    @classmethod
    def get_date_range(cls, start_date, end_date):
        """Generates date list from start_date up to (but not including) end_date."""
        current = start_date
        while current < end_date:
            yield current
            current += timedelta(days=1)

    @classmethod
    def ensure_availability_records(cls, property_obj, room_type, start_date, end_date):
        """Initializes availability records for a date range if not already populated."""
        total_active_rooms = Room.objects.filter(
            property=property_obj,
            room_type=room_type,
            is_active=True
        ).count()

        for d in cls.get_date_range(start_date, end_date):
            RoomAvailability.objects.get_or_create(
                property=property_obj,
                room_type=room_type,
                date=d,
                defaults={
                    'total_rooms': total_active_rooms,
                    'available_rooms': total_active_rooms,
                    'locked_rooms': 0,
                }
            )

    @classmethod
    def check_availability(cls, property_id, room_type_id, check_in_date, check_out_date, requested_count=1):
        """
        Validates if requested_count rooms are continuously available for every night of the stay.
        """
        nights = list(cls.get_date_range(check_in_date, check_out_date))
        if not nights:
            raise ValidationError("Check-out date must be strictly after check-in date.")

        records = RoomAvailability.objects.filter(
            property_id=property_id,
            room_type_id=room_type_id,
            date__in=nights
        )
        record_map = {r.date: r.available_rooms for r in records}

        for d in nights:
            avail = record_map.get(d)
            if avail is None or avail < requested_count:
                return False
        return True

    @classmethod
    def lock_inventory(cls, property_id, room_type_id, check_in_date, check_out_date, requested_count=1):
        """
        Concurrency-safe atomic lock.
        Uses select_for_update() on availability rows to serialize concurrent attempts
        and prevent double-booking.
        """
        nights = list(cls.get_date_range(check_in_date, check_out_date))
        if not nights:
            raise ValidationError("Invalid stay dates.")

        # Row-level lock on availability records for the requested dates
        locked_records = list(
            RoomAvailability.objects.select_for_update().filter(
                property_id=property_id,
                room_type_id=room_type_id,
                date__in=nights
            )
        )

        if len(locked_records) != len(nights):
            raise ValidationError("Availability records incomplete for selected date range.")

        # Check every night has sufficient inventory
        for rec in locked_records:
            if rec.available_rooms < requested_count:
                raise ValidationError(
                    f"Room type sold out on {rec.date}. Available: {rec.available_rooms}, Requested: {requested_count}"
                )

        # Decrement available and increment locked
        for rec in locked_records:
            rec.available_rooms -= requested_count
            rec.locked_rooms += requested_count
            rec.save(update_fields=['available_rooms', 'locked_rooms'])

        return True

    @classmethod
    def release_inventory(cls, property_id, room_type_id, check_in_date, check_out_date, requested_count=1):
        """
        Releases previously locked or reserved inventory back to the available pool.
        """
        nights = list(cls.get_date_range(check_in_date, check_out_date))
        with transaction.atomic():
            locked_records = RoomAvailability.objects.select_for_update().filter(
                property_id=property_id,
                room_type_id=room_type_id,
                date__in=nights
            )
            for rec in locked_records:
                rec.available_rooms += requested_count
                rec.locked_rooms = max(0, rec.locked_rooms - requested_count)
                rec.save(update_fields=['available_rooms', 'locked_rooms'])
