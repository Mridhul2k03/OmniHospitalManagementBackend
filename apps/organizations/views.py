"""
Organization serializers and viewsets.
"""
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsSuperAdmin
from .models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    users_count = serializers.SerializerMethodField()
    properties_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'code', 'legal_name', 'contact_email',
            'contact_phone', 'address', 'subscription_tier',
            'is_active', 'created_at', 'updated_at',
            'users_count', 'properties_count'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_users_count(self, obj):
        return obj.users.count() if hasattr(obj, 'users') else 0

    def get_properties_count(self, obj):
        if hasattr(obj, 'properties_property_set'):
            return obj.properties_property_set.count()
        elif hasattr(obj, 'properties'):
            return obj.properties.count()
        return 0


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all().order_by('-created_at')
    serializer_class = OrganizationSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ['is_active', 'subscription_tier']
    search_fields = ['name', 'code', 'contact_email']

    def create(self, request, *args, **kwargs):
        admin_email = request.data.get('admin_email')
        admin_password = request.data.get('admin_password')
        admin_first_name = request.data.get('admin_first_name', '')
        admin_last_name = request.data.get('admin_last_name', '')
        admin_username = request.data.get('admin_username')

        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED and admin_email and admin_password:
            from apps.accounts.models import User
            import uuid
            org_id = response.data.get('id')
            org = Organization.objects.filter(id=org_id).first()
            if org and not User.objects.filter(email=admin_email).exists():
                fallback_username = admin_email.split('@')[0]
                if User.objects.filter(username=fallback_username).exists():
                    fallback_username = f"{fallback_username}_{org.code.replace('-', '_')}"
                username_to_use = admin_username or fallback_username
                if User.objects.filter(username=username_to_use).exists():
                    username_to_use = f"{username_to_use}_{uuid.uuid4().hex[:6]}"
                User.objects.create_user(
                    email=admin_email,
                    username=username_to_use,
                    password=admin_password,
                    first_name=admin_first_name,
                    last_name=admin_last_name,
                    organization=org,
                    role='ORG_ADMIN',
                    is_staff=True
                )
        return response

    @action(detail=True, methods=['post'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        org = self.get_object()
        org.is_active = not org.is_active
        org.save(update_fields=['is_active', 'updated_at'])
        return Response({
            'success': True,
            'is_active': org.is_active,
            'message': f"Client {org.name} status updated to {'Active' if org.is_active else 'Suspended'}."
        })

    @action(detail=True, methods=['post'], url_path='set-tier')
    def set_tier(self, request, pk=None):
        org = self.get_object()
        tier = (request.data.get('subscription_tier') or 'ENTERPRISE').upper()
        if tier not in ['STARTER', 'PROFESSIONAL', 'ENTERPRISE']:
            return Response({'success': False, 'error': 'Invalid subscription tier.'}, status=status.HTTP_400_BAD_REQUEST)
        org.subscription_tier = tier
        org.save(update_fields=['subscription_tier', 'updated_at'])
        return Response({
            'success': True,
            'subscription_tier': org.subscription_tier.lower(),
            'message': f"Client {org.name} subscription plan set to {tier}."
        })

    @action(detail=False, methods=['post'], url_path='switch-plan', permission_classes=[permissions.IsAuthenticated])
    def switch_plan(self, request):
        tier = (request.data.get('subscription_tier') or 'ENTERPRISE').upper()
        if tier not in ['STARTER', 'PROFESSIONAL', 'ENTERPRISE']:
            tier = 'ENTERPRISE'

        user = request.user
        org = user.organization if hasattr(user, 'organization') and user.organization else Organization.objects.first()

        if org:
            org.subscription_tier = tier
            org.save(update_fields=['subscription_tier', 'updated_at'])
            return Response({
                'success': True,
                'message': f"Organization subscription updated to {tier}.",
                'subscription_tier': tier.lower(),
                'organization_id': str(org.id)
            })
        return Response({'success': False, 'error': 'No organization found'}, status=status.HTTP_404_NOT_FOUND)
