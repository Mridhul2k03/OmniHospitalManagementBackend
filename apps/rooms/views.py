"""
Rooms, Room Types, and Rates serializers and viewsets.
"""
from rest_framework import serializers, viewsets
from common.permissions import IsPropertyStaffOrAdmin
from .models import RoomAmenity, RoomType, Room, RatePlan, RoomRate


class RoomAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomAmenity
        fields = '__all__'


class RoomTypeSerializer(serializers.ModelSerializer):
    amenities = RoomAmenitySerializer(many=True, read_only=True)

    class Meta:
        model = RoomType
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    floor_name = serializers.CharField(source='floor.name', read_only=True)

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
