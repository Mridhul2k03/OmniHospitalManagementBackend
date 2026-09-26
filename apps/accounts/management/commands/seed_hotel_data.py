from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.properties.models import Property, Building, Floor
from apps.rooms.models import Room, RoomType, RoomAmenity
from apps.pricing.models import DynamicPricingRule, DemandBand
from apps.loyalty.models import GuestReview, PromoCampaign, LoyaltyMember

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds database with realistic hotel data matching OmniHospitalManagementFrontend"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Omni HMOS Enterprise Data...")

        # 1. Tenant Organization
        org, _ = Organization.objects.get_or_create(
            code="oxford-crest",
            defaults={
                "name": "Oxford Crest Luxury Hospitality",
                "legal_name": "Oxford Crest Luxury Hospitality LLC",
                "subscription_tier": "ENTERPRISE",
                "contact_email": "admin@oxfordcrest.com",
                "is_active": True
            }
        )

        # Also ensure default ghhg organization exists
        ghhg_org, _ = Organization.objects.get_or_create(
            code="ghhg",
            defaults={
                "name": "Grand Horizon Hospitality Group",
                "legal_name": "Grand Horizon Hospitality Group LLC",
                "subscription_tier": "ENTERPRISE",
                "contact_email": "corporate@omnihospitality.com",
                "is_active": True
            }
        )

        # 2. SuperUser
        if not User.objects.filter(username="admin").exists():
            admin_user = User.objects.create_superuser("admin", "admin@oxfordcrest.com", "Admin@123456")
            admin_user.organization = org
            admin_user.role = "SUPER_ADMIN"
            admin_user.save()
        else:
            admin_user = User.objects.get(username="admin")
            admin_user.set_password("Admin@123456")
            admin_user.organization = org
            admin_user.save()

        # 3. Property & Building
        prop, _ = Property.objects.get_or_create(
            code="GH-01",
            defaults={
                "name": "Grand Horizon Palace & Spa",
                "organization": org,
                "city": "New York",
                "state": "NY",
                "country": "US",
                "property_type": "HOTEL",
                "currency": "USD"
            }
        )
        bld, _ = Building.objects.get_or_create(
            code="MAIN",
            defaults={
                "name": "Main Palace Tower",
                "property": prop
            }
        )

        # 4. Floors 1 to 5
        floor_objs = {}
        for f_num in range(1, 6):
            floor, _ = Floor.objects.get_or_create(
                floor_number=f_num,
                building=bld,
                defaults={"name": f"Floor {f_num}"}
            )
            floor_objs[f_num] = floor

        # 5. Amenities & Room Types
        jacuzzi, _ = RoomAmenity.objects.get_or_create(name="Jacuzzi & Spa Tub", defaults={"description": "Private in-suite spa whirlpool"})
        balcony, _ = RoomAmenity.objects.get_or_create(name="Private Oceanfront Balcony", defaults={"description": "Panoramic ocean horizon view"})
        butler, _ = RoomAmenity.objects.get_or_create(name="24h Dedicated Butler Service", defaults={"description": "Discreet white-glove assistance"})

        rt_penthouse, _ = RoomType.objects.get_or_create(
            property=prop,
            code="PENT",
            defaults={
                "name": "Penthouse Royal Suite",
                "base_price": 1400.00,
                "base_occupancy": 2,
                "max_occupancy": 4,
                "description": "Top-floor duplex luxury suite with wraparound terrace and private elevator."
            }
        )
        rt_penthouse.amenities.add(jacuzzi, balcony, butler)

        rt_deluxe, _ = RoomType.objects.get_or_create(
            property=prop,
            code="EXEC-K",
            defaults={
                "name": "Executive Oceanfront King",
                "base_price": 380.00,
                "base_occupancy": 2,
                "max_occupancy": 3,
                "description": "Spacious king bedroom with floor-to-ceiling glass and marble bathroom."
            }
        )
        rt_deluxe.amenities.add(balcony)

        # 6. Physical Rooms (101 to 501)
        for room_no in ["101", "102", "201", "208", "304", "412", "501"]:
            f_num = int(room_no[0])
            Room.objects.get_or_create(
                room_number=room_no,
                defaults={
                    "property": prop,
                    "floor": floor_objs.get(f_num),
                    "room_type": rt_penthouse if room_no == "501" else rt_deluxe,
                    "status": "AVAILABLE",
                }
            )

        # 7. Dynamic AI Pricing Rules
        DynamicPricingRule.objects.get_or_create(
            organization=org,
            room_type=rt_penthouse,
            defaults={
                "demand_band": DemandBand.SURGE,
                "surge_multiplier": 1.25,
                "is_manual_override": False,
            }
        )
        DynamicPricingRule.objects.get_or_create(
            organization=org,
            room_type=rt_deluxe,
            defaults={
                "demand_band": DemandBand.HIGH,
                "surge_multiplier": 1.15,
                "is_manual_override": False,
            }
        )

        # 8. Guest Loyalty Members & Reviews
        LoyaltyMember.objects.get_or_create(
            organization=org,
            guest_name="Lord Sterling Crawford",
            defaults={
                "guest_email": "crawford@luxury.co.uk",
                "tier": "platinum",
                "points": 14200,
                "stays_count": 12,
                "lifetime_spend": 38400.00
            }
        )
        LoyaltyMember.objects.get_or_create(
            organization=org,
            guest_name="Lady Eleanor Vance",
            defaults={
                "guest_email": "vance@invest.com",
                "tier": "platinum",
                "points": 11800,
                "stays_count": 9,
                "lifetime_spend": 29500.00
            }
        )

        GuestReview.objects.get_or_create(
            organization=org,
            reviewer_name="Lord Sterling Crawford",
            defaults={
                "rating": 5,
                "stay_reference": "Room 501 Penthouse Royal Suite",
                "feedback": "Exemplary culinary execution and discreet butler service. The penthouse terrace view is unmatched.",
                "status": "responded",
                "management_response": "Thank you Lord Crawford, it was our distinct pleasure hosting your delegation."
            }
        )

        PromoCampaign.objects.get_or_create(
            organization=org,
            promo_code="AUTUMN26",
            defaults={
                "campaign_name": "Autumn VIP Escape",
                "discount_percentage": 15.00,
                "is_active": True
            }
        )

        self.stdout.write(self.style.SUCCESS("Omni HMOS Enterprise Data successfully seeded!"))
