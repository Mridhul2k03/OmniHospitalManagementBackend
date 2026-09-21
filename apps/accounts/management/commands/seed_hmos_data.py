"""
Database seeding command for OmniHospitalManagement HMOS.
Populates full multi-tenant organization, properties, rooms, room types, rate plans,
guest profiles, reservations, active folios, stay logs, and all catalog user roles.
"""
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.properties.models import Property, Building, Floor
from apps.rooms.models import RoomType, Room, RatePlan
from apps.guests.models import GuestProfile
from apps.reservations.models import Reservation, ReservationRoom
from apps.billing.models import Folio
from apps.billing.services import FolioService, ChargeEventService
from apps.payments.services import PaymentService
from apps.frontoffice.models import StayLog
from apps.corporate.models import ShareholderProfile, DividendDistribution, FinancialReport


class Command(BaseCommand):
    help = "Seed the HMOS database with production-realistic demo data."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding HMOS database..."))

        # 1. Primary Tenant Organization
        org, _ = Organization.objects.get_or_create(
            code="ghhg",
            defaults={
                "name": "Grand Horizon Hospitality Group",
                "legal_name": "Grand Horizon Hospitality Group LLC",
                "contact_email": "corporate@omnihospitality.com",
                "contact_phone": "+1 (212) 555-0100",
                "address": "742 Evergreen Promenade, New York, NY 10001",
                "subscription_tier": "ENTERPRISE",
                "is_active": True,
            }
        )
        self.stdout.write(f"Organization: {org.name} ({org.code})")

        # 2. Seed All Catalog Role Users (Password: Password123!)
        users_specs = [
            ("superadmin@omnihospitality.com", "superadmin", "Alexander", "Wright", "SUPER_ADMIN", True, True),
            ("orgadmin@omnihospitality.com", "orgadmin", "Eleanor", "Vance", "ORG_ADMIN", True, False),
            ("manager.palace@omnihospitality.com", "manager_palace", "Marcus", "Sterling", "PROPERTY_MANAGER", False, False),
            ("frontdesk.palace@omnihospitality.com", "frontdesk_palace", "Sophia", "Chen", "FRONT_DESK", False, False),
            ("housekeeping.lead@omnihospitality.com", "housekeeping_lead", "Maria", "Santos", "HOUSEKEEPING", False, False),
            ("fnb.captain@omnihospitality.com", "fnb_captain", "Julian", "Rios", "RESTAURANT_POS", False, False),
            ("headchef@omnihospitality.com", "headchef", "Antoine", "Dubois", "CHEF_KITCHEN", False, False),
            ("chiefengineer@omnihospitality.com", "chiefengineer", "Vikram", "Patel", "MAINTENANCE", False, False),
            ("accountant@omnihospitality.com", "accountant", "Beatrice", "Lowe", "ACCOUNTANT", False, False),
            ("ceo@omnihospitality.com", "ceo_hale", "Jonathan", "Hale", "CEO", True, False),
            ("ops.director@omnihospitality.com", "ops_fox", "Samantha", "Fox", "OPERATIONS_DIRECTOR", False, False),
            ("shareholder.capital@aurumpartners.com", "shareholder_aurelia", "Aurelia", "Montague", "SHAREHOLDER", False, False),
            ("gate.chief@omnihospitality.com", "gate_chief", "Babatunde", "Adeleke", "SECURITY_STAFF", False, False),
            ("fleet.dispatch@omnihospitality.com", "fleet_dispatch", "Liam", "O'Connor", "TRANSPORT_DISPATCHER", False, False),
            ("guest.traveler@gmail.com", "guest_traveler", "Isabella", "Rossi", "GUEST", False, False),
        ]

        for email, username, first_name, last_name, role, is_staff, is_superuser in users_specs:
            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password="Password123!",
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    organization=org,
                    is_staff=is_staff,
                    is_superuser=is_superuser,
                )
            else:
                user.role = role
                user.organization = org
                user.set_password("Password123!")
                user.save()
        self.stdout.write(f"Seeded {len(users_specs)} user personas.")

        # 3. Properties
        prop_palace, _ = Property.objects.get_or_create(
            organization=org,
            code="ghp-ny",
            defaults={
                "name": "Grand Horizon Palace & Spa",
                "property_type": "HOTEL",
                "address": "742 Evergreen Promenade",
                "city": "New York",
                "state": "NY",
                "country": "US",
                "postal_code": "10001",
                "contact_email": "palace@omnihospitality.com",
                "contact_phone": "+1 (212) 555-0199",
                "check_in_time": "15:00",
                "check_out_time": "11:00",
                "currency": "USD",
            }
        )

        prop_resort, _ = Property.objects.get_or_create(
            organization=org,
            code="abor-mia",
            defaults={
                "name": "Azure Bay Ocean Resort",
                "property_type": "RESORT",
                "address": "10 Oceanfront Avenue",
                "city": "Miami Beach",
                "state": "FL",
                "country": "US",
                "postal_code": "33139",
                "contact_email": "azurebay@omnihospitality.com",
                "contact_phone": "+1 (305) 555-0144",
                "currency": "USD",
            }
        )

        prop_chalet, _ = Property.objects.get_or_create(
            organization=org,
            code="acc-asp",
            defaults={
                "name": "Alpine Crest Chalets",
                "property_type": "BOUTIQUE",
                "address": "45 Glacier Peak Trail",
                "city": "Aspen",
                "state": "CO",
                "country": "US",
                "postal_code": "81611",
                "contact_email": "alpinecrest@omnihospitality.com",
                "contact_phone": "+1 (970) 555-0188",
                "currency": "USD",
            }
        )

        # 4. Building & Floors
        bldg, _ = Building.objects.get_or_create(
            property=prop_palace,
            name="Main Grand Tower",
            defaults={"code": "mt-01"}
        )

        floors = {}
        for f_num in range(1, 6):
            fl, _ = Floor.objects.get_or_create(
                building=bldg,
                floor_number=f_num,
                defaults={"name": f"Floor {f_num}"}
            )
            floors[f_num] = fl

        # 5. Room Types
        rt_specs = [
            ("Penthouse Royal Suite", "prs-ste", 2, 4, Decimal("1450.00"), "Top floor panoramic suite with private plunge pool and dedicated butler."),
            ("Premier Suite", "prm-ste", 2, 3, Decimal("520.00"), "Spacious living area, marble bath, and private balcony."),
            ("Ocean View Executive", "exec-kng", 1, 2, Decimal("380.00"), "Executive king bed with high-floor unobstructed views and Nespresso bar."),
            ("Accessible Suite", "acc-ste", 1, 2, Decimal("260.00"), "ADA compliant suite with wide roll-in shower and audio-visual alarms."),
            ("Garden King Deluxe", "gdn-kng", 1, 2, Decimal("240.00"), "Luxurious king bed overlooking the botanical courtyard."),
        ]

        room_types = {}
        for name, code, base_occ, max_occ, price, desc in rt_specs:
            rt, _ = RoomType.objects.get_or_create(
                property=prop_palace,
                code=code,
                defaults={
                    "name": name,
                    "base_occupancy": base_occ,
                    "max_occupancy": max_occ,
                    "base_price": price,
                    "description": desc,
                    "is_active": True,
                }
            )
            room_types[code] = rt

            RatePlan.objects.get_or_create(
                property=prop_palace,
                room_type=rt,
                name="Best Available Rate",
                defaults={"code": f"bar-{code}", "meal_plan": "EP", "cancellation_policy": "FLEXIBLE_24H"}
            )

        # 6. Physical Rooms
        rooms_specs = [
            ("101", 1, "gdn-kng", "AVAILABLE"),
            ("102", 1, "gdn-kng", "OCCUPIED"),
            ("103", 1, "gdn-kng", "DIRTY"),
            ("104", 1, "gdn-kng", "CLEANING"),
            ("105", 1, "acc-ste", "AVAILABLE"),
            ("201", 2, "exec-kng", "OCCUPIED"),
            ("202", 2, "exec-kng", "AVAILABLE"),
            ("203", 2, "exec-kng", "INSPECTION"),
            ("204", 2, "exec-kng", "MAINTENANCE"),
            ("301", 3, "prm-ste", "AVAILABLE"),
            ("302", 3, "prm-ste", "OCCUPIED"),
            ("303", 3, "prm-ste", "RESERVED"),
            ("304", 3, "prm-ste", "OCCUPIED"),
            ("401", 4, "prs-ste", "OCCUPIED"),
            ("402", 4, "prs-ste", "AVAILABLE"),
        ]

        rooms = {}
        for r_num, f_num, rt_code, status in rooms_specs:
            rm, _ = Room.objects.get_or_create(
                property=prop_palace,
                room_number=r_num,
                defaults={
                    "floor": floors[f_num],
                    "room_type": room_types[rt_code],
                    "status": status,
                    "is_active": status != "OUT_OF_ORDER",
                }
            )
            rm.status = status
            rm.save()
            rooms[r_num] = rm

        self.stdout.write(f"Seeded {len(rooms_specs)} rooms across {len(floors)} floors.")

        # 7. Guests
        guests_data = [
            ("Lord Sterling", "Crawford", "crawford@estates.uk", "+44 20 7946 0912", "PASSPORT", "GB9821884", "United Kingdom", True),
            ("Dr. Eleanor", "Vance", "e.vance@techcorp.ch", "+41 22 555 0192", "PASSPORT", "CH773192", "Switzerland", True),
            ("Elena", "Rostova", "elena.rostova@geneva.com", "+41 22 888 1122", "PASSPORT", "CH991044", "Switzerland", True),
            ("Julian", "Montague", "j.montague@london.co.uk", "+44 20 7111 2222", "PASSPORT", "GB882910", "United Kingdom", True),
            ("Ambassador Alexander", "Thorne", "a.thorne@embassy.gov", "+1 202 555 0199", "PASSPORT", "US1102934", "United States", True),
        ]

        guests = {}
        for fn, ln, em, ph, id_type, id_num, country, vip in guests_data:
            g, _ = GuestProfile.objects.get_or_create(
                organization=org,
                email=em,
                defaults={
                    "first_name": fn,
                    "last_name": ln,
                    "phone_number": ph,
                    "id_document_type": id_type,
                    "id_document_number": id_num,
                    "nationality": country,
                    "vip_status": vip,
                }
            )
            guests[em] = g

        # 8. Reservations
        today = date.today()

        # Res 1: In-House (Lord Crawford in 401 Penthouse)
        res_crawford, _ = Reservation.objects.get_or_create(
            organization=org,
            confirmation_code="RES-9011",
            defaults={
                "property": prop_palace,
                "guest": guests["crawford@estates.uk"],
                "check_in_date": today - timedelta(days=2),
                "check_out_date": today + timedelta(days=3),
                "status": "IN_HOUSE",
                "source": "DIRECT",
                "total_amount": Decimal("7250.00"),
                "paid_amount": Decimal("1500.00"),
                "special_requests": "Late checkout requested, champagne on arrival.",
            }
        )
        ReservationRoom.objects.get_or_create(
            reservation=res_crawford,
            room_type=room_types["prs-ste"],
            defaults={
                "allocated_room": rooms["401"],
                "nightly_rate": Decimal("1450.00"),
            }
        )

        # Res 2: Today's Arrival (Elena Rostova in 304)
        res_elena, _ = Reservation.objects.get_or_create(
            organization=org,
            confirmation_code="RES-9012",
            defaults={
                "property": prop_palace,
                "guest": guests["elena.rostova@geneva.com"],
                "check_in_date": today,
                "check_out_date": today + timedelta(days=3),
                "status": "CONFIRMED",
                "source": "CORPORATE",
                "total_amount": Decimal("1560.00"),
                "paid_amount": Decimal("0.00"),
                "special_requests": "Quiet high floor, hypoallergenic bedding.",
            }
        )
        ReservationRoom.objects.get_or_create(
            reservation=res_elena,
            room_type=room_types["prm-ste"],
            defaults={
                "allocated_room": rooms["304"],
                "nightly_rate": Decimal("520.00"),
            }
        )

        # Res 3: Today's Departure (Dr. Eleanor Vance in 201)
        res_vance, _ = Reservation.objects.get_or_create(
            organization=org,
            confirmation_code="RES-8994",
            defaults={
                "property": prop_palace,
                "guest": guests["e.vance@techcorp.ch"],
                "check_in_date": today - timedelta(days=3),
                "check_out_date": today,
                "status": "IN_HOUSE",
                "source": "DIRECT",
                "total_amount": Decimal("1140.00"),
                "paid_amount": Decimal("0.00"),
            }
        )
        ReservationRoom.objects.get_or_create(
            reservation=res_vance,
            room_type=room_types["exec-kng"],
            defaults={
                "allocated_room": rooms["201"],
                "nightly_rate": Decimal("380.00"),
            }
        )

        # Res 4: Confirmed Future Arrival (Julian Montague in 302)
        res_julian, _ = Reservation.objects.get_or_create(
            organization=org,
            confirmation_code="RES-9104",
            defaults={
                "property": prop_palace,
                "guest": guests["j.montague@london.co.uk"],
                "check_in_date": today + timedelta(days=1),
                "check_out_date": today + timedelta(days=5),
                "status": "CONFIRMED",
                "source": "OTA_BOOKING_COM",
                "total_amount": Decimal("2080.00"),
                "paid_amount": Decimal("0.00"),
            }
        )
        ReservationRoom.objects.get_or_create(
            reservation=res_julian,
            room_type=room_types["prm-ste"],
            defaults={
                "allocated_room": rooms["302"],
                "nightly_rate": Decimal("520.00"),
            }
        )

        # 9. Folios & Line Charges
        frontdesk_user = User.objects.filter(email="frontdesk.palace@omnihospitality.com").first()

        folio_crawford = FolioService.get_or_create_folio(res_crawford)
        if folio_crawford.charge_events.count() <= 1:
            ChargeEventService.post_charge_event(
                folio=folio_crawford,
                source="POS_RESTAURANT",
                description="Palm Court Dining - Dinner Check #401",
                amount=Decimal("380.00"),
                tax_amount=Decimal("38.00"),
                posted_by=frontdesk_user,
            )
            ChargeEventService.post_charge_event(
                folio=folio_crawford,
                source="SPA",
                description="Aromatherapy & Deep Tissue Massage (2h)",
                amount=Decimal("240.00"),
                tax_amount=Decimal("24.00"),
                posted_by=frontdesk_user,
            )
            PaymentService.record_payment(
                folio=folio_crawford,
                amount=Decimal("1500.00"),
                payment_method="CREDIT_CARD",
                recorded_by=frontdesk_user,
            )

        folio_vance = FolioService.get_or_create_folio(res_vance)
        if folio_vance.payments.count() == 0 and folio_vance.balance > Decimal("0.00"):
            PaymentService.record_payment(
                folio=folio_vance,
                amount=folio_vance.balance,
                payment_method="CREDIT_CARD",
                recorded_by=frontdesk_user,
            )

        # 10. Stay Logs for In-House Guests
        StayLog.objects.get_or_create(
            organization=org,
            reservation=res_crawford,
            defaults={
                "property": prop_palace,
                "guest": guests["crawford@estates.uk"],
                "room": rooms["401"],
                "is_id_verified": True,
                "key_cards_issued": 2,
                "checked_in_by": frontdesk_user,
            }
        )
        StayLog.objects.get_or_create(
            organization=org,
            reservation=res_vance,
            defaults={
                "property": prop_palace,
                "guest": guests["e.vance@techcorp.ch"],
                "room": rooms["201"],
                "is_id_verified": True,
                "key_cards_issued": 1,
                "checked_in_by": frontdesk_user,
            }
        )

        # 11. Corporate & Shareholder Records
        shareholder_user = User.objects.filter(email="shareholder.capital@aurumpartners.com").first()
        if shareholder_user:
            profile, _ = ShareholderProfile.objects.get_or_create(
                organization=org,
                user=shareholder_user,
                defaults={
                    "ownership_units": 150000,
                    "ownership_percentage": Decimal("8.50"),
                    "investment_date": date(2024, 1, 15),
                    "dividend_entitlement": True,
                    "notes": "Aurum Partners Capital Fund III anchor shareholder.",
                }
            )
            DividendDistribution.objects.get_or_create(
                organization=org,
                shareholder=profile,
                period_label="FY 2025 Annual",
                defaults={
                    "amount": Decimal("127500.00"),
                    "currency": "USD",
                    "status": "DISBURSED",
                    "disbursement_date": date(2026, 2, 1),
                }
            )
            FinancialReport.objects.get_or_create(
                organization=org,
                title="Q4 2025 Consolidated Audited Financials",
                defaults={
                    "report_type": "AUDIT_OPINION",
                    "period_label": "Q4 2025 (Oct - Dec)",
                    "publish_date": date(2026, 1, 30),
                    "pdf_url": "https://omnihospitality.com/reports/2025-q4-audited.pdf",
                    "is_certified": True,
                }
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded HMOS database with full enterprise demo dataset!"))
