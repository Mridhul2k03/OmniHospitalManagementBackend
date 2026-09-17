import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.properties.models import Property


@pytest.mark.django_db
class TestMultiTenancyAndAccessControl:
    def setup_method(self):
        self.client = APIClient()

        # Tenant 1
        self.org_a = Organization.objects.create(name="Org Alpha", code="org-alpha", contact_email="a@test.com")
        self.user_a = User.objects.create_user(
            email="admin@alpha.com",
            username="alpha_admin",
            password="Password123!",
            organization=self.org_a,
            role="ORG_ADMIN"
        )
        self.prop_a = Property.objects.create(
            organization=self.org_a,
            name="Alpha Grand Resort",
            code="ALPHA-RESORT",
            address="123 Ocean Drive",
            city="Miami",
            state="FL",
            postal_code="33139",
            contact_email="frontdesk@alpha.com",
            contact_phone="1234567890"
        )

        # Tenant 2
        self.org_b = Organization.objects.create(name="Org Beta", code="org-beta", contact_email="b@test.com")
        self.user_b = User.objects.create_user(
            email="admin@beta.com",
            username="beta_admin",
            password="Password123!",
            organization=self.org_b,
            role="ORG_ADMIN"
        )
        self.prop_b = Property.objects.create(
            organization=self.org_b,
            name="Beta Skyline Hotel",
            code="BETA-SKY",
            address="456 City Center",
            city="New York",
            state="NY",
            postal_code="10001",
            contact_email="frontdesk@beta.com",
            contact_phone="0987654321"
        )

        # Shareholder in Org A
        self.shareholder = User.objects.create_user(
            email="investor@alpha.com",
            username="alpha_investor",
            password="Password123!",
            organization=self.org_a,
            role="SHAREHOLDER"
        )

    def test_tenant_a_cannot_see_tenant_b_properties(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/v1/properties/')

        assert response.status_code == status.HTTP_200_OK
        returned_ids = [item['id'] for item in response.data['results']]
        assert str(self.prop_a.id) in returned_ids
        assert str(self.prop_b.id) not in returned_ids

    def test_tenant_b_cannot_see_tenant_a_properties(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get('/api/v1/properties/')

        assert response.status_code == status.HTTP_200_OK
        returned_ids = [item['id'] for item in response.data['results']]
        assert str(self.prop_b.id) in returned_ids
        assert str(self.prop_a.id) not in returned_ids

    def test_shareholder_read_only_perimeter_on_reservations(self):
        self.client.force_authenticate(user=self.shareholder)

        # GET is permitted (safe method)
        get_response = self.client.get('/api/v1/reservations/')
        assert get_response.status_code == status.HTTP_200_OK

        # POST is strictly denied with 403 Forbidden
        post_response = self.client.post('/api/v1/reservations/', {
            'property_id': str(self.prop_a.id),
        }, format='json')
        assert post_response.status_code == status.HTTP_403_FORBIDDEN
