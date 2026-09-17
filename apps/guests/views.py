"""
Guest serializers and viewsets.
"""
from rest_framework import serializers, viewsets
from common.permissions import IsPropertyStaffOrAdmin
from .models import GuestProfile


class GuestProfileSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = GuestProfile
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class GuestProfileViewSet(viewsets.ModelViewSet):
    serializer_class = GuestProfileSerializer
    permission_classes = [IsPropertyStaffOrAdmin]
    filterset_fields = ['vip_status', 'nationality']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number', 'id_document_number']

    def get_queryset(self):
        return GuestProfile.objects.for_user(self.request.user)

    def perform_create(self, serializer):
        if self.request.user.is_superuser:
            serializer.save()
        else:
            serializer.save(organization=self.request.user.organization)
