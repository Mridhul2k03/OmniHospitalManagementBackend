"""
Billing serializers and viewsets.
"""
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsPropertyStaffOrAdmin, IsShareholderReadOnly
from .models import Folio, ChargeEvent, Invoice
from .services import FolioService, ChargeEventService


class ChargeEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeEvent
        fields = '__all__'
        read_only_fields = ('id', 'event_id', 'total_amount', 'created_at', 'updated_at')


class PostChargeRequestSerializer(serializers.Serializer):
    source = serializers.CharField(default='OTHER')
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    outlet_code = serializers.CharField(required=False, allow_blank=True)
    room_id = serializers.UUIDField(required=False, allow_null=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True)


class FolioSerializer(serializers.ModelSerializer):
    charge_events = ChargeEventSerializer(many=True, read_only=True)
    guest_name = serializers.CharField(source='guest.full_name', read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)

    class Meta:
        model = Folio
        fields = '__all__'
        read_only_fields = ('id', 'folio_number', 'total_charges', 'total_payments', 'balance', 'created_at', 'updated_at')


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class FolioViewSet(viewsets.ModelViewSet):
    serializer_class = FolioSerializer
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]
    filterset_fields = ['property', 'status', 'reservation']
    search_fields = ['folio_number', 'guest__first_name', 'guest__last_name']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return Folio.objects.none()
        return Folio.objects.for_user(user)

    @action(detail=True, methods=['post'], url_path='charges')
    def post_charge(self, request, pk=None):
        folio = self.get_object()
        serializer = PostChargeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        event = ChargeEventService.post_charge_event(
            folio=folio,
            source=data['source'],
            description=data['description'],
            amount=data['amount'],
            tax_amount=data.get('tax_amount', 0.00),
            outlet_code=data.get('outlet_code', ''),
            posted_by=request.user,
            idempotency_key=data.get('idempotency_key')
        )
        return Response({
            'success': True,
            'charge_event': ChargeEventSerializer(event).data,
            'new_balance': float(folio.balance)
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='close')
    def close_folio(self, request, pk=None):
        folio = self.get_object()
        FolioService.close_folio(folio)
        return Response({
            'success': True,
            'message': f"Folio {folio.folio_number} closed successfully.",
            'status': folio.status
        })


class ChargeEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChargeEventSerializer
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]
    filterset_fields = ['property', 'folio', 'source', 'status']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return ChargeEvent.objects.none()
        return ChargeEvent.objects.for_user(user)
