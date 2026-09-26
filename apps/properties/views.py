import uuid
from django.utils.text import slugify
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsPropertyStaffOrAdmin
from .models import Property, Building, Floor


class FloorSerializer(serializers.ModelSerializer):
    building = serializers.PrimaryKeyRelatedField(queryset=Building.objects.all(), required=False, allow_null=True)
    building_name = serializers.CharField(source='building.name', read_only=True)
    property_id = serializers.UUIDField(source='building.property.id', read_only=True)
    property_name = serializers.CharField(source='building.property.name', read_only=True)

    class Meta:
        model = Floor
        fields = '__all__'
        read_only_fields = ('id',)
        validators = []


class BuildingSerializer(serializers.ModelSerializer):
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all(), required=False, allow_null=True)
    property_name = serializers.CharField(source='property.name', read_only=True)
    code = serializers.SlugField(required=False)
    floors = FloorSerializer(many=True, read_only=True)

    class Meta:
        model = Building
        fields = '__all__'
        read_only_fields = ('id',)
        validators = []


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

    @action(detail=True, methods=['get'])
    def buildings(self, request, pk=None):
        property_obj = self.get_object()
        buildings = property_obj.buildings.all()
        serializer = BuildingSerializer(buildings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'patch', 'put'], url_path='policies')
    def policies(self, request, pk=None):
        property_obj = self.get_object()
        if request.method == 'GET':
            return Response({
                'id': str(property_obj.id),
                'name': property_obj.name,
                'checkInTime': getattr(property_obj, 'check_in_time', '15:00'),
                'checkOutTime': getattr(property_obj, 'check_out_time', '11:00'),
                'stateTaxRate': float(getattr(property_obj, 'state_tax_rate', 8.875)),
                'cityUnitFee': float(getattr(property_obj, 'city_unit_fee', 1.50)),
                'baseCurrency': getattr(property_obj, 'currency', 'USD'),
                'phone': getattr(property_obj, 'contact_phone', '+1 (212) 555-0199'),
                'email': getattr(property_obj, 'contact_email', 'management@grandhorizon.com'),
                'address': getattr(property_obj, 'address', '742 Evergreen Promenade, New York, NY 10001'),
            })

        data = request.data
        if 'name' in data:
            property_obj.name = data['name']
        if 'checkInTime' in data or 'check_in_time' in data:
            property_obj.check_in_time = data.get('checkInTime') or data.get('check_in_time')
        if 'checkOutTime' in data or 'check_out_time' in data:
            property_obj.check_out_time = data.get('checkOutTime') or data.get('check_out_time')
        if 'phone' in data or 'contact_phone' in data:
            property_obj.contact_phone = data.get('phone') or data.get('contact_phone')
        if 'email' in data or 'contact_email' in data:
            property_obj.contact_email = data.get('email') or data.get('contact_email')
        if 'address' in data:
            property_obj.address = data['address']
        if 'baseCurrency' in data or 'currency' in data:
            property_obj.currency = data.get('baseCurrency') or data.get('currency')
        property_obj.save()
        return Response({
            'success': True,
            'message': 'Property policies and profile updated successfully.',
            'data': {
                'id': str(property_obj.id),
                'name': property_obj.name,
                'checkInTime': property_obj.check_in_time,
                'checkOutTime': property_obj.check_out_time,
                'stateTaxRate': float(getattr(property_obj, 'state_tax_rate', 8.875)),
                'cityUnitFee': float(getattr(property_obj, 'city_unit_fee', 1.50)),
                'baseCurrency': property_obj.currency,
                'phone': property_obj.contact_phone,
                'email': property_obj.contact_email,
                'address': property_obj.address,
            }
        })


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

    def perform_create(self, serializer):
        user = self.request.user
        property_obj = serializer.validated_data.get('property')
        if not property_obj:
            if hasattr(user, 'organization') and user.organization:
                property_obj = Property.objects.filter(organization=user.organization).first()
            if not property_obj:
                property_obj = Property.objects.first()

        name = serializer.validated_data.get('name', 'Main Wing')
        code = serializer.validated_data.get('code')
        if not code:
            code = f"{slugify(name)[:24] or 'bld'}-{str(uuid.uuid4())[:6]}"

        serializer.save(property=property_obj, code=code)

    @action(detail=True, methods=['get'])
    def floors(self, request, pk=None):
        building = self.get_object()
        floors = building.floors.all()
        serializer = FloorSerializer(floors, many=True)
        return Response(serializer.data)


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

    def perform_create(self, serializer):
        user = self.request.user
        building = serializer.validated_data.get('building')
        if not building:
            property_obj = None
            if hasattr(user, 'organization') and user.organization:
                property_obj = Property.objects.filter(organization=user.organization).first()
            if not property_obj:
                property_obj = Property.objects.first()

            if property_obj:
                building = Building.objects.filter(property=property_obj).first()
                if not building:
                    building = Building.objects.create(
                        property=property_obj,
                        name=f"{property_obj.name} Main Tower",
                        code=f"MAIN-{str(uuid.uuid4())[:6]}"
                    )
            serializer.save(building=building)
            return
        serializer.save()

