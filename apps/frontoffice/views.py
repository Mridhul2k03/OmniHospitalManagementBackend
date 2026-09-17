"""
Front office serializers and viewsets.
"""
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsPropertyStaffOrAdmin, IsShareholderReadOnly
from .models import StayLog
from .services import FrontOfficeService
from apps.reservations.models import Reservation
from apps.rooms.models import Room


class StayLogSerializer(serializers.ModelSerializer):
    guest_name = serializers.CharField(source='guest.full_name', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    confirmation_code = serializers.CharField(source='reservation.confirmation_code', read_only=True)

    class Meta:
        model = StayLog
        fields = '__all__'
        read_only_fields = ('id', 'check_in_time', 'check_out_time', 'created_at', 'updated_at')


class CheckInRequestSerializer(serializers.Serializer):
    reservation_id = serializers.UUIDField()
    room_id = serializers.UUIDField()
    is_id_verified = serializers.BooleanField(default=True)
    signature_url = serializers.URLField(required=False, allow_blank=True)
    key_cards_issued = serializers.IntegerField(default=1, min_value=1)


class CheckOutRequestSerializer(serializers.Serializer):
    reservation_id = serializers.UUIDField()


class RoomTransferRequestSerializer(serializers.Serializer):
    reservation_id = serializers.UUIDField()
    new_room_id = serializers.UUIDField()


class FrontOfficeViewSet(viewsets.GenericViewSet):
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]
    serializer_class = StayLogSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return StayLog.objects.none()
        return StayLog.objects.for_user(user)

    @action(detail=False, methods=['post'], url_path='check-in')
    def check_in(self, request):
        serializer = CheckInRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        reservation = Reservation.objects.get(id=data['reservation_id'])
        room = Room.objects.get(id=data['room_id'])

        stay_log = FrontOfficeService.check_in(
            reservation=reservation,
            room=room,
            checked_in_by=request.user,
            is_id_verified=data['is_id_verified'],
            signature_url=data.get('signature_url', ''),
            key_cards_issued=data.get('key_cards_issued', 1)
        )

        return Response({
            'success': True,
            'stay_log': StayLogSerializer(stay_log).data,
            'reservation_status': reservation.status,
            'room_status': room.status
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='check-out')
    def check_out(self, request):
        serializer = CheckOutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        reservation = Reservation.objects.get(id=data['reservation_id'])

        stay_log = FrontOfficeService.check_out(
            reservation=reservation,
            checked_out_by=request.user
        )

        return Response({
            'success': True,
            'message': f"Reservation {reservation.confirmation_code} checked out successfully.",
            'reservation_status': reservation.status,
            'stay_log': StayLogSerializer(stay_log).data if stay_log else None
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='transfer-room')
    def transfer_room(self, request):
        serializer = RoomTransferRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        reservation = Reservation.objects.get(id=data['reservation_id'])
        new_room = Room.objects.get(id=data['new_room_id'])

        stay_log = FrontOfficeService.transfer_room(
            reservation=reservation,
            new_room=new_room
        )

        return Response({
            'success': True,
            'message': f"Guest transferred to Room {new_room.room_number}.",
            'stay_log': StayLogSerializer(stay_log).data
        }, status=status.HTTP_200_OK)


class StayLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StayLogSerializer
    permission_classes = [IsPropertyStaffOrAdmin, IsShareholderReadOnly]
    filterset_fields = ['property', 'room', 'is_id_verified']
    search_fields = ['reservation__confirmation_code', 'guest__first_name', 'guest__last_name']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return StayLog.objects.none()
        return StayLog.objects.for_user(user)
