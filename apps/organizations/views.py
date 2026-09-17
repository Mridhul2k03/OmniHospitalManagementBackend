"""
Organization serializers and viewsets.
"""
from rest_framework import serializers, viewsets
from common.permissions import IsSuperAdmin
from .models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['is_active', 'subscription_tier']
    search_fields = ['name', 'code', 'contact_email']
