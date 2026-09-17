import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from apps.accounts.models import User


@pytest.mark.django_db
class TestAccountsAndAuth:
    def setup_method(self):
        self.client = APIClient()
        self.org = Organization.objects.create(
            name="Grand Horizon Group",
            code="grand-horizon",
            contact_email="admin@grandhorizon.com"
        )
        self.user = User.objects.create_user(
            email="manager@grandhorizon.com",
            username="gh_manager",
            password="SecurePassword123!",
            organization=self.org,
            role="PROPERTY_MANAGER",
            first_name="Alexander",
            last_name="Wright"
        )

    def test_user_creation_and_properties(self):
        assert self.user.email == "manager@grandhorizon.com"
        assert self.user.role == "PROPERTY_MANAGER"
        assert self.user.organization == self.org
        assert self.user.check_password("SecurePassword123!") is True
        assert self.user.full_name == "Alexander Wright"

    def test_jwt_login_success(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'email': 'manager@grandhorizon.com',
            'password': 'SecurePassword123!'
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
        assert response.data['user']['email'] == 'manager@grandhorizon.com'
        assert response.data['user']['role'] == 'PROPERTY_MANAGER'
        assert response.data['user']['organization_id'] == str(self.org.id)

    def test_jwt_login_failure(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'email': 'manager@grandhorizon.com',
            'password': 'WrongPassword!'
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_current_user_profile(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('current_user')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['user']['email'] == self.user.email
        assert response.data['user']['role'] == 'PROPERTY_MANAGER'
