from datetime import date, timedelta
from decimal import Decimal
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.properties.models import Property
from apps.rooms.models import RoomType, Room
from apps.guests.models import GuestProfile
from apps.reservations.models import Reservation
from apps.reservations.services import ReservationService
from apps.billing.models import Folio, ChargeEvent
from apps.billing.services import FolioService, ChargeEventService
from apps.payments.models import Payment
from apps.payments.services import PaymentService
from apps.frontoffice.models import StayLog
from apps.frontoffice.services import FrontOfficeService


@pytest.mark.django_db
class TestPMSAndFrontOffice:
    def setup_method(self):
        self.client = APIClient()

        self.org = Organization.objects.create(name="Omni Hotels Corp", code="omni-corp", contact_email="corp@omni.com")
        self.staff_user = User.objects.create_user(
            email="desk@omnihotels.com",
            username="omni_desk",
            password="Password123!",
            organization=self.org,
            role="FRONT_DESK"
        )
        self.property = Property.objects.create(
            organization=self.org,
            name="Omni Palace",
            code="OMNI-PALACE",
            address="100 Grand Boulevard",
            city="Las Vegas",
            state="NV",
            postal_code="89109",
            contact_email="frontdesk@omni.com",
            contact_phone="7025550199"
        )
        self.room_type = RoomType.objects.create(
            property=self.property,
            name="Presidential Suite",
            code="PRS-STE",
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('500.00')
        )
        self.room_201 = Room.objects.create(
            property=self.property,
            room_type=self.room_type,
            room_number="201",
            status="AVAILABLE"
        )
        self.room_202 = Room.objects.create(
            property=self.property,
            room_type=self.room_type,
            room_number="202",
            status="AVAILABLE"
        )

        self.guest = GuestProfile.objects.create(
            organization=self.org,
            first_name="Victoria",
            last_name="Sterling",
            email="v.sterling@example.com",
            phone_number="7025550144"
        )

        # Create a confirmed 2-night reservation
        today = date.today()
        self.reservation = ReservationService.create_reservation(
            organization=self.org,
            property_obj=self.property,
            guest=self.guest,
            room_type_id=self.room_type.id,
            check_in_date=today + timedelta(days=1),
            check_out_date=today + timedelta(days=3)
        )

        self.client.force_authenticate(user=self.staff_user)

    def test_check_in_flow(self):
        # 1. Execute check-in
        check_in_url = '/api/v1/frontoffice/check-in/'
        response = self.client.post(check_in_url, {
            'reservation_id': str(self.reservation.id),
            'room_id': str(self.room_201.id),
            'is_id_verified': True,
            'key_cards_issued': 2
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['reservation_status'] == 'IN_HOUSE'
        assert response.data['room_status'] == 'OCCUPIED'

        # Refresh from database
        self.room_201.refresh_from_db()
        assert self.room_201.status == 'OCCUPIED'

        self.reservation.refresh_from_db()
        assert self.reservation.status == 'IN_HOUSE'

        # Verify Folio was initialized
        folio = Folio.objects.get(reservation=self.reservation)
        assert folio.status == 'OPEN'
        assert folio.total_charges == Decimal('1000.00')  # 2 nights * $500
        assert folio.balance == Decimal('1000.00')

    def test_folio_charge_event_and_idempotency(self):
        # Initialize folio via service
        folio = FolioService.get_or_create_folio(self.reservation)
        initial_balance = folio.balance

        # Post room service charge
        charge_url = f'/api/v1/billing/folios/{folio.id}/charges/'
        charge_payload = {
            'source': 'ROOM_SERVICE',
            'description': 'Late night dining - Champagne & Caviar',
            'amount': '150.00',
            'tax_amount': '15.00',
            'outlet_code': 'KITCHEN-MAIN',
            'idempotency_key': 'charge-room-service-001'
        }

        resp1 = self.client.post(charge_url, charge_payload, format='json')
        assert resp1.status_code == status.HTTP_201_CREATED
        assert resp1.data['new_balance'] == float(initial_balance + Decimal('165.00'))

        # Post duplicate charge with same idempotency key
        resp2 = self.client.post(charge_url, charge_payload, format='json')
        assert resp2.status_code == status.HTTP_201_CREATED

        # Ensure only one charge event exists with that key
        assert ChargeEvent.objects.filter(idempotency_key='charge-room-service-001').count() == 1
        folio.refresh_from_db()
        assert folio.balance == initial_balance + Decimal('165.00')

    def test_checkout_fails_with_outstanding_balance(self):
        # Check in guest
        FrontOfficeService.check_in(self.reservation, self.room_201, checked_in_by=self.staff_user)

        # Attempt to checkout with $1000 balance
        checkout_url = '/api/v1/frontoffice/check-out/'
        response = self.client.post(checkout_url, {
            'reservation_id': str(self.reservation.id)
        }, format='json')

        # Must fail with validation error
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Settlement required before check-out' in str(response.data)

    def test_full_settlement_and_successful_checkout(self):
        # 1. Check in
        FrontOfficeService.check_in(self.reservation, self.room_201, checked_in_by=self.staff_user)
        folio = Folio.objects.get(reservation=self.reservation)

        # 2. Pay full balance
        pay_url = '/api/v1/payments/'
        pay_resp = self.client.post(pay_url, {
            'folio_id': str(folio.id),
            'amount': '1000.00',
            'payment_method': 'CREDIT_CARD',
            'gateway': 'STRIPE',
            'idempotency_key': 'pay-full-settlement-001'
        }, format='json')

        assert pay_resp.status_code == status.HTTP_201_CREATED
        assert pay_resp.data['folio_balance'] == 0.0

        folio.refresh_from_db()
        assert folio.balance == Decimal('0.00')

        # 3. Check out
        checkout_url = '/api/v1/frontoffice/check-out/'
        checkout_resp = self.client.post(checkout_url, {
            'reservation_id': str(self.reservation.id)
        }, format='json')

        assert checkout_resp.status_code == status.HTTP_200_OK
        assert checkout_resp.data['reservation_status'] == 'CHECKED_OUT'

        # 4. Verify room is now DIRTY (ready for Housekeeping queue)
        self.room_201.refresh_from_db()
        assert self.room_201.status == 'DIRTY'

        # 5. Verify folio is CLOSED
        folio.refresh_from_db()
        assert folio.status == 'CLOSED'

    def test_room_transfer_in_house(self):
        # Check in guest to Room 201
        FrontOfficeService.check_in(self.reservation, self.room_201, checked_in_by=self.staff_user)
        assert self.room_201.status == 'OCCUPIED'
        assert self.room_202.status == 'AVAILABLE'

        # Transfer guest to Room 202
        transfer_url = '/api/v1/frontoffice/transfer-room/'
        transfer_resp = self.client.post(transfer_url, {
            'reservation_id': str(self.reservation.id),
            'new_room_id': str(self.room_202.id)
        }, format='json')

        assert transfer_resp.status_code == status.HTTP_200_OK

        # Verify old room 201 is now DIRTY
        self.room_201.refresh_from_db()
        assert self.room_201.status == 'DIRTY'

        # Verify new room 202 is now OCCUPIED
        self.room_202.refresh_from_db()
        assert self.room_202.status == 'OCCUPIED'

        # Verify StayLog reflects new room
        stay_log = StayLog.objects.get(reservation=self.reservation)
        assert stay_log.room == self.room_202
