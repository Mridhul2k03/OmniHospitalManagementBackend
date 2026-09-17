"""
Payments serializers and viewsets.
"""
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsPropertyStaffOrAdmin, IsShareholderReadOnly
from .models import Payment, PaymentRefund
from .services import PaymentService
from apps.billing.models import Folio


class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRefund
        fields = '__all__'
        read_only_fields = ('id', 'refund_transaction_id', 'created_at', 'updated_at')


class PaymentSerializer(serializers.ModelSerializer):
    refunds = PaymentRefundSerializer(many=True, read_only=True)
    guest_name = serializers.CharField(source='guest.full_name', read_only=True)
    folio_number = serializers.CharField(source='folio.folio_number', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('id', 'transaction_id', 'status', 'paid_at', 'created_at', 'updated_at')


class CreatePaymentRequestSerializer(serializers.Serializer):
    folio_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.CharField(default='CREDIT_CARD')
    gateway = serializers.CharField(default='MANUAL_CASH')
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True)


class RefundPaymentRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    reason = serializers.CharField()


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]
    filterset_fields = ['property', 'folio', 'payment_method', 'status', 'gateway']
    search_fields = ['transaction_id', 'guest__first_name', 'guest__last_name']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return Payment.objects.none()
        return Payment.objects.for_user(user)

    def create(self, request, *args, **kwargs):
        serializer = CreatePaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        folio = Folio.objects.get(id=data['folio_id'])

        payment = PaymentService.record_payment(
            folio=folio,
            amount=data['amount'],
            payment_method=data.get('payment_method', 'CREDIT_CARD'),
            gateway=data.get('gateway', 'MANUAL_CASH'),
            transaction_id=data.get('transaction_id'),
            idempotency_key=data.get('idempotency_key'),
            recorded_by=request.user
        )

        return Response({
            'success': True,
            'payment': PaymentSerializer(payment).data,
            'folio_balance': float(folio.balance)
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='refund')
    def refund(self, request, pk=None):
        payment = self.get_object()
        serializer = RefundPaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        refund = PaymentService.process_refund(
            payment=payment,
            amount=data['amount'],
            reason=data['reason'],
            processed_by=request.user
        )

        return Response({
            'success': True,
            'refund': PaymentRefundSerializer(refund).data,
            'payment_status': payment.status,
            'folio_balance': float(payment.folio.balance)
        })
