import uuid
from django.utils.text import slugify
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsPropertyStaffOrAdmin
from apps.properties.models import Property
from .models import RoomAmenity, RoomType, Room, RatePlan, RoomRate


class RoomAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomAmenity
        fields = '__all__'


class RoomTypeSerializer(serializers.ModelSerializer):
    amenities = RoomAmenitySerializer(many=True, read_only=True)
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all(), required=False, allow_null=True)
    code = serializers.SlugField(required=False)
    property_name = serializers.CharField(source='property.name', read_only=True)

    class Meta:
        model = RoomType
        fields = '__all__'
        validators = []


class RoomSerializer(serializers.ModelSerializer):
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    floor_name = serializers.CharField(source='floor.name', read_only=True)
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all(), required=False)
    room_type = serializers.PrimaryKeyRelatedField(queryset=RoomType.objects.all(), required=False)

    class Meta:
        model = Room
        fields = '__all__'


class RatePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatePlan
        fields = '__all__'


class RoomRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomRate
        fields = '__all__'


class RoomAmenityViewSet(viewsets.ModelViewSet):
    queryset = RoomAmenity.objects.all()
    serializer_class = RoomAmenitySerializer
    permission_classes = [IsPropertyStaffOrAdmin]


class RoomTypeViewSet(viewsets.ModelViewSet):
    serializer_class = RoomTypeSerializer
    permission_classes = [IsPropertyStaffOrAdmin]
    filterset_fields = ['property', 'is_active']
    search_fields = ['name', 'code']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return RoomType.objects.none()
        if user.is_superuser:
            return RoomType.objects.all()
        return RoomType.objects.filter(property__organization=user.organization)

    def perform_create(self, serializer):
        user = self.request.user
        property_obj = serializer.validated_data.get('property')
        if not property_obj:
            if hasattr(user, 'organization') and user.organization:
                property_obj = Property.objects.filter(organization=user.organization).first()
            if not property_obj:
                property_obj = Property.objects.first()

        name = serializer.validated_data.get('name', 'Room Type')
        code = serializer.validated_data.get('code')
        if not code:
            base_slug = slugify(name)[:24] or 'rt'
            code = f"{base_slug}-{str(uuid.uuid4())[:6]}"

        serializer.save(property=property_obj, code=code)


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsPropertyStaffOrAdmin]
    filterset_fields = ['property', 'room_type', 'status', 'is_active']
    search_fields = ['room_number']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return Room.objects.none()
        if user.is_superuser:
            return Room.objects.all()
        return Room.objects.filter(property__organization=user.organization)

    def perform_create(self, serializer):
        user = self.request.user
        role = getattr(user, 'role', '')
        allowed_roles = (
            'SUPER_ADMIN', 'ORG_ADMIN', 'PROPERTY_MANAGER',
            'PRESIDENT', 'VICE_PRESIDENT', 'CEO', 'OPERATIONS_DIRECTOR'
        )
        if not (user.is_superuser or role in allowed_roles):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrative or management personnel can create rooms.")

        property_obj = serializer.validated_data.get('property')
        if not property_obj:
            if hasattr(user, 'organization') and user.organization:
                property_obj = Property.objects.filter(organization=user.organization).first()
            if not property_obj:
                property_obj = Property.objects.first()

        room_type_obj = serializer.validated_data.get('room_type')
        if not room_type_obj:
            if property_obj:
                room_type_obj = RoomType.objects.filter(property=property_obj).first()
            if not room_type_obj:
                room_type_obj = RoomType.objects.first()
            if not room_type_obj and property_obj:
                room_type_obj = RoomType.objects.create(
                    property=property_obj,
                    name='Standard Suite',
                    code='STD-01',
                    base_rate=250.00,
                    max_occupancy=2
                )
        serializer.save(property=property_obj, room_type=room_type_obj)

    @action(detail=True, methods=['post'], url_path='status-transition')
    def status_transition(self, request, pk=None):
        """State machine transition endpoint for room status."""
        room = self.get_object()
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')

        valid_statuses = [choice[0] for choice in Room.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {'success': False, 'error': {'code': 'INVALID_STATUS', 'message': f'Unknown room status: {new_status}. Valid: {valid_statuses}'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = room.status
        room.status = new_status
        room.is_active = new_status not in ('OUT_OF_ORDER', 'BLOCKED')

        room.save(update_fields=['status', 'is_active'])

        return Response({
            'success': True,
            'data': RoomSerializer(room).data,
            'message': f'Room {room.room_number} transitioned from {old_status} to {new_status}.',
        })

    @action(detail=True, methods=['post'], url_path='transfer')
    def transfer(self, request, pk=None):
        current_room = self.get_object()
        target_room_id = request.data.get('targetRoomId') or request.data.get('target_room_id')
        reason = request.data.get('reason', 'Operational transfer')
        
        try:
            target_room = Room.objects.get(id=target_room_id)
        except Room.DoesNotExist:
            return Response(
                {'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'Target room {target_room_id} not found.'}},
                status=status.HTTP_404_NOT_FOUND
            )

        from apps.frontoffice.models import StayLog
        from apps.frontoffice.services import FrontOfficeService
        stay_log = StayLog.objects.filter(room=current_room, check_out_time__isnull=True).last()
        if stay_log:
            FrontOfficeService.transfer_room(reservation=stay_log.reservation, new_room=target_room)
        else:
            current_room.status = 'DIRTY'
            current_room.save(update_fields=['status'])
            target_room.status = 'OCCUPIED'
            target_room.save(update_fields=['status'])

        return Response({
            'success': True,
            'message': f"Transferred from {current_room.room_number} to {target_room.room_number}. Reason: {reason}",
            'sourceRoom': RoomSerializer(current_room).data,
            'targetRoom': RoomSerializer(target_room).data,
        })


class RatePlanViewSet(viewsets.ModelViewSet):
    serializer_class = RatePlanSerializer
    permission_classes = [IsPropertyStaffOrAdmin]
    filterset_fields = ['property', 'room_type', 'meal_plan', 'is_active']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return RatePlan.objects.none()
        if user.is_superuser:
            return RatePlan.objects.all()
        return RatePlan.objects.filter(property__organization=user.organization)


class RoomRateViewSet(viewsets.ModelViewSet):
    serializer_class = RoomRateSerializer
    permission_classes = [IsPropertyStaffOrAdmin]
    filterset_fields = ['rate_plan', 'date']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return RoomRate.objects.none()
        if user.is_superuser:
            return RoomRate.objects.all()
        return RoomRate.objects.filter(rate_plan__property__organization=user.organization)
