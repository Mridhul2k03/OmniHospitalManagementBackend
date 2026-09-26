"""
Reservation serializers and viewsets.
"""
import uuid
from datetime import date
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsPropertyStaffOrAdmin, IsShareholderReadOnly
from .models import Reservation, ReservationRoom
from .services import ReservationService
from apps.guests.models import GuestProfile
from apps.properties.models import Property
from apps.rooms.models import RoomType


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
    property_id = serializers.UUIDField(required=False)
    propertyId = serializers.UUIDField(required=False)
    guest = serializers.DictField(required=False)
    guest_id = serializers.UUIDField(required=False)
    guestId = serializers.UUIDField(required=False)
    guest_first_name = serializers.CharField(required=False, allow_blank=True)
    guest_last_name = serializers.CharField(required=False, allow_blank=True)
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(required=False, allow_blank=True)
    room_type_id = serializers.UUIDField(required=False)
    roomTypeId = serializers.UUIDField(required=False)
    room_id = serializers.UUIDField(required=False)
    roomId = serializers.UUIDField(required=False)
    check_in_date = serializers.DateField(required=False)
    checkInDate = serializers.DateField(required=False)
    check_out_date = serializers.DateField(required=False)
    checkOutDate = serializers.DateField(required=False)
    total_adults = serializers.IntegerField(default=1, min_value=1, required=False)
    totalAdults = serializers.IntegerField(default=1, min_value=1, required=False)
    total_children = serializers.IntegerField(default=0, min_value=0, required=False)
    totalChildren = serializers.IntegerField(default=0, min_value=0, required=False)
    source = serializers.CharField(default='DIRECT', required=False)
    channel = serializers.CharField(required=False)
    special_requests = serializers.CharField(required=False, allow_blank=True)
    specialRequests = serializers.CharField(required=False, allow_blank=True)
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

        raw_guest = data.get('guest') or {}
        first_name = data.get('guest_first_name') or raw_guest.get('firstName') or raw_guest.get('first_name') or 'Valued'
        last_name = data.get('guest_last_name') or raw_guest.get('lastName') or raw_guest.get('last_name') or 'Guest'
        email = data.get('guest_email') or raw_guest.get('email') or f"guest-{uuid.uuid4().hex[:6]}@example.com"
        phone = data.get('guest_phone') or raw_guest.get('phone') or raw_guest.get('phoneNumber') or '+1 555-0100'

        check_in_date = data.get('check_in_date') or data.get('checkInDate')
        check_out_date = data.get('check_out_date') or data.get('checkOutDate')

        if not check_in_date or not check_out_date:
            return Response(
                {'success': False, 'error': {'code': 'MISSING_DATES', 'message': 'check_in_date and check_out_date are required.'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Resolve Room & RoomType
        specific_room_id = data.get('room_id') or data.get('roomId')
        allocated_room = None
        if specific_room_id:
            from apps.rooms.models import Room
            allocated_room = Room.objects.filter(id=specific_room_id).first()

        property_id = data.get('property_id') or data.get('propertyId')
        property_obj = None
        if property_id:
            property_obj = Property.objects.filter(id=property_id).first()
        if not property_obj and allocated_room:
            property_obj = allocated_room.property
        if not property_obj and hasattr(request.user, 'organization') and request.user.organization:
            property_obj = Property.objects.filter(organization=request.user.organization).first()
        if not property_obj:
            property_obj = Property.objects.first()

        if not property_obj:
            return Response({'success': False, 'error': {'code': 'NO_PROPERTY', 'message': 'No property configured in system.'}}, status=status.HTTP_400_BAD_REQUEST)

        # Resolve or Create GuestProfile
        guest_id = data.get('guest_id') or data.get('guestId')
        guest = None
        if guest_id:
            guest = GuestProfile.objects.filter(id=guest_id).first()
        if not guest:
            guest = GuestProfile.objects.filter(email=email).first()
            if not guest:
                guest = GuestProfile.objects.create(
                    organization=property_obj.organization,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone_number=phone,
                    id_document_type='PASSPORT',
                    id_document_number=f"DOC-{uuid.uuid4().hex[:6].upper()}",
                    vip_status=False
                )

        room_type_id = data.get('room_type_id') or data.get('roomTypeId')
        if not room_type_id and allocated_room:
            room_type_id = allocated_room.room_type_id
        if not room_type_id:
            rt = RoomType.objects.filter(property=property_obj).first()
            if not rt:
                rt = RoomType.objects.first()
            room_type_id = rt.id if rt else None

        if not room_type_id:
            return Response({'success': False, 'error': {'code': 'NO_ROOM_TYPE', 'message': 'No room category available.'}}, status=status.HTTP_400_BAD_REQUEST)

        organization = request.user.organization if (hasattr(request.user, 'organization') and request.user.organization) else property_obj.organization
        source = (data.get('channel') or data.get('source') or 'DIRECT').upper()

        reservation = ReservationService.create_reservation(
            organization=organization,
            property_obj=property_obj,
            guest=guest,
            room_type_id=room_type_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            total_adults=data.get('total_adults') or data.get('totalAdults') or 1,
            total_children=data.get('total_children') or data.get('totalChildren') or 0,
            source=source,
            special_requests=data.get('special_requests') or data.get('specialRequests') or '',
            idempotency_key=data.get('idempotency_key')
        )

        if allocated_room:
            res_room = reservation.reservation_rooms.first()
            if res_room:
                res_room.allocated_room = allocated_room
                res_room.save(update_fields=['allocated_room'])
            if (data.get('auto_check_in') or data.get('autoCheckIn')):
                from apps.frontoffice.services import FrontOfficeService
                FrontOfficeService.check_in(
                    reservation=reservation,
                    room=allocated_room,
                    checked_in_by=request.user if request.user.is_authenticated else None,
                    is_id_verified=True,
                    key_cards_issued=1
                )

        res_serializer = self.get_serializer(reservation)
        return Response({
            'success': True,
            'reservation': res_serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        reason = request.data.get('reason', 'Cancelled by operator')
        ReservationService.cancel_reservation(reservation)
        return Response({
            'success': True,
            'message': f"Reservation {reservation.confirmation_code} cancelled successfully. Reason: {reason}",
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
        return self._perform_digital_checkin(request, self.get_object())

    @action(detail=True, methods=['post'], url_path='digital-check-in')
    def digital_check_in_detail(self, request, pk=None):
        return self._perform_digital_checkin(request, self.get_object())

    @action(detail=False, methods=['post'], url_path='digital-check-in')
    def digital_check_in_collection(self, request):
        code = request.data.get('confirmationCode') or request.data.get('confirmation_code') or request.data.get('reservation_code')
        if not code:
            return Response({'success': False, 'error': {'code': 'MISSING_CODE', 'message': 'confirmationCode is required'}}, status=status.HTTP_400_BAD_REQUEST)
        reservation = Reservation.objects.filter(confirmation_code__iexact=code).first()
        if not reservation:
            return Response({'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'Reservation {code} not found'}}, status=status.HTTP_404_NOT_FOUND)
        return self._perform_digital_checkin(request, reservation)

    def _perform_digital_checkin(self, request, reservation):
        from apps.rooms.models import Room
        from apps.frontoffice.services import FrontOfficeService
        from apps.frontoffice.models import StayLog

        res_room = reservation.reservation_rooms.first()
        room = res_room.allocated_room if (res_room and res_room.allocated_room) else Room.objects.filter(property=reservation.property, status='AVAILABLE').first()
        if not room:
            room = Room.objects.filter(property=reservation.property).first()

        stay_log = None
        if reservation.status in ('CONFIRMED', 'PENDING'):
            stay_log = FrontOfficeService.check_in(
                reservation=reservation,
                room=room,
                checked_in_by=None,
                is_id_verified=True,
                signature_url=request.data.get('signatureBase64', ''),
                key_cards_issued=1
            )
        else:
            stay_log = StayLog.objects.filter(reservation=reservation).first()
            if stay_log and request.data.get('signatureBase64'):
                stay_log.signature_url = request.data.get('signatureBase64')
                stay_log.save(update_fields=['signature_url'])

        room_no = (room.room_number if room else (stay_log.room.room_number if stay_log and stay_log.room else "101"))
        return Response({
            'status': 'confirmed',
            'message': f"Digital pre-arrival check-in confirmed for {reservation.confirmation_code}. Room {room_no}.",
            'qrCode': f"OMNI-KEY-{reservation.confirmation_code}-{room_no}",
            'roomNumber': room_no,
            'data': {
                'stay_id': str(stay_log.id) if stay_log else '',
                'room_number': room_no,
                'guest_name': reservation.guest.full_name,
            }
        })

