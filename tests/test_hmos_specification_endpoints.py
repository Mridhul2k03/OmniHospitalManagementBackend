import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.properties.models import Property, Building, Floor
from apps.rooms.models import Room, RoomType
from apps.pricing.models import DynamicPricingRule, DemandBand
from apps.loyalty.models import GuestReview, LoyaltyMember


@pytest.mark.django_db
class TestHMOSSpecificationEndpoints:
    def setup_method(self):
        self.client = APIClient()
        self.org = Organization.objects.create(
            name="Oxford Crest Hospitality",
            code="oxford-test",
            contact_email="admin@oxfordtest.com"
        )
        self.user = User.objects.create_user(
            email="admin@oxfordtest.com",
            username="oxford_admin",
            password="AdminPassword123!",
            organization=self.org,
            role="SUPER_ADMIN",
            is_staff=True,
            is_superuser=True
        )
        self.prop = Property.objects.create(
            organization=self.org,
            name="Grand Horizon Palace",
            code="GHP-TEST",
            city="New York"
        )
        self.building = Building.objects.create(
            property=self.prop,
            name="Main Tower",
            code="MAIN-TOWER"
        )
        self.floor = Floor.objects.create(
            building=self.building,
            floor_number=5,
            name="Floor 5"
        )
        self.room_type = RoomType.objects.create(
            property=self.prop,
            name="Penthouse Suite",
            code="PENT-SUITE",
            base_price=1400.00,
            base_occupancy=2,
            max_occupancy=4
        )
        self.room = Room.objects.create(
            property=self.prop,
            floor=self.floor,
            room_type=self.room_type,
            room_number="501",
            status="AVAILABLE"
        )
        self.pricing_rule = DynamicPricingRule.objects.create(
            organization=self.org,
            room_type=self.room_type,
            demand_band=DemandBand.SURGE,
            surge_multiplier=1.25,
            is_manual_override=False
        )
        self.client.force_authenticate(user=self.user)

    def test_dynamic_pricing_rules_and_demand_bands(self):
        res = self.client.get('/api/v1/pricing/rules/')
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) >= 1
        assert res.data[0]['roomTypeName'] == "Penthouse Suite"

        res_bands = self.client.get('/api/v1/pricing/demand-bands/')
        assert res_bands.status_code == status.HTTP_200_OK
        assert res_bands.data['activeBand'] == "surge"

    def test_dynamic_pricing_override_and_revoke(self):
        res_override = self.client.post('/api/v1/pricing/overrides/', {
            "roomTypeId": str(self.room_type.id),
            "overrideRate": 1850.00,
            "reason": "VIP delegation strategy"
        }, format='json')
        assert res_override.status_code == status.HTTP_200_OK
        assert res_override.data['isManualOverride'] is True
        assert float(res_override.data['manualOverrideRate']) == 1850.00
        assert float(res_override.data['calculatedRate']) == 1850.00

        rule_id = res_override.data['id']
        res_del = self.client.delete(f'/api/v1/pricing/rules/{rule_id}/overrides/')
        assert res_del.status_code == status.HTTP_200_OK
        self.pricing_rule.refresh_from_db()
        assert self.pricing_rule.is_manual_override is False

    def test_loyalty_tiers_members_and_reviews(self):
        res_tiers = self.client.get('/api/v1/loyalty/tiers/')
        assert res_tiers.status_code == status.HTTP_200_OK
        assert 'silverCount' in res_tiers.data
        assert 'platinumCount' in res_tiers.data

        res_members = self.client.get('/api/v1/loyalty/members/')
        assert res_members.status_code == status.HTTP_200_OK
        assert len(res_members.data) >= 1

        review = GuestReview.objects.create(
            organization=self.org,
            reviewer_name="Lord Crawford",
            rating=5,
            stay_reference="Room 501 Penthouse",
            feedback="Exemplary experience.",
            status="pending"
        )
        res_reviews = self.client.get('/api/v1/loyalty/reviews/')
        assert res_reviews.status_code == status.HTTP_200_OK

        res_respond = self.client.post(f'/api/v1/loyalty/{review.id}/respond/', {
            "responseText": "Thank you Lord Crawford."
        }, format='json')
        assert res_respond.status_code == status.HTTP_200_OK
        review.refresh_from_db()
        assert review.status == "responded"

    def test_loyalty_campaign_creation(self):
        res_camp = self.client.post('/api/v1/loyalty/campaigns/', {
            "name": "Autumn VIP Escape",
            "promoCode": "AUTUMN26",
            "discountPercentage": 15.00
        }, format='json')
        assert res_camp.status_code == status.HTTP_201_CREATED
        assert res_camp.data['promoCode'] == "AUTUMN26"

    def test_walk_in_booking_and_digital_check_in(self):
        # Walk-in booking with guest dict and direct room allocation
        res_walkin = self.client.post('/api/v1/reservations/', {
            "guest": {
                "firstName": "Julian",
                "lastName": "Rios",
                "email": "julian.rios@example.com",
                "phone": "+1 555-0199"
            },
            "roomId": str(self.room.id),
            "checkInDate": "2026-09-24",
            "checkOutDate": "2026-09-27",
            "channel": "walk_in"
        }, format='json')
        assert res_walkin.status_code == status.HTTP_201_CREATED
        conf_code = res_walkin.data['reservation']['confirmation_code']

        # Digital check-in using confirmation code
        res_dcheckin = self.client.post('/api/v1/reservations/digital-check-in/', {
            "confirmationCode": conf_code,
            "signatureBase64": "data:image/png;base64,sample_signature"
        }, format='json')
        assert res_dcheckin.status_code == status.HTTP_200_OK
        assert res_dcheckin.data['status'] == 'confirmed'
        assert 'qrCode' in res_dcheckin.data

    def test_direct_folios_and_night_audit(self):
        res_folios = self.client.get('/api/v1/folios/')
        assert res_folios.status_code == status.HTTP_200_OK

        res_audit = self.client.post('/api/v1/folios/night-audit/')
        assert res_audit.status_code == status.HTTP_200_OK
        assert 'total_daily_revenue' in res_audit.data

        res_gl = self.client.get('/api/v1/finance/gl-export/')
        assert res_gl.status_code == status.HTTP_200_OK
        assert res_gl['Content-Type'] == 'text/csv'

    def test_dining_kot_and_folio_billing(self):
        # Firing KOT order
        res_kot = self.client.post('/api/v1/dining/orders/kot/', {
            "tableNumber": "T-01",
            "roomNumber": "501",
            "items": [{"name": "Charred Wagyu", "quantity": 1, "station": "grill"}]
        }, format='json')
        assert res_kot.status_code == status.HTTP_201_CREATED
        kot_id = res_kot.data['id']

        # Check KDS tickets
        res_kds = self.client.get('/api/v1/kot/orders/')
        assert res_kds.status_code == status.HTTP_200_OK

        # Advance KDS ticket status
        res_status = self.client.patch(f'/api/v1/kot/orders/{kot_id}/status/', {
            "status": "ready"
        }, format='json')
        assert res_status.status_code == status.HTTP_200_OK
        assert res_status.data['status'] == "ready"

        # Bill dining check to room folio
        res_folio = self.client.post('/api/v1/dining/orders/folio/', {
            "roomNumber": "501",
            "amount": 145.00,
            "tip": 20.00
        }, format='json')
        assert res_folio.status_code == status.HTTP_200_OK
        assert res_folio.data['success'] is True

    def test_lost_and_found_claim_bridge(self):
        res_claim = self.client.post('/api/v1/housekeeping/lost-found/lf-1/claim/', {
            "claimantName": "Lord Sterling Crawford",
            "verifiedBy": "Front Desk Lead"
        }, format='json')
        assert res_claim.status_code == status.HTTP_200_OK
        assert res_claim.data['status'] == "claimed"

    def test_events_beo_folio_bridge(self):
        res_events_folio = self.client.get('/api/v1/events/ev-1/folio/')
        assert res_events_folio.status_code == status.HTTP_200_OK
        assert 'venueRental' in res_events_folio.data
        assert 'catering' in res_events_folio.data
        assert 'total' in res_events_folio.data

    def test_channel_mappings_bridge(self):
        res_mappings = self.client.get('/api/v1/channels/ch-1/mappings/')
        assert res_mappings.status_code == status.HTTP_200_OK
        assert len(res_mappings.data) >= 1

        res_post_map = self.client.post('/api/v1/channels/ch-1/mappings/', {
            "pmsRoomTypeId": str(self.room_type.id),
            "otaRoomCode": "BK-TEST-SUITE"
        }, format='json')
        assert res_post_map.status_code == status.HTTP_201_CREATED

    def test_corporate_and_shareholder_endpoints(self):
        res_trend = self.client.get('/api/v1/executive/occupancy-trend/')
        assert res_trend.status_code == status.HTTP_200_OK

        res_board = self.client.get('/api/v1/executive/export-board-pack/')
        assert res_board.status_code == status.HTTP_200_OK
        assert res_board['Content-Type'] == 'application/pdf'

        res_assets = self.client.get('/api/v1/shareholder/assets/')
        assert res_assets.status_code == status.HTTP_200_OK

        res_voucher = self.client.get('/api/v1/shareholder/dividends/div-1/voucher-pdf/')
        assert res_voucher.status_code == status.HTTP_200_OK
        assert res_voucher['Content-Type'] == 'application/pdf'

    def test_properties_policies_endpoint(self):
        res_get = self.client.get(f'/api/v1/properties/{self.prop.id}/policies/')
        assert res_get.status_code == status.HTTP_200_OK
        assert 'checkInTime' in res_get.data

        res_patch = self.client.patch(f'/api/v1/properties/{self.prop.id}/policies/', {
            "checkInTime": "16:00",
            "stateTaxRate": 9.5
        }, format='json')
        assert res_patch.status_code == status.HTTP_200_OK
        assert res_patch.data['data']['checkInTime'] == "16:00"
