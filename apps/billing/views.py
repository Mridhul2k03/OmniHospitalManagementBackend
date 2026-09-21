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


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        from apps.payments.models import Payment
        model = Payment
        fields = '__all__'


class FolioSerializer(serializers.ModelSerializer):
    charge_events = ChargeEventSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    guest_name = serializers.CharField(source='guest.full_name', read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)
    reservation_code = serializers.CharField(source='reservation.confirmation_code', read_only=True)
    room_number = serializers.SerializerMethodField()

    class Meta:
        model = Folio
        fields = '__all__'
        read_only_fields = ('id', 'folio_number', 'total_charges', 'total_payments', 'balance', 'created_at', 'updated_at')

    def get_room_number(self, obj):
        try:
            if obj.reservation:
                res_room = obj.reservation.reservation_rooms.first()
                if res_room and res_room.allocated_room:
                    return res_room.allocated_room.room_number
        except Exception:
            pass
        return ''


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

    @action(detail=True, methods=['post'], url_path='void-charge')
    def void_charge(self, request, pk=None):
        """Voids a folio item. Requires mandatory audit explanation."""
        folio = self.get_object()
        charge_id = request.data.get('charge_id')
        void_reason = request.data.get('void_reason', '')

        if not charge_id:
            return Response(
                {'success': False, 'error': {'code': 'MISSING_FIELD', 'message': 'charge_id is required.'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            charge_event = folio.charge_events.get(id=charge_id)
        except ChargeEvent.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'Charge {charge_id} not found on this folio.'}},
                status=status.HTTP_404_NOT_FOUND
            )

        voided_event = ChargeEventService.void_charge_event(
            charge_event=charge_event,
            void_reason=void_reason,
            voided_by=request.user
        )

        return Response({
            'success': True,
            'message': f"Charge {voided_event.event_id} voided successfully.",
            'charge_event': ChargeEventSerializer(voided_event).data,
            'new_balance': float(folio.balance)
        })

    @action(detail=True, methods=['post'], url_path=r'charges/(?P<charge_id>[^/.]+)/void')
    def void_charge_nested(self, request, pk=None, charge_id=None):
        folio = self.get_object()
        void_reason = request.data.get('reason', 'Correction')
        try:
            charge_event = folio.charge_events.get(id=charge_id)
        except (ChargeEvent.DoesNotExist, Exception):
            charge_event = folio.charge_events.filter(event_id=charge_id).first()
            if not charge_event:
                return Response({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Charge not found'}}, status=status.HTTP_404_NOT_FOUND)

        voided_event = ChargeEventService.void_charge_event(
            charge_event=charge_event,
            void_reason=void_reason,
            voided_by=request.user if request.user.is_authenticated else None
        )
        return Response({
            'success': True,
            'message': f"Charge {voided_event.event_id} voided successfully.",
            'voidedCharge': ChargeEventSerializer(voided_event).data,
            'new_balance': float(folio.balance)
        })

    @action(detail=True, methods=['post'], url_path='payments')
    def settle_payment(self, request, pk=None):
        folio = self.get_object()
        amount = request.data.get('amount')
        method = (request.data.get('method') or 'CARD').upper()
        if method == 'CREDIT_CARD' or method == 'DEBIT_CARD':
            method = 'CARD'
        elif method == 'BANK_TRANSFER':
            method = 'BANK'
        reference = request.data.get('transactionReference', '')
        from decimal import Decimal
        from apps.payments.services import PaymentService
        payment = PaymentService.process_payment(
            organization=folio.organization,
            property_obj=folio.property,
            folio=folio,
            amount=Decimal(str(amount)),
            method=method,
            transaction_reference=reference,
            processed_by=request.user if request.user.is_authenticated else None
        )
        return Response({
            'success': True,
            'message': f"Payment of ${amount} applied successfully.",
            'payment_id': str(payment.id),
            'new_balance': float(folio.balance),
            'folio': FolioSerializer(folio).data
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
