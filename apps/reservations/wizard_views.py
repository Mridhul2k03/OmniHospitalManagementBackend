"""
Contactless Digital Check-In Wizard endpoint.
"""
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.reservations.models import Reservation
from apps.frontoffice.services import FrontOfficeService


class EmergencyContactSerializer(serializers.Serializer):
    name = serializers.CharField()
    phone = serializers.CharField()
    relationship = serializers.CharField(required=False, allow_blank=True)


class CheckInWizardSerializer(serializers.Serializer):
    reservation_code = serializers.CharField()
    guest_verified = serializers.BooleanField(default=True)
    id_document_image = serializers.CharField(required=False, allow_blank=True)
    emergency_contact = EmergencyContactSerializer(required=False)
    digital_signature = serializers.CharField(required=False, allow_blank=True)


class CheckInWizardView(APIView):
    """
    Contactless check-in wizard submission from mobile / self-service kiosk.
    POST /api/v1/check-in/wizard-submit/
    """
    permission_classes = [AllowAny]
    serializer_class = CheckInWizardSerializer

    def post(self, request):
        serializer = CheckInWizardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            reservation = Reservation.objects.get(
                confirmation_code=data['reservation_code']
            )
        except Reservation.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': f"Reservation {data['reservation_code']} not found."}},
                status=status.HTTP_404_NOT_FOUND
            )

        if reservation.status not in ('CONFIRMED', 'PENDING'):
            return Response(
                {'success': False, 'error': {'code': 'INVALID_STATE', 'message': f"Reservation status is {reservation.status}. Cannot check in."}},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find first available room of the reserved type
        res_room = reservation.reservation_rooms.first()
        if not res_room:
            return Response(
                {'success': False, 'error': {'code': 'NO_ROOM', 'message': 'No room assignment found for this reservation.'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.rooms.models import Room
        room = res_room.allocated_room
        if not room:
            room = Room.objects.filter(
                property=reservation.property,
                room_type=res_room.room_type,
                status='AVAILABLE'
            ).first()
            if not room:
                return Response(
                    {'success': False, 'error': {'code': 'NO_AVAILABLE_ROOM', 'message': 'No available room of the reserved type.'}},
                    status=status.HTTP_400_BAD_REQUEST
                )

        stay_log = FrontOfficeService.check_in(
            reservation=reservation,
            room=room,
            checked_in_by=None,
            is_id_verified=data.get('guest_verified', True),
            signature_url=data.get('digital_signature', ''),
            key_cards_issued=1
        )

        return Response({
            'success': True,
            'message': f"Contactless check-in completed for {reservation.confirmation_code}.",
            'data': {
                'stay_id': str(stay_log.id),
                'room_number': room.room_number,
                'guest_name': reservation.guest.full_name,
                'check_in_time': stay_log.check_in_time.isoformat(),
            }
        }, status=status.HTTP_200_OK)
