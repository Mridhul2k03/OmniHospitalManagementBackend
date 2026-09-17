"""
Reservation serializers and viewsets.
"""
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsPropertyStaffOrAdmin, IsShareholderReadOnly
from .models import Reservation, ReservationRoom
from .services import ReservationService
from apps.guests.models import GuestProfile
from apps.properties.models import Property


class ReservationRoomSerializer(serializers.ModelSerializer):
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    room_number = serializers.CharField(source='allocated_room.room_number', read_only=True)

    class Meta:
        model = ReservationRoom
        fields = '__all__'


class ReservationSerializer(serializers.ModelSerializer):
    reservation_rooms = ReservationRoomSerializer(many=True, read_only=True)
    guest_name = serializers.CharField(source='guest.full_name', read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)
    total_nights = serializers.IntegerField(read_only=True)

    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ('id', 'confirmation_code', 'total_amount', 'created_at', 'updated_at')


class CreateReservationRequestSerializer(serializers.Serializer):
    property_id = serializers.UUIDField()
    guest_id = serializers.UUIDField()
    room_type_id = serializers.UUIDField()
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()
    total_adults = serializers.IntegerField(default=1, min_value=1)
    total_children = serializers.IntegerField(default=0, min_value=0)
    source = serializers.CharField(default='DIRECT')
    special_requests = serializers.CharField(required=False, allow_blank=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True)


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]
    filterset_fields = ['property', 'status', 'source', 'check_in_date', 'check_out_date']
    search_fields = ['confirmation_code', 'guest__first_name', 'guest__last_name', 'guest__email']

    def get_queryset(self):
        return Reservation.objects.for_user(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = CreateReservationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        property_obj = Property.objects.get(id=data['property_id'])
        guest = GuestProfile.objects.get(id=data['guest_id'])

        organization = request.user.organization if request.user.organization else property_obj.organization

        reservation = ReservationService.create_reservation(
            organization=organization,
            property_obj=property_obj,
            guest=guest,
            room_type_id=data['room_type_id'],
            check_in_date=data['check_in_date'],
            check_out_date=data['check_out_date'],
            total_adults=data.get('total_adults', 1),
            total_children=data.get('total_children', 0),
            source=data.get('source', 'DIRECT'),
            special_requests=data.get('special_requests', ''),
            idempotency_key=data.get('idempotency_key')
        )

        res_serializer = self.get_serializer(reservation)
        return Response({
            'success': True,
            'reservation': res_serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        ReservationService.cancel_reservation(reservation)
        return Response({
            'success': True,
            'message': f"Reservation {reservation.confirmation_code} cancelled successfully.",
            'status': reservation.status
        })
