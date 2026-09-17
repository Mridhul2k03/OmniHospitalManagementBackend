"""
Property serializers and viewsets.
"""
from rest_framework import serializers, viewsets
from common.permissions import IsPropertyStaffOrAdmin
from .models import Property, Building, Floor


class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'
        read_only_fields = ('id',)


class BuildingSerializer(serializers.ModelSerializer):
    floors = FloorSerializer(many=True, read_only=True)

    class Meta:
        model = Building
        fields = '__all__'
        read_only_fields = ('id',)


class PropertySerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    buildings = BuildingSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [IsPropertyStaffOrAdmin]
    filterset_fields = ['property_type', 'city', 'state', 'country', 'is_active']
    search_fields = ['name', 'code', 'city', 'contact_email']

    def get_queryset(self):
        return Property.objects.for_user(self.request.user)

    def perform_create(self, serializer):
        if self.request.user.is_superuser:
            serializer.save()
        else:
            serializer.save(organization=self.request.user.organization)


class BuildingViewSet(viewsets.ModelViewSet):
    serializer_class = BuildingSerializer
    permission_classes = [IsPropertyStaffOrAdmin]
    filterset_fields = ['property']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return Building.objects.none()
        if user.is_superuser:
            return Building.objects.all()
        return Building.objects.filter(property__organization=user.organization)


class FloorViewSet(viewsets.ModelViewSet):
    serializer_class = FloorSerializer
    permission_classes = [IsPropertyStaffOrAdmin]
    filterset_fields = ['building']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return Floor.objects.none()
        if user.is_superuser:
            return Floor.objects.all()
        return Floor.objects.filter(building__property__organization=user.organization)
