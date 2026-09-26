import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.properties.models import Property


@pytest.mark.django_db
class TestPlatformSuperAdmin:
    def setup_method(self):
        self.client = APIClient()

        # Regular tenant
        self.org = Organization.objects.create(name="Delta Hotel", code="delta-hotel", contact_email="delta@test.com")
        self.tenant_admin = User.objects.create_user(
            email="tenant_admin@delta.com",
            username="delta_admin",
            password="Password123!",
            organization=self.org,
            role="ORG_ADMIN",
            is_superuser=False
        )

        # Platform SuperAdmin
        self.superadmin = User.objects.create_superuser(
            email="superadmin@omnihospital.com",
            username="platform_root",
            password="Password123!"
        )

    def test_platform_stats_denied_to_regular_tenant_admin(self):
        self.client.force_authenticate(user=self.tenant_admin)
        response = self.client.get('/api/v1/platform/stats/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_platform_stats_allowed_for_superadmin(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/v1/platform/stats/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_tenants' in response.data
        assert 'total_users' in response.data
        assert response.data['total_tenants'] >= 1

    def test_provision_new_tenant_with_auto_bootstrapping(self):
        self.client.force_authenticate(user=self.superadmin)
        payload = {
            "name": "Epsilon Luxury Suites",
            "contact_email": "hello@epsilon.com",
            "contact_phone": "+1999888777",
            "subscription_tier": "ENTERPRISE",
            "property_name": "Epsilon Downtown Resort",
            "property_code": "EPS-RESORT",
            "admin_email": "admin@epsilon.com",
            "admin_name": "Epsilon General Manager",
            "admin_password": "SecurePassword123!",
            "admin_phone": "+1999888666"
        }
        response = self.client.post('/api/v1/platform/tenants/', payload, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print("ERROR RESPONSE DATA:", response.data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "Epsilon Luxury Suites"

        # Verify Organization created
        new_org = Organization.objects.filter(contact_email="hello@epsilon.com").first()
        assert new_org is not None
        assert new_org.subscription_tier == "ENTERPRISE"

        # Verify Property created and bound
        prop = Property.objects.filter(organization=new_org).first()
        assert prop is not None
        assert prop.name == "Epsilon Downtown Resort"

        # Verify initial tenant admin created
        admin = User.objects.filter(email="admin@epsilon.com").first()
        assert admin is not None
        assert admin.organization == new_org
        assert admin.role == "ORG_ADMIN"

    def test_toggle_tenant_status(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.post(f'/api/v1/platform/tenants/{self.org.id}/toggle-status/')
        assert response.status_code == status.HTTP_200_OK
        self.org.refresh_from_db()
        assert self.org.is_active is False

    def test_cross_tenant_user_management(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/v1/platform/users/')
        assert response.status_code == status.HTTP_200_OK
        returned_emails = [u['email'] for u in response.data['results']]
        assert "tenant_admin@delta.com" in returned_emails
        assert "superadmin@omnihospital.com" in returned_emails

    def test_platform_system_health(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/v1/platform/system/health/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'].upper() == "HEALTHY"
