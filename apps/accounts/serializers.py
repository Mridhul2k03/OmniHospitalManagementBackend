"""
Accounts serializers supporting JWT token generation and user profiles.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Custom claims embedded in JWT
        token['email'] = user.email
        token['username'] = user.username
        token['full_name'] = user.full_name
        token['role'] = user.role
        token['organization_id'] = str(user.organization_id) if user.organization_id else None
        token['is_superuser'] = user.is_superuser
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Include detailed user context in the direct login response
        org = self.user.organization
        active_tenant = {
            'id': str(org.id) if org else '7d18388a-872b-4d2b-b42a-f658c03e9e60',
            'name': org.name if org else 'Grand Horizon Hospitality Group',
            'slug': org.code.lower() if org and org.code else 'grand-horizon',
            'code': org.code if org and org.code else 'GHHG',
            'institution_type': 'luxury_hospitality_chain',
            'subscription_tier': (org.subscription_tier.lower() if org and hasattr(org, 'subscription_tier') and org.subscription_tier else 'enterprise'),
            'is_default': True,
        }
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'full_name': self.user.full_name,
            'role': self.user.role,
            'organization_id': str(self.user.organization_id) if self.user.organization_id else None,
            'organization_name': self.user.organization.name if self.user.organization else None,
            'is_superuser': self.user.is_superuser,
            'is_staff': self.user.is_staff,
        }
        data['active_tenant'] = active_tenant
        data['accessible_tenants'] = [active_tenant]
        return data


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'role', 'organization', 'organization_name',
            'phone_number', 'is_2fa_enabled', 'is_active', 'is_staff',
            'is_superuser', 'date_joined', 'password'
        )
        read_only_fields = ('id', 'full_name', 'date_joined', 'is_superuser')
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
