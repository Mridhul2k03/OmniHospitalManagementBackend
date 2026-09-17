from datetime import date, timedelta
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.properties.models import Property
from apps.rooms.models import RoomType, Room
from apps.guests.models import GuestProfile
from apps.availability.models import RoomAvailability
from apps.availability.services import AvailabilityService
from apps.reservations.models import Reservation
from apps.reservations.services import ReservationService


@pytest.mark.django_db
class TestReservationAndAvailabilityEngine:
    def setup_method(self):
        self.client = APIClient()

        self.org = Organization.objects.create(name="Apex Hospitality", code="apex-hosp", contact_email="contact@apex.com")
        self.staff_user = User.objects.create_user(
            email="desk@apex.com",
            username="apex_desk",
            password="Password123!",
            organization=self.org,
            role="FRONT_DESK"
        )
        self.property = Property.objects.create(
            organization=self.org,
            name="Apex Grand Hotel",
            code="APEX-MAIN",
            address="789 Central Ave",
            city="Chicago",
            state="IL",
            postal_code="60601",
            contact_email="frontdesk@apex.com",
            contact_phone="5551234567"
        )
        self.room_type = RoomType.objects.create(
            property=self.property,
            name="Deluxe King",
            code="DLX-KNG",
            base_occupancy=2,
            max_occupancy=3,
            base_price=250.00
        )
        # Create 2 physical rooms
        self.room_101 = Room.objects.create(
            property=self.property,
            room_type=self.room_type,
            room_number="101"
        )
        self.room_102 = Room.objects.create(
            property=self.property,
            room_type=self.room_type,
            room_number="102"
        )

        self.guest = GuestProfile.objects.create(
            organization=self.org,
            first_name="Eleanor",
            last_name="Vance",
            email="eleanor@example.com",
            phone_number="5559876543"
        )

        self.client.force_authenticate(user=self.staff_user)

    def test_availability_search(self):
        today = date.today()
        check_in = today + timedelta(days=5)
        check_out = today + timedelta(days=7)

        response = self.client.get('/api/v1/availability/search/', {
            'property_id': str(self.property.id),
            'check_in': check_in.strftime('%Y-%m-%d'),
            'check_out': check_out.strftime('%Y-%m-%d'),
            'adults': 2
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['available_room_types']) == 1
        rt_data = response.data['available_room_types'][0]
        assert rt_data['room_type_id'] == str(self.room_type.id)
        assert rt_data['total_nights'] == 2
        assert rt_data['estimated_total'] == 500.00

    def test_successful_reservation_locks_inventory(self):
        today = date.today()
        check_in = today + timedelta(days=10)
        check_out = today + timedelta(days=12)

        payload = {
            'property_id': str(self.property.id),
            'guest_id': str(self.guest.id),
            'room_type_id': str(self.room_type.id),
            'check_in_date': check_in.strftime('%Y-%m-%d'),
            'check_out_date': check_out.strftime('%Y-%m-%d'),
            'total_adults': 2,
            'source': 'DIRECT',
            'idempotency_key': 'test-unique-key-001'
        }

        response = self.client.post('/api/v1/reservations/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        res_data = response.data['reservation']
        assert res_data['status'] == 'CONFIRMED'
        assert res_data['total_amount'] == '500.00'
        assert 'confirmation_code' in res_data

        # Verify inventory has been decremented
        avail_record = RoomAvailability.objects.get(
            property=self.property,
            room_type=self.room_type,
            date=check_in
        )
        assert avail_record.available_rooms == 1
        assert avail_record.locked_rooms == 1

    def test_idempotency_key_prevents_duplicate_booking(self):
        today = date.today()
        check_in = today + timedelta(days=15)
        check_out = today + timedelta(days=17)

        payload = {
            'property_id': str(self.property.id),
            'guest_id': str(self.guest.id),
            'room_type_id': str(self.room_type.id),
            'check_in_date': check_in.strftime('%Y-%m-%d'),
            'check_out_date': check_out.strftime('%Y-%m-%d'),
            'total_adults': 1,
            'idempotency_key': 'idem-duplicate-prevent-key'
        }

        resp1 = self.client.post('/api/v1/reservations/', payload, format='json')
        assert resp1.status_code == status.HTTP_201_CREATED
        code1 = resp1.data['reservation']['confirmation_code']

        # Second request with same idempotency key
        resp2 = self.client.post('/api/v1/reservations/', payload, format='json')
        assert resp2.status_code == status.HTTP_201_CREATED
        code2 = resp2.data['reservation']['confirmation_code']

        # Must return the same confirmation code without creating a second reservation
        assert code1 == code2
        assert Reservation.objects.filter(idempotency_key='idem-duplicate-prevent-key').count() == 1

    def test_cancellation_releases_inventory(self):
        today = date.today()
        check_in = today + timedelta(days=20)
        check_out = today + timedelta(days=22)

        reservation = ReservationService.create_reservation(
            organization=self.org,
            property_obj=self.property,
            guest=self.guest,
            room_type_id=self.room_type.id,
            check_in_date=check_in,
            check_out_date=check_out
        )

        avail_during = RoomAvailability.objects.get(
            property=self.property,
            room_type=self.room_type,
            date=check_in
        )
        assert avail_during.available_rooms == 1
        assert avail_during.locked_rooms == 1

        # Cancel reservation
        cancel_url = f'/api/v1/reservations/{reservation.id}/cancel/'
        cancel_response = self.client.post(cancel_url)

        assert cancel_response.status_code == status.HTTP_200_OK
        assert cancel_response.data['status'] == 'CANCELLED'

        # Verify inventory has been restored
        avail_after = RoomAvailability.objects.get(
            property=self.property,
            room_type=self.room_type,
            date=check_in
        )
        assert avail_after.available_rooms == 2
        assert avail_after.locked_rooms == 0
