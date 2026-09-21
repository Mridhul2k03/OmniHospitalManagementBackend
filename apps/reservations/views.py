"""
Reservation serializers and viewsets.
"""
from datetime import date
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

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs.get(lookup_url_kwarg)
        import uuid
        try:
            uuid.UUID(str(lookup_value))
            return super().get_object()
        except ValueError:
            queryset = self.filter_queryset(self.get_queryset())
            obj = queryset.filter(confirmation_code__iexact=lookup_value).first()
            if not obj:
                from django.http import Http404
                raise Http404(f"No reservation matching {lookup_value}")
            self.check_object_permissions(self.request, obj)
            return obj

    @action(detail=False, methods=['get'], url_path='today-arrivals')
    def today_arrivals(self, request):
        """Optimized query for arrivals expected on the current operational date."""
        today = date.today()
        qs = self.get_queryset().filter(
            check_in_date=today,
            status__in=['CONFIRMED', 'PENDING']
        ).select_related('guest', 'property')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'], url_path='today-departures')
    def today_departures(self, request):
        """Departures scheduled for today."""
        today = date.today()
        qs = self.get_queryset().filter(
            check_out_date=today,
            status='IN_HOUSE'
        ).select_related('guest', 'property')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'], url_path='in-house')
    def in_house(self, request):
        """In-house guests manifest."""
        qs = self.get_queryset().filter(status='IN_HOUSE').select_related('guest', 'property')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=True, methods=['post'], url_path='check-in')
    def check_in(self, request, pk=None):
        reservation = self.get_object()
        room_id = request.data.get('assignedRoomId') or request.data.get('room_id')
        from apps.rooms.models import Room
        from apps.frontoffice.services import FrontOfficeService
        if not room_id:
            res_room = reservation.reservation_rooms.first()
            if res_room and res_room.allocated_room:
                room = res_room.allocated_room
            else:
                room = Room.objects.filter(property=reservation.property, status='AVAILABLE').first()
                if not room:
                    room = Room.objects.filter(property=reservation.property).first()
        else:
            room = Room.objects.get(id=room_id)

        stay_log = FrontOfficeService.check_in(
            reservation=reservation,
            room=room,
            checked_in_by=request.user if request.user.is_authenticated else None,
            is_id_verified=True,
            signature_url=request.data.get('signatureDataUrl', ''),
            key_cards_issued=request.data.get('keyCardCount', 1)
        )
        return Response({
            'success': True,
            'message': f"Guest checked into Room {room.room_number}.",
            'reservation': self.get_serializer(reservation).data,
            'stay_id': str(stay_log.id),
        })

    @action(detail=True, methods=['post'], url_path='check-out')
    def check_out(self, request, pk=None):
        reservation = self.get_object()
        from apps.frontoffice.services import FrontOfficeService
        stay_log = FrontOfficeService.check_out(
            reservation=reservation,
            checked_out_by=request.user if request.user.is_authenticated else None
        )
        return Response({
            'success': True,
            'message': f"Reservation {reservation.confirmation_code} successfully checked out.",
            'reservation': self.get_serializer(reservation).data,
        })

    @action(detail=True, methods=['post'], url_path='digital-checkin')
    def digital_checkin(self, request, pk=None):
        reservation = self.get_object()
        from apps.rooms.models import Room
        from apps.frontoffice.services import FrontOfficeService
        res_room = reservation.reservation_rooms.first()
        room = res_room.allocated_room if (res_room and res_room.allocated_room) else Room.objects.filter(property=reservation.property, status='AVAILABLE').first()
        if not room:
            room = Room.objects.filter(property=reservation.property).first()

        stay_log = FrontOfficeService.check_in(
            reservation=reservation,
            room=room,
            checked_in_by=None,
            is_id_verified=True,
            signature_url=request.data.get('signatureBase64', ''),
            key_cards_issued=1
        )
        return Response({
            'status': 'confirmed',
            'message': f"Digital pre-arrival check-in confirmed for {reservation.confirmation_code}. Room {room.room_number}.",
            'qrCode': f"OMNI-KEY-{reservation.confirmation_code}-{room.room_number}",
            'data': {
                'stay_id': str(stay_log.id),
                'room_number': room.room_number,
                'guest_name': reservation.guest.full_name,
            }
        })

