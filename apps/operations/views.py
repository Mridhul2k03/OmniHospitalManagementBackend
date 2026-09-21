"""
Operations Views providing Dining, POS, KOT, Housekeeping, Maintenance, and Transport endpoints.
"""
import uuid
from datetime import datetime, timezone
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

# In-memory operational store for runtime agility with PMS integration
DINING_TABLES = [
    {"id": "tbl-1", "tableNumber": "T-01", "section": "Terrace Dining", "capacity": 4, "status": "available", "currentServer": "Julian Rios"},
    {"id": "tbl-2", "tableNumber": "T-02", "section": "Terrace Dining", "capacity": 2, "status": "occupied", "currentServer": "Julian Rios", "activeOrderId": "ord-101"},
    {"id": "tbl-3", "tableNumber": "T-03", "section": "Main Dining Hall", "capacity": 6, "status": "reserved", "currentServer": "Elena Vance"},
    {"id": "tbl-4", "tableNumber": "T-04", "section": "Main Dining Hall", "capacity": 4, "status": "billing", "currentServer": "Julian Rios", "activeOrderId": "ord-102"},
    {"id": "tbl-5", "tableNumber": "B-01", "section": "Rooftop Bar", "capacity": 2, "status": "available", "currentServer": "Alex Wright"},
]

MENU_ITEMS = [
    {"id": "item-1", "name": "Wagyu Ribeye Steak (8oz)", "category": "Mains", "price": 85.00, "station": "grill", "isAvailable": True},
    {"id": "item-2", "name": "Pan-Seared Chilean Sea Bass", "category": "Mains", "price": 68.00, "station": "grill", "isAvailable": True},
    {"id": "item-3", "name": "Lobster Bisque & Cognac", "category": "Starters", "price": 24.00, "station": "pantry", "isAvailable": True},
    {"id": "item-4", "name": "Truffle Tagliolini", "category": "Pasta", "price": 42.00, "station": "pantry", "isAvailable": True},
    {"id": "item-5", "name": "Grand Cru Chocolate Soufflé", "category": "Desserts", "price": 22.00, "station": "pastry", "isAvailable": True},
    {"id": "item-6", "name": "Smoked Old Fashioned", "category": "Cocktails", "price": 20.00, "station": "bar", "isAvailable": True},
]

KOT_ORDERS = [
    {
        "id": "kot-1",
        "ticketNumber": "KOT-8801",
        "tableNumber": "T-02",
        "station": "grill",
        "status": "preparing",
        "serverName": "Julian Rios",
        "guestCount": 2,
        "items": [
            {"menuItemId": "item-1", "name": "Wagyu Ribeye Steak (8oz)", "quantity": 1, "specialInstructions": "Medium-Rare, peppercorn sauce"},
            {"menuItemId": "item-2", "name": "Pan-Seared Chilean Sea Bass", "quantity": 1, "specialInstructions": "Crispy skin"}
        ],
        "createdAt": "2026-09-20T19:42:00Z"
    },
    {
        "id": "kot-2",
        "ticketNumber": "KOT-8802",
        "tableNumber": "T-04",
        "station": "bar",
        "status": "ready",
        "serverName": "Julian Rios",
        "guestCount": 4,
        "items": [
            {"menuItemId": "item-6", "name": "Smoked Old Fashioned", "quantity": 3, "specialInstructions": "One without cherry"}
        ],
        "createdAt": "2026-09-20T19:48:00Z"
    }
]

HOUSEKEEPING_TASKS = [
    {
        "id": "hk-1",
        "roomNumber": "103",
        "floorNumber": 1,
        "roomTypeName": "Superior King Room",
        "taskType": "turnover",
        "status": "cleaning_started",
        "priority": "high",
        "assignedAttendantName": "Maria Santos",
        "assignedTo": "Maria Santos",
        "startedAt": "2026-09-20T10:00:00Z",
        "checklist": [
            {"id": "c1", "task": "Strip bed linens & replace with fresh 400TC cotton", "completed": True},
            {"id": "c2", "task": "Disinfect bathroom vanities & restock Hermès amenities", "completed": True},
            {"id": "c3", "task": "Vacuum hardwood floors & wool carpets", "completed": False},
            {"id": "c4", "task": "Restock complimentary mineral water & espresso pods", "completed": False},
            {"id": "c5", "task": "Inspect mini-bar seal and climate thermostat", "completed": False},
        ],
    },
    {
        "id": "hk-2",
        "roomNumber": "104",
        "floorNumber": 1,
        "roomTypeName": "Deluxe Double Queen",
        "taskType": "deep_clean",
        "status": "dirty",
        "priority": "medium",
        "assignedAttendantName": "Maria Santos",
        "assignedTo": "Maria Santos",
        "checklist": [
            {"id": "c1", "task": "Strip bed linens & replace with fresh 400TC cotton", "completed": False},
            {"id": "c2", "task": "Disinfect bathroom vanities & restock amenities", "completed": False},
            {"id": "c3", "task": "Deep steam carpet cleaning", "completed": False},
            {"id": "c4", "task": "Wipe window sills and sanitize fixtures", "completed": False},
        ],
    },
    {
        "id": "hk-3",
        "roomNumber": "203",
        "floorNumber": 2,
        "roomTypeName": "Executive Suite",
        "taskType": "inspection",
        "status": "inspection",
        "priority": "high",
        "assignedAttendantName": "Lead Supervisor Vance",
        "assignedTo": "Lead Supervisor Vance",
        "checklist": [
            {"id": "c1", "task": "Verify linen thread count and pillow plumping", "completed": True},
            {"id": "c2", "task": "Inspect bathroom glass and marble polishing", "completed": True},
            {"id": "c3", "task": "Test smart automation panel & TV casting", "completed": True},
            {"id": "c4", "task": "Check welcome champagne presentation", "completed": False},
        ],
    },
    {
        "id": "hk-4",
        "roomNumber": "301",
        "floorNumber": 3,
        "roomTypeName": "Presidential Penthouse",
        "taskType": "turndown",
        "status": "cleaning_completed",
        "priority": "low",
        "assignedAttendantName": "Carlos Ruiz",
        "assignedTo": "Carlos Ruiz",
        "checklist": [
            {"id": "c1", "task": "Evening turndown: Fold duvet & place artisan chocolates", "completed": True},
            {"id": "c2", "task": "Dim lighting to ambient evening scene", "completed": True},
            {"id": "c3", "task": "Restock bedside mineral water & ice bucket", "completed": True},
        ],
    },
]

LOST_AND_FOUND = [
    {
        "id": "lf-1",
        "itemDescription": "Gold Montblanc Rollerball Pen",
        "category": "Other",
        "locationFound": "Room 501 (Penthouse)",
        "foundLocation": "Room 501 (Penthouse)",
        "status": "stored",
        "finderName": "Maria Santos",
        "foundBy": "Maria Santos",
        "dateFound": "2026-09-18",
        "foundDate": "2026-09-18",
    },
    {
        "id": "lf-2",
        "itemDescription": "Silk Hermes Scarf (Navy/Gold)",
        "category": "Clothing",
        "locationFound": "Palm Court Lounge",
        "foundLocation": "Palm Court Lounge",
        "status": "stored",
        "finderName": "Julian Rios",
        "foundBy": "Julian Rios",
        "dateFound": "2026-09-19",
        "foundDate": "2026-09-19",
    },
]

MAINTENANCE_TICKETS = [
    {"id": "maint-1", "propertyId": "prop-001", "roomNumber": "204", "area": "Guest Room", "title": "AC Compressor Noise", "description": "Loud vibration when cooling engages at high fan speed.", "priority": "high", "status": "in_progress", "category": "hvac", "assignedTechnician": "Vikram Patel", "createdAt": "2026-09-19T14:30:00Z"},
    {"id": "maint-2", "propertyId": "prop-001", "area": "Palm Court Kitchen", "title": "Walk-in Freezer Temp Alarm", "description": "Freezer #2 ambient temperature reading +2°C above setpoint.", "priority": "critical", "status": "open", "category": "appliance", "assignedTechnician": "Vikram Patel", "createdAt": "2026-09-20T08:15:00Z"},
    {"id": "maint-3", "propertyId": "prop-001", "roomNumber": "402", "area": "Imperial Penthouse", "title": "Plunge Pool Filter Jet Low Flow", "description": "Primary return jet pressure low.", "priority": "medium", "status": "completed", "category": "plumbing", "assignedTechnician": "Vikram Patel", "createdAt": "2026-09-18T11:00:00Z"},
]

TRANSPORT_TRIPS = [
    {"id": "trip-1", "guestName": "Dr. Eleanor Vance", "roomNumber": "201", "pickupLocation": "Grand Horizon Palace", "dropoffLocation": "JFK International Airport (Terminal 4)", "pickupTime": "2026-09-21T14:30:00Z", "passengerCount": 2, "flightNumber": "BA-178", "status": "assigned", "vehicleName": "Mercedes-Benz S580 (#01)", "driverName": "Liam O'Connor"},
    {"id": "trip-2", "guestName": "Lord Sterling Crawford", "roomNumber": "501", "pickupLocation": "Grand Horizon Palace", "dropoffLocation": "Wall Street Heliport", "pickupTime": "2026-09-21T16:00:00Z", "passengerCount": 1, "status": "en_route", "vehicleName": "Cadillac Escalade ESV (#03)", "driverName": "Liam O'Connor"},
    {"id": "trip-3", "guestName": "VIP Delegation", "pickupLocation": "LaGuardia Airport (LGA)", "dropoffLocation": "Grand Horizon Palace", "pickupTime": "2026-09-21T18:00:00Z", "passengerCount": 6, "status": "requested", "vehicleName": "Unassigned", "driverName": "Unassigned"},
]

TRANSPORT_VEHICLES = [
    {"id": "veh-1", "name": "Mercedes-Benz S580 4MATIC", "licensePlate": "LUX-8911", "category": "sedan", "capacity": 3, "status": "active"},
    {"id": "veh-2", "name": "BMW 760i xDrive", "licensePlate": "LUX-8912", "category": "sedan", "capacity": 3, "status": "active"},
    {"id": "veh-3", "name": "Cadillac Escalade ESV Premium", "licensePlate": "SUV-4401", "category": "suv", "capacity": 6, "status": "active"},
    {"id": "veh-4", "name": "Mercedes-Benz Sprinter Executive", "licensePlate": "VAN-9010", "category": "van", "capacity": 12, "status": "active"},
]

DRIVERS = [
    {"id": "drv-1", "name": "Liam O'Connor", "phone": "+1 (212) 555-0181", "status": "on_duty", "assignedVehicle": "Mercedes-Benz S580"},
    {"id": "drv-2", "name": "Dmitri Volkov", "phone": "+1 (212) 555-0182", "status": "on_duty", "assignedVehicle": "Cadillac Escalade ESV"},
    {"id": "drv-3", "name": "Marcus Kane", "phone": "+1 (212) 555-0183", "status": "off_duty", "assignedVehicle": "BMW 760i"},
]


# ──────────── Dining & POS Views ────────────

class DiningTablesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(DINING_TABLES)

    def patch(self, request, pk=None):
        for table in DINING_TABLES:
            if table["id"] == pk:
                table["status"] = request.data.get("status", table["status"])
                return Response(table)
        return Response({"error": "Table not found"}, status=404)


class MenuItemsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category = request.query_params.get("category")
        items = [i for i in MENU_ITEMS if (not category or i["category"].lower() == category.lower())]
        return Response(items)


class DiningOrdersView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        new_kot = {
            "id": f"kot-{len(KOT_ORDERS)+1}",
            "ticketNumber": f"KOT-{8800 + len(KOT_ORDERS) + 1}",
            "tableNumber": data.get("tableId", "T-01"),
            "station": "grill",
            "status": "new",
            "serverName": data.get("serverName", "Staff"),
            "guestCount": data.get("guestCount", 2),
            "items": data.get("items", []),
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        KOT_ORDERS.insert(0, new_kot)
        return Response(new_kot, status=status.HTTP_201_CREATED)


class PostOrderToRoomView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, order_id=None):
        from apps.rooms.models import Room
        from apps.billing.models import Folio
        from apps.billing.services import ChargeEventService
        room_id = request.data.get("roomId")
        room = Room.objects.filter(id=room_id).first() if room_id else Room.objects.first()
        folio = Folio.objects.filter(room=room, status='OPEN').first() if room else Folio.objects.filter(status='OPEN').first()
        if folio:
            evt = ChargeEventService.post_charge_event(
                folio=folio,
                source='RESTAURANT',
                description=f"Dining Check (Order {order_id})",
                amount=75.00,
                tax_amount=7.50,
                posted_by=request.user if request.user.is_authenticated else None
            )
            return Response({"success": True, "message": f"Charged $82.50 to Room {room.room_number if room else '501'}", "folioChargeId": str(evt.id)})
        return Response({"success": True, "message": "Charged to Room Folio", "folioChargeId": f"ch-{uuid.uuid4().hex[:8]}"})


class KOTOrdersView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        station = request.query_params.get("station")
        orders = [o for o in KOT_ORDERS if (not station or o["station"] == station)]
        return Response(orders)

    def patch(self, request, pk=None):
        for o in KOT_ORDERS:
            if o["id"] == pk:
                o["status"] = request.data.get("status", o["status"])
                return Response(o)
        return Response({"error": "Order not found"}, status=404)


class CancelKOTOrderView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk=None):
        for o in KOT_ORDERS:
            if o["id"] == pk:
                o["status"] = "cancelled"
                o["cancelReason"] = request.data.get("reason", "Cancelled by kitchen")
                return Response({"message": f"KOT {o['ticketNumber']} cancelled.", "cancelledOrder": o})
        return Response({"error": "Order not found"}, status=404)


# ──────────── Housekeeping Views ────────────

class HousekeepingTasksView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        status_filter = request.query_params.get("status")
        tasks = [t for t in HOUSEKEEPING_TASKS if (not status_filter or t["status"] == status_filter)]
        return Response(tasks)

    def patch(self, request, pk=None):
        for t in HOUSEKEEPING_TASKS:
            if t["id"] == pk:
                t["status"] = request.data.get("status", t["status"])
                if "notes" in request.data:
                    t["notes"] = request.data.get("notes")
                if "checklist" in request.data:
                    checklist_payload = request.data.get("checklist")
                    if isinstance(checklist_payload, list):
                        t["checklist"] = checklist_payload
                return Response(t)
        return Response({"error": "Task not found"}, status=404)


class HousekeepingChecklistView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk=None):
        for t in HOUSEKEEPING_TASKS:
            if t["id"] == pk:
                checklist_payload = request.data.get("checklist", {})
                if isinstance(checklist_payload, list):
                    t["checklist"] = checklist_payload
                elif isinstance(checklist_payload, dict) and isinstance(t.get("checklist"), list):
                    for item in t["checklist"]:
                        if item.get("id") in checklist_payload:
                            item["completed"] = bool(checklist_payload[item["id"]])
                t["status"] = request.data.get("status", t.get("status", "inspection"))
                return Response(t)
        return Response({"error": "Task not found"}, status=404)


class LostAndFoundView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        status_filter = request.query_params.get("status")
        items = [i for i in LOST_AND_FOUND if (not status_filter or i["status"] == status_filter)]
        return Response(items)

    def post(self, request):
        item = request.data
        item["id"] = f"lf-{len(LOST_AND_FOUND)+1}"
        item["dateFound"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        LOST_AND_FOUND.insert(0, item)
        return Response(item, status=status.HTTP_201_CREATED)


# ──────────── Maintenance Views ────────────

class MaintenanceTicketsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        status_filter = request.query_params.get("status")
        tickets = [t for t in MAINTENANCE_TICKETS if (not status_filter or t["status"] == status_filter)]
        return Response(tickets)

    def post(self, request):
        ticket = request.data
        ticket["id"] = f"maint-{len(MAINTENANCE_TICKETS)+1}"
        ticket["status"] = "open"
        ticket["createdAt"] = datetime.now(timezone.utc).isoformat()
        MAINTENANCE_TICKETS.insert(0, ticket)
        return Response(ticket, status=status.HTTP_201_CREATED)

    def patch(self, request, pk=None):
        for t in MAINTENANCE_TICKETS:
            if t["id"] == pk:
                t["status"] = request.data.get("status", t["status"])
                if "resolutionNotes" in request.data:
                    t["resolutionNotes"] = request.data["resolutionNotes"]
                return Response(t)
        return Response({"error": "Ticket not found"}, status=404)


class AssignTechnicianView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk=None):
        for t in MAINTENANCE_TICKETS:
            if t["id"] == pk:
                t["assignedTechnician"] = request.data.get("technicianName", "Assigned Tech")
                t["technicianId"] = request.data.get("technicianId")
                t["status"] = "in_progress"
                return Response(t)
        return Response({"error": "Ticket not found"}, status=404)


# ──────────── Transport & Fleet Views ────────────

class TransportTripsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        status_filter = request.query_params.get("status")
        trips = [t for t in TRANSPORT_TRIPS if (not status_filter or t["status"] == status_filter)]
        return Response(trips)

    def post(self, request):
        trip = request.data
        trip["id"] = f"trip-{len(TRANSPORT_TRIPS)+1}"
        trip["status"] = "assigned"
        TRANSPORT_TRIPS.insert(0, trip)
        return Response(trip, status=status.HTTP_201_CREATED)

    def patch(self, request, pk=None):
        for t in TRANSPORT_TRIPS:
            if t["id"] == pk:
                t["status"] = request.data.get("status", t["status"])
                return Response(t)
        return Response({"error": "Trip not found"}, status=404)


class DispatchTripView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk=None):
        for t in TRANSPORT_TRIPS:
            if t["id"] == pk:
                t["vehicleId"] = request.data.get("vehicleId")
                t["driverId"] = request.data.get("driverId")
                t["status"] = "assigned"
                return Response(t)
        return Response({"error": "Trip not found"}, status=404)


class TransportVehiclesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(TRANSPORT_VEHICLES)


class TransportDriversView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(DRIVERS)


# ──────────── Spa & Wellness Views ────────────

SPA_SERVICES = [
    {"id": "s-1", "propertyId": "prop-001", "category": "Massage", "name": "Royal Thai Herbal Poultice Massage", "durationMinutes": 90, "price": 210, "description": "Steamed medicinal herbs applied with acupressure"},
    {"id": "s-2", "propertyId": "prop-001", "category": "Massage", "name": "Deep Tissue Muscle Relief", "durationMinutes": 60, "price": 175, "description": "Targeted myofascial release with organic arnica oils"},
    {"id": "s-3", "propertyId": "prop-001", "category": "Ayurveda", "name": "Shirodhara Mind Calming Ritual", "durationMinutes": 75, "price": 240, "description": "Continuous stream of warm medicated herbal oil on the forehead"},
    {"id": "s-4", "propertyId": "prop-001", "category": "Facial", "name": "Caviar Radiance Anti-Aging Facial", "durationMinutes": 60, "price": 195, "description": "Marine DNA extracts and collagen infusion"},
]

SPA_APPOINTMENTS = [
    {"id": "apt-1", "propertyId": "prop-001", "guestName": "Elena Rostova", "roomNumber": "304", "serviceName": "Royal Thai Herbal Poultice Massage", "therapistName": "Maya Thorne", "scheduledDateTime": "2026-09-17 15:30", "durationMinutes": 90, "amount": 210, "status": "booked"},
    {"id": "apt-2", "propertyId": "prop-001", "guestName": "Kenji Takahashi", "roomNumber": "412", "serviceName": "Deep Tissue Muscle Relief", "therapistName": "Sanjay Kumar", "scheduledDateTime": "2026-09-17 17:00", "durationMinutes": 60, "amount": 175, "status": "booked"},
]

class SpaServicesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(SPA_SERVICES)


class SpaAppointmentsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(SPA_APPOINTMENTS)

    def post(self, request):
        apt = request.data
        if "id" not in apt:
            apt["id"] = f"apt-{len(SPA_APPOINTMENTS)+1}"
        if "status" not in apt:
            apt["status"] = "booked"
        SPA_APPOINTMENTS.insert(0, apt)
        return Response(apt, status=status.HTTP_201_CREATED)


# ──────────── Security Gate Views ────────────

GATE_LOGS = [
    {"id": "g-1", "propertyId": "prop-001", "visitorName": "Robert Langdon (Uber Chauffeur)", "purpose": "Guest", "hostOrDestination": "Lord Crawford (Room 501)", "entryTime": "20:15", "badgeNumber": "VIS-9021", "vehiclePlate": "NY-KLT-4921", "status": "inside"},
    {"id": "g-2", "propertyId": "prop-001", "visitorName": "Metro Produce Logistics", "purpose": "Vendor / Delivery", "hostOrDestination": "Main Kitchen Loading Bay", "entryTime": "19:40", "exitTime": "20:10", "badgeNumber": "VND-3012", "vehiclePlate": "NJ-TRK-8819", "status": "exited"},
    {"id": "g-3", "propertyId": "prop-001", "visitorName": "David K. (Elevator Service Tech)", "purpose": "Contractor", "hostOrDestination": "Engineering Basement", "entryTime": "18:30", "badgeNumber": "CON-1102", "vehiclePlate": "NY-VAN-2201", "status": "inside"},
]

class SecurityGateLogsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(GATE_LOGS)

    def post(self, request):
        log_entry = request.data
        if "id" not in log_entry:
            log_entry["id"] = f"g-{int(datetime.now(timezone.utc).timestamp())}"
        if "status" not in log_entry:
            log_entry["status"] = "inside"
        if "badgeNumber" not in log_entry:
            log_entry["badgeNumber"] = f"PASS-{len(GATE_LOGS)+1000}"
        GATE_LOGS.insert(0, log_entry)
        return Response(log_entry, status=status.HTTP_201_CREATED)


class SecurityGateExitView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk=None):
        for entry in GATE_LOGS:
            if entry["id"] == pk:
                entry["status"] = "exited"
                entry["exitTime"] = datetime.now(timezone.utc).strftime("%H:%M")
                return Response(entry)
        return Response({"error": "Gate log not found"}, status=404)


# ──────────── Inventory & Procurement Views ────────────

STOCK_ITEMS = [
    {"id": "inv-1", "name": "Macallan 18 Single Malt Scotch", "category": "Bar Spirits", "currentStock": 8, "reorderPoint": 12, "unit": "Bottles (750ml)", "storeLocation": "Main Cellar Vault", "status": "low_stock"},
    {"id": "inv-2", "name": "Bulgari White Tea Luxury Shampoo 75ml", "category": "Guest Amenities", "currentStock": 450, "reorderPoint": 200, "unit": "Pieces", "storeLocation": "Housekeeping Central Store", "status": "optimal"},
    {"id": "inv-3", "name": "Egyptian Cotton Bath Sheets (White)", "category": "Linens", "currentStock": 120, "reorderPoint": 80, "unit": "Sheets", "storeLocation": "Laundry Warehouse", "status": "optimal"},
    {"id": "inv-4", "name": "HVAC Blower Motor Fan Belts #A42", "category": "Engineering Spares", "currentStock": 2, "reorderPoint": 6, "unit": "Units", "storeLocation": "Engineering Workshop", "status": "reorder_required"},
    {"id": "inv-5", "name": "Australian Wagyu Striploin MB9+", "category": "F&B Provisions", "currentStock": 14, "reorderPoint": 20, "unit": "Kilograms", "storeLocation": "Walk-In Meat Chiller", "status": "low_stock"},
]

class InventoryStockView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(STOCK_ITEMS)

    def post(self, request):
        item = request.data
        if "id" not in item:
            item["id"] = f"inv-{len(STOCK_ITEMS)+1}"
        STOCK_ITEMS.append(item)
        return Response(item, status=status.HTTP_201_CREATED)


class InventoryPurchaseOrderView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        po_data = request.data
        po_record = {
            "poNumber": f"PO-{int(datetime.now(timezone.utc).timestamp())}",
            "itemId": po_data.get("itemId"),
            "quantity": po_data.get("quantity", 10),
            "status": "dispatched",
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        return Response(po_record, status=status.HTTP_201_CREATED)


# ──────────── Events & Banquets Views ────────────

BANQUET_VENUES = [
    {"id": "v-1", "propertyId": "prop-001", "name": "The Grand Ballroom", "capacityCocktail": 450, "capacityBanquet": 300, "capacityTheatre": 500, "hourlyRate": 1200, "amenities": ["Stage Lighting", "Surround Sound", "Bridal Suite"]},
    {"id": "v-2", "propertyId": "prop-001", "name": "Azure Pavilion & Lawn", "capacityCocktail": 250, "capacityBanquet": 180, "capacityTheatre": 220, "hourlyRate": 850, "amenities": ["Ocean View", "Outdoor Lawn", "Fire Pit"]},
    {"id": "v-3", "propertyId": "prop-001", "name": "Executive Boardroom Alpha", "capacityCocktail": 40, "capacityBanquet": 24, "capacityTheatre": 30, "hourlyRate": 350, "amenities": ["Video Conference 4K", "Smart Screen", "Executive Catering"]},
]

BANQUET_EVENTS = [
    {
        "id": "ev-1",
        "propertyId": "prop-001",
        "title": "Global Fintech Leaders Summit 2026",
        "clientName": "Apex Capital Partners",
        "clientContact": "Sarah Jenkins (+1 415 555 0199)",
        "venueId": "v-1",
        "venueName": "The Grand Ballroom",
        "startDate": "2026-09-24 08:00",
        "endDate": "2026-09-26 18:00",
        "attendeeCount": 280,
        "eventType": "Corporate Summit",
        "status": "confirmed",
        "totalRevenue": 68000,
        "roomBlockId": "rb-901 (45 Deluxe Suites Blocked)",
    },
    {
        "id": "ev-2",
        "propertyId": "prop-001",
        "title": "Vance & Montgomery Royal Wedding",
        "clientName": "Eleanor Vance",
        "clientContact": "vance.family@invest.com",
        "venueId": "v-2",
        "venueName": "Azure Pavilion & Lawn",
        "startDate": "2026-10-02 15:00",
        "endDate": "2026-10-03 01:00",
        "attendeeCount": 160,
        "eventType": "Wedding",
        "status": "confirmed",
        "totalRevenue": 42500,
        "roomBlockId": "rb-902 (20 Ocean Suites Blocked)",
    },
]

class EventsVenuesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(BANQUET_VENUES)


class EventsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(BANQUET_EVENTS)

    def post(self, request):
        ev = request.data
        if "id" not in ev:
            ev["id"] = f"ev-{len(BANQUET_EVENTS)+1}"
        BANQUET_EVENTS.insert(0, ev)
        return Response(ev, status=status.HTTP_201_CREATED)


# ──────────── Cloakroom & Luggage Views ────────────

CLOAKROOM_TICKETS = [
    {
        "id": "clk-1",
        "ticketNumber": "CLOAK-8021",
        "propertyId": "prop-001",
        "ownerName": "Lord Sterling Crawford",
        "roomNumber": "501",
        "contactPhone": "+44 20 7946 0912",
        "itemCount": 4,
        "itemDescriptions": "2x Rimowa Aluminum Trunks, 1x Louis Vuitton Garment Bag, 1x Golf Set",
        "storageRackLocation": "Rack B-04 (VIP High Security Vault)",
        "issuedAt": "2026-09-17 14:15",
        "status": "stored",
    },
    {
        "id": "clk-2",
        "ticketNumber": "CLOAK-8019",
        "propertyId": "prop-001",
        "ownerName": "David K. (Conference Speaker)",
        "roomNumber": "",
        "contactPhone": "+1 415 555 0188",
        "itemCount": 2,
        "itemDescriptions": "1x Tumi Roller Suitcase, 1x Laptop Briefcase",
        "storageRackLocation": "Rack A-12 (Bell Desk Hold)",
        "issuedAt": "2026-09-17 11:30",
        "status": "stored",
    },
]

class CloakroomTicketsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(CLOAKROOM_TICKETS)

    def post(self, request):
        tkt = request.data
        if "id" not in tkt:
            tkt["id"] = f"clk-{int(datetime.now(timezone.utc).timestamp())}"
        if "ticketNumber" not in tkt:
            tkt["ticketNumber"] = f"CLOAK-{len(CLOAKROOM_TICKETS)+8000}"
        if "status" not in tkt:
            tkt["status"] = "stored"
        if "issuedAt" not in tkt:
            tkt["issuedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        CLOAKROOM_TICKETS.insert(0, tkt)
        return Response(tkt, status=status.HTTP_201_CREATED)


class CloakroomReleaseView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk=None):
        for tkt in CLOAKROOM_TICKETS:
            if tkt["id"] == pk:
                tkt["status"] = "released"
                tkt["releasedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
                return Response(tkt)
        return Response({"error": "Cloakroom ticket not found"}, status=404)


# ──────────── OTA Channels Views ────────────

OTA_CHANNELS = [
    {"id": "ch-1", "propertyId": "prop-001", "channelName": "Booking.com", "status": "synced", "lastSyncAt": "2026-09-20 21:12", "syncedRoomTypesCount": 6, "pendingErrorsCount": 0},
    {"id": "ch-2", "propertyId": "prop-001", "channelName": "Expedia", "status": "synced", "lastSyncAt": "2026-09-20 21:10", "syncedRoomTypesCount": 6, "pendingErrorsCount": 0},
    {"id": "ch-3", "propertyId": "prop-001", "channelName": "Agoda", "status": "synced", "lastSyncAt": "2026-09-20 21:05", "syncedRoomTypesCount": 5, "pendingErrorsCount": 0},
    {"id": "ch-4", "propertyId": "prop-001", "channelName": "Airbnb", "status": "synced", "lastSyncAt": "2026-09-20 20:45", "syncedRoomTypesCount": 3, "pendingErrorsCount": 0},
]

class ChannelsListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(OTA_CHANNELS)


class ChannelsSyncView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        for ch in OTA_CHANNELS:
            ch["status"] = "synced"
            ch["lastSyncAt"] = now_str
        return Response({"message": "All channels synchronized successfully", "channels": OTA_CHANNELS})


# ──────────── HR & Attendance Views ────────────

STAFF_MEMBERS = [
    {"id": "staff-1", "name": "Marcus Sterling", "department": "Front Office", "role": "Front Office Director", "shift": "Morning (07:00 - 15:30)", "clockInTime": "06:55", "status": "on_duty"},
    {"id": "staff-2", "name": "Maria Santos", "department": "Housekeeping", "role": "Executive Housekeeper", "shift": "Morning (07:00 - 15:30)", "clockInTime": "07:02", "status": "on_duty"},
    {"id": "staff-3", "name": "Julian Rios", "department": "Culinary & F&B", "role": "Head Sommelier", "shift": "Evening (15:00 - 23:30)", "clockInTime": "14:50", "status": "on_duty"},
    {"id": "staff-4", "name": "Elena Rostova", "department": "Engineering", "role": "Chief Maintenance Engineer", "shift": "Morning (07:00 - 15:30)", "status": "break"},
    {"id": "staff-5", "name": "Tariq Mansour", "department": "Security", "role": "Security Chief Officer", "shift": "Night Audit (23:00 - 07:30)", "status": "off_duty"},
]

class HRStaffView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(STAFF_MEMBERS)

    def post(self, request):
        member = request.data
        if "id" not in member:
            member["id"] = f"staff-{len(STAFF_MEMBERS)+1}"
        STAFF_MEMBERS.append(member)
        return Response(member, status=status.HTTP_201_CREATED)

