"""
Corporate governance serializers and viewsets.
"""
from rest_framework import serializers, viewsets
from common.permissions import IsOrganizationAdmin
from .models import Region, PropertyGroup, ExecutiveAssignment


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class PropertyGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyGroup
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ExecutiveAssignmentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = ExecutiveAssignment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [IsOrganizationAdmin]
    search_fields = ['name', 'code']

    def get_queryset(self):
        return Region.objects.for_user(self.request.user)


class PropertyGroupViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyGroupSerializer
    permission_classes = [IsOrganizationAdmin]
    search_fields = ['name', 'code']

    def get_queryset(self):
        return PropertyGroup.objects.for_user(self.request.user)


class ExecutiveAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = ExecutiveAssignmentSerializer
    permission_classes = [IsOrganizationAdmin]
    filterset_fields = ['role', 'is_active']

    def get_queryset(self):
        return ExecutiveAssignment.objects.for_user(self.request.user)
