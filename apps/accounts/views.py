"""
Accounts views for authentication, token refresh, and user management.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from common.permissions import IsOrganizationAdmin
from .models import User
from .serializers import UserSerializer, CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        serializer = UserSerializer(request.user)
        user = request.user
        org = user.organization
        active_tenant = {
            'id': str(org.id) if org else '7d18388a-872b-4d2b-b42a-f658c03e9e60',
            'name': org.name if org else 'Grand Horizon Hospitality Group',
            'slug': org.code.lower() if org and org.code else 'grand-horizon',
            'code': org.code if org and org.code else 'GHHG',
            'institution_type': 'luxury_hospitality_chain',
            'subscription_tier': (org.subscription_tier.lower() if org and hasattr(org, 'subscription_tier') and org.subscription_tier else 'enterprise'),
            'is_default': True,
        }
        
        user_data = serializer.data
        user_data['role'] = user.role
        user_data['is_staff'] = user.is_staff
        user_data['is_superuser'] = user.is_superuser

        return Response({
            'success': True,
            'user': user_data,
            'active_tenant': active_tenant,
            'accessible_tenants': [active_tenant],
            'permissions': ['*'] if user.is_superuser else [f"{user.role.lower()}:manage", 'rooms:view', 'reservations:view', 'folios:view']
        })


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email') or request.data.get('admin_email')
        password = request.data.get('password') or request.data.get('admin_password')
        username = request.data.get('username') or request.data.get('admin_username') or (email.split('@')[0] if email else None)
        first_name = request.data.get('first_name') or request.data.get('admin_first_name', '')
        last_name = request.data.get('last_name') or request.data.get('admin_last_name', '')
        org_name = request.data.get('organization_name') or request.data.get('institution_name') or request.data.get('name')
        org_code = request.data.get('organization_code') or request.data.get('slug') or request.data.get('code')
        role = request.data.get('role', 'ORG_ADMIN')
        subscription_tier = (request.data.get('subscription_tier') or 'ENTERPRISE').upper()

        if not email or not password:
            return Response({'success': False, 'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'success': False, 'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        org = None
        if org_name:
            import uuid
            from apps.organizations.models import Organization
            code_to_use = org_code or org_name.lower().replace(' ', '-')
            if Organization.objects.filter(code=code_to_use).exists():
                code_to_use = f"{code_to_use}-{uuid.uuid4().hex[:4]}"
            org = Organization.objects.create(
                name=org_name,
                code=code_to_use,
                contact_email=email,
                subscription_tier=subscription_tier
            )
        else:
            from apps.organizations.models import Organization
            org = Organization.objects.first()

        import uuid
        if User.objects.filter(username=username).exists():
            username = f"{username}_{uuid.uuid4().hex[:4]}"

        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            organization=org,
            role=role,
            is_staff=(role in ['SUPER_ADMIN', 'ORG_ADMIN'])
        )

        active_tenant = {
            'id': str(org.id) if org else '7d18388a-872b-4d2b-b42a-f658c03e9e60',
            'name': org.name if org else 'Grand Horizon Hospitality Group',
            'slug': org.code.lower() if org and org.code else 'grand-horizon',
            'code': org.code if org and org.code else 'GHHG',
            'institution_type': 'luxury_hospitality_chain',
            'subscription_tier': (org.subscription_tier.lower() if org and hasattr(org, 'subscription_tier') and org.subscription_tier else 'enterprise'),
            'is_default': True,
        }

        return Response({
            'success': True,
            'message': 'Account registered successfully.',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name,
                'role': user.role,
                'organization_id': str(org.id) if org else None,
                'organization_name': org.name if org else None,
            },
            'active_tenant': active_tenant
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return Response({
            'success': True,
            'message': 'Logged out successfully.'
        })


class SwitchTenantView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        tenant_id = request.data.get('tenant_id')
        from apps.organizations.models import Organization
        org = Organization.objects.filter(id=tenant_id).first() if tenant_id else getattr(request.user, 'organization', None)
        active_tenant = {
            'id': str(org.id) if org else (tenant_id or '7d18388a-872b-4d2b-b42a-f658c03e9e60'),
            'name': org.name if org else 'Grand Horizon Hospitality Group',
            'slug': org.code.lower() if org and org.code else 'grand-horizon',
            'code': org.code if org and org.code else 'GHHG',
            'institution_type': 'luxury_hospitality_chain',
            'is_default': True,
        }
        return Response({
            'success': True,
            'active_tenant': active_tenant,
            'message': f"Switched active tenant to {active_tenant['name']}"
        })


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.db import connection
        from datetime import datetime, timezone
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_ok = False

        return Response({
            'success': True,
            'status': 'healthy' if db_ok else 'degraded',
            'database': 'operational' if db_ok else 'unreachable',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'service': 'OmniHospitalManagement Backend API',
            'version': '1.0.0'
        })


class TenantViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        from apps.organizations.models import Organization
        orgs = Organization.objects.all()
        data = [{
            'id': str(o.id),
            'name': o.name,
            'slug': o.code.lower(),
            'code': o.code,
            'contact_email': o.contact_email,
            'currency': getattr(o, 'currency', 'USD'),
            'institution_type': 'luxury_hospitality_chain',
            'subscription_tier': getattr(o, 'subscription_tier', 'ENTERPRISE').lower(),
            'is_default': True,
        } for o in orgs]
        if not data:
            data = [{
                'id': '7d18388a-872b-4d2b-b42a-f658c03e9e60',
                'name': 'Grand Horizon Hospitality Group',
                'slug': 'grand-horizon',
                'code': 'GHHG',
                'contact_email': 'contact@omnihospitality.com',
                'currency': 'USD',
                'institution_type': 'luxury_hospitality_chain',
                'subscription_tier': 'enterprise',
                'is_default': True,
            }]
        return Response(data)

    def retrieve(self, request, pk=None):
        if pk == 'current':
            return self.current(request)
        from apps.organizations.models import Organization
        org = Organization.objects.filter(id=pk).first()
        if not org:
            return Response({
                'id': pk,
                'name': 'Grand Horizon Hospitality Group',
                'slug': 'grand-horizon',
                'code': 'GHHG',
                'currency': 'USD',
                'subscription_tier': 'enterprise',
            })
        return Response({
            'id': str(org.id),
            'name': org.name,
            'slug': org.code.lower(),
            'code': org.code,
            'contact_email': org.contact_email,
            'currency': getattr(org, 'currency', 'USD'),
            'subscription_tier': getattr(org, 'subscription_tier', 'ENTERPRISE').lower(),
        })

    def current(self, request):
        from apps.organizations.models import Organization
        user = getattr(request, 'user', None)
        org = getattr(user, 'organization', None) if (user and user.is_authenticated) else Organization.objects.first()
        if not org:
            return Response({
                'id': '7d18388a-872b-4d2b-b42a-f658c03e9e60',
                'name': 'Grand Horizon Hospitality Group',
                'slug': 'grand-horizon',
                'code': 'GHHG',
                'contact_email': 'contact@omnihospitality.com',
                'currency': 'USD',
                'institution_type': 'luxury_hospitality_chain',
                'subscription_tier': 'enterprise',
                'is_default': True,
            })
        return Response({
            'id': str(org.id),
            'name': org.name,
            'slug': org.code.lower(),
            'code': org.code,
            'contact_email': org.contact_email,
            'currency': getattr(org, 'currency', 'USD'),
            'institution_type': 'luxury_hospitality_chain',
            'subscription_tier': getattr(org, 'subscription_tier', 'ENTERPRISE').lower(),
            'is_default': True,
        })


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsOrganizationAdmin]
    filterset_fields = ['role', 'is_active', 'organization']
    search_fields = ['email', 'username', 'first_name', 'last_name']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return User.objects.none()
        if user.is_superuser or getattr(user, 'role', '') == 'SUPER_ADMIN':
            return User.objects.all().select_related('organization').order_by('-date_joined')
        if getattr(user, 'organization', None):
            return User.objects.filter(organization=user.organization).select_related('organization').order_by('-date_joined')
        return User.objects.none()

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        target_user = self.get_object()
        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=['is_active'])
        return Response({
            'success': True,
            'is_active': target_user.is_active,
            'message': f"User {target_user.email} is now {'Active' if target_user.is_active else 'Deactivated'}."
        })

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        password = request.data.get('password')
        if not password or len(password) < 6:
            return Response({'success': False, 'error': 'Password must be at least 6 characters.'}, status=status.HTTP_400_BAD_REQUEST)
        target_user = self.get_object()
        target_user.set_password(password)
        target_user.save()
        return Response({
            'success': True,
            'message': f"Password for {target_user.email} has been updated."
        })
