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
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'username': self.user.username,
            'full_name': self.user.full_name,
            'role': self.user.role,
            'organization_id': str(self.user.organization_id) if self.user.organization_id else None,
            'organization_name': self.user.organization.name if self.user.organization else None,
            'is_superuser': self.user.is_superuser,
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'role', 'organization', 'organization_name',
            'phone_number', 'is_2fa_enabled', 'is_active', 'date_joined'
        )
        read_only_fields = ('id', 'full_name', 'date_joined')
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
