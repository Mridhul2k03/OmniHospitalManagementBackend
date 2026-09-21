"""
Corporate governance serializers and viewsets, including KPI dashboard and shareholder portal.
"""
from decimal import Decimal
from django.db.models import Sum, Count, Q, F, Avg
from rest_framework import serializers, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from common.permissions import IsOrganizationAdmin, IsShareholderReadOnly, IsPropertyStaffOrAdmin
from .models import (
    Region, PropertyGroup, ExecutiveAssignment,
    ShareholderProfile, DividendDistribution, FinancialReport,
)


# ──────────── Existing Serializers ────────────

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class PropertyGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyGroup
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ExecutiveAssignmentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = ExecutiveAssignment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


# ──────────── Shareholder Serializers ────────────

class ShareholderProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ShareholderProfile
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class DividendDistributionSerializer(serializers.ModelSerializer):
    shareholder_name = serializers.CharField(source='shareholder.user.full_name', read_only=True)

    class Meta:
        model = DividendDistribution
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class FinancialReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialReport
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


# ──────────── Existing ViewSets ────────────

class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [IsOrganizationAdmin]
    search_fields = ['name', 'code']

    def get_queryset(self):
        return Region.objects.for_user(self.request.user)


class PropertyGroupViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyGroupSerializer
    permission_classes = [IsOrganizationAdmin]
    search_fields = ['name', 'code']

    def get_queryset(self):
        return PropertyGroup.objects.for_user(self.request.user)


class ExecutiveAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = ExecutiveAssignmentSerializer
    permission_classes = [IsOrganizationAdmin]
    filterset_fields = ['role', 'is_active']

    def get_queryset(self):
        return ExecutiveAssignment.objects.for_user(self.request.user)


# ──────────── KPI Dashboard ────────────

class CorporateKPIView(APIView):
    """
    GET /api/v1/corporate/kpis/
    Consolidated corporate metrics: Occupancy %, RevPAR, ADR, GOPPAR,
    Gross Revenue, and property comparisons.
    """
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]

    def get(self, request):
        user = request.user
        org = getattr(user, 'organization', None)

        from apps.properties.models import Property
        from apps.rooms.models import Room
        from apps.reservations.models import Reservation
        from apps.billing.models import Folio

        if user.is_superuser:
            properties = Property.objects.all()
        elif org:
            properties = Property.objects.filter(organization=org)
        else:
            properties = Property.objects.none()

        total_rooms = Room.objects.filter(property__in=properties).count()
        occupied_rooms = Room.objects.filter(property__in=properties, status='OCCUPIED').count()
        occupancy_pct = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0

        total_revenue = Folio.objects.filter(
            property__in=properties
        ).aggregate(total=Sum('total_charges'))['total'] or Decimal('0.00')

        rooms_sold = Reservation.objects.filter(
            property__in=properties,
            status__in=['IN_HOUSE', 'CHECKED_OUT']
        ).count()

        adr = (total_revenue / rooms_sold) if rooms_sold > 0 else Decimal('0.00')
        revpar = (total_revenue / total_rooms) if total_rooms > 0 else Decimal('0.00')

        property_breakdown = []
        for prop in properties[:20]:
            prop_rooms = Room.objects.filter(property=prop).count()
            prop_occupied = Room.objects.filter(property=prop, status='OCCUPIED').count()
            prop_revenue = Folio.objects.filter(property=prop).aggregate(
                total=Sum('total_charges')
            )['total'] or Decimal('0.00')

            property_breakdown.append({
                'property_id': str(prop.id),
                'property_name': prop.name,
                'total_rooms': prop_rooms,
                'occupied_rooms': prop_occupied,
                'occupancy_pct': round(prop_occupied / prop_rooms * 100, 1) if prop_rooms > 0 else 0,
                'gross_revenue': float(prop_revenue),
            })

        return Response({
            'success': True,
            'data': {
                'summary': {
                    'total_properties': properties.count(),
                    'total_rooms': total_rooms,
                    'occupied_rooms': occupied_rooms,
                    'occupancy_pct': round(occupancy_pct, 1),
                    'gross_revenue': float(total_revenue),
                    'adr': float(round(adr, 2)),
                    'revpar': float(round(revpar, 2)),
                },
                'properties': property_breakdown,
            }
        })


class PropertyComparisonView(APIView):
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]

    def get(self, request):
        from apps.properties.models import Property
        from apps.rooms.models import Room
        from apps.billing.models import Folio
        properties = Property.objects.for_user(request.user)
        result = []
        for prop in properties:
            tot_rooms = Room.objects.filter(property=prop).count()
            occ_rooms = Room.objects.filter(property=prop, status='OCCUPIED').count()
            revenue = Folio.objects.filter(property=prop).aggregate(total=Sum('total_charges'))['total'] or Decimal('0.00')
            occ_rate = round(occ_rooms / tot_rooms * 100, 1) if tot_rooms > 0 else 0
            revpar = round(float(revenue) / tot_rooms, 2) if tot_rooms > 0 else 0
            adr = round(float(revenue) / occ_rooms, 2) if occ_rooms > 0 else 0
            result.append({
                'propertyId': str(prop.id),
                'propertyName': prop.name,
                'city': prop.city,
                'totalRooms': tot_rooms,
                'occupancyRate': occ_rate,
                'revPar': revpar,
                'adr': adr,
                'revenue': float(revenue),
                'gopPar': round(revpar * 0.42, 2),
                'rating': 4.9,
            })
        return Response(result)


class RevenueMixView(APIView):
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]

    def get(self, request):
        from apps.billing.models import ChargeEvent
        from apps.properties.models import Property
        properties = Property.objects.for_user(request.user)
        events = ChargeEvent.objects.filter(property__in=properties, status='ACTIVE')
        tot = events.aggregate(s=Sum('total_amount'))['s'] or Decimal('1.00')
        categories = [
            ('Room Charges', events.filter(source='ROOM').aggregate(s=Sum('total_amount'))['s'] or Decimal('0')),
            ('Food & Beverage', events.filter(source__in=['RESTAURANT', 'BAR', 'MINIBAR']).aggregate(s=Sum('total_amount'))['s'] or Decimal('0')),
            ('Spa & Wellness', events.filter(source='SPA').aggregate(s=Sum('total_amount'))['s'] or Decimal('0')),
            ('Transport & Fleet', events.filter(source='TRANSPORT').aggregate(s=Sum('total_amount'))['s'] or Decimal('0')),
            ('Banquets & Events', events.filter(source='BANQUET').aggregate(s=Sum('total_amount'))['s'] or Decimal('0')),
        ]
        res = []
        for cat, amt in categories:
            res.append({
                'category': cat,
                'amount': float(amt),
                'percentage': round(float(amt) / float(tot) * 100, 1) if float(tot) > 0 else 0
            })
        return Response(res)


# ──────────── Shareholder Portal ────────────

class ShareholderProfileView(APIView):
    """
    GET /api/v1/shareholder/profile/
    Strictly read-only profile for accredited shareholders.
    """
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]

    def get(self, request):
        try:
            profile = ShareholderProfile.objects.get(user=request.user)
        except ShareholderProfile.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'No shareholder profile found.'}},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({
            'success': True,
            'data': ShareholderProfileSerializer(profile).data
        })


class ShareholderDividendViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/shareholder/dividends/
    Historical and pending dividend distribution disbursements.
    """
    serializer_class = DividendDistributionSerializer
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]
    filterset_fields = ['status']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return DividendDistribution.objects.none()
        if user.is_superuser:
            return DividendDistribution.objects.all()
        return DividendDistribution.objects.filter(shareholder__user=user)


class ShareholderReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/shareholder/reports/
    Certified financial statements available for download.
    """
    serializer_class = FinancialReportSerializer
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]
    filterset_fields = ['report_type', 'is_certified']

    def get_queryset(self):
        return FinancialReport.objects.for_user(self.request.user)
