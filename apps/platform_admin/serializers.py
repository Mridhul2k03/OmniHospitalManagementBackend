"""
Serializers for the Cross-Tenant Platform SuperAdmin Control Center.
Implements automated bootstrapping and cross-tenant serialization.
"""
import uuid
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.properties.models import Property


class PlatformTenantSerializer(serializers.ModelSerializer):
    users_count = serializers.SerializerMethodField()
    properties_count = serializers.SerializerMethodField()
    subscription_tier = serializers.CharField()

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


class PlatformTenantCreateSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False, allow_blank=True)
    property_name = serializers.CharField(required=False, allow_blank=True)
    property_code = serializers.CharField(required=False, allow_blank=True)
    admin_name = serializers.CharField(required=False, allow_blank=True)
    admin_phone = serializers.CharField(required=False, allow_blank=True)
    admin_email = serializers.EmailField(required=False, allow_blank=True)
    admin_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    admin_first_name = serializers.CharField(required=False, allow_blank=True)
    admin_last_name = serializers.CharField(required=False, allow_blank=True)
    admin_username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'code', 'legal_name', 'contact_email',
            'contact_phone', 'address', 'subscription_tier',
            'property_name', 'property_code',
            'admin_name', 'admin_phone', 'admin_email', 'admin_password',
            'admin_first_name', 'admin_last_name', 'admin_username'
        ]
        read_only_fields = ('id',)

    def validate(self, attrs):
        if not attrs.get('code') and attrs.get('name'):
            base_slug = slugify(attrs['name'])
            candidate = base_slug
            idx = 1
            while Organization.objects.filter(code=candidate).exists():
                candidate = f"{base_slug}-{idx}"
                idx += 1
            attrs['code'] = candidate
        return attrs

    def create(self, validated_data):
        admin_email = validated_data.pop('admin_email', None)
        admin_password = validated_data.pop('admin_password', None)
        admin_name = validated_data.pop('admin_name', '')
        admin_phone = validated_data.pop('admin_phone', '')
        admin_first_name = validated_data.pop('admin_first_name', '')
        admin_last_name = validated_data.pop('admin_last_name', '')
        admin_username = validated_data.pop('admin_username', None)

        if admin_name and not admin_first_name:
            parts = admin_name.strip().split(' ', 1)
            admin_first_name = parts[0]
            admin_last_name = parts[1] if len(parts) > 1 else ''

        prop_name = validated_data.pop('property_name', None)
        prop_code = validated_data.pop('property_code', None)

        tier = (validated_data.get('subscription_tier') or 'ENTERPRISE').upper()
        validated_data['subscription_tier'] = tier

        with transaction.atomic():
            # 1. Provision Tenant Organization Record
            organization = Organization.objects.create(**validated_data)

            # 2. Auto-bootstrap initial primary property scope
            effective_prop_code = prop_code or f"{organization.code.upper()[:4]}-01"
            effective_prop_name = prop_name or f"{organization.name} Primary Property"

            Property.objects.get_or_create(
                organization=organization,
                code=effective_prop_code,
                defaults={
                    'name': effective_prop_name,
                    'property_type': 'HOTEL',
                    'contact_email': organization.contact_email,
                    'contact_phone': organization.contact_phone or '+1 (555) 010-0000',
                    'address': organization.address or '742 Main Street',
                    'city': 'New York',
                    'state': 'NY',
                    'country': 'United States',
                    'postal_code': '10001',
                    'currency': 'USD',
                    'check_in_time': '15:00',
                    'check_out_time': '11:00',
                }
            )

            # 3. Auto-bootstrap initial Organization Administrator if credentials provided
            if admin_email and admin_password:
                if not User.objects.filter(email=admin_email).exists():
                    fallback_username = admin_email.split('@')[0]
                    if User.objects.filter(username=fallback_username).exists():
                        fallback_username = f"{fallback_username}_{organization.code.replace('-', '_')}"
                    username_to_use = admin_username or fallback_username
                    if User.objects.filter(username=username_to_use).exists():
                        username_to_use = f"{username_to_use}_{uuid.uuid4().hex[:6]}"

                    User.objects.create_user(
                        email=admin_email,
                        username=username_to_use,
                        password=admin_password,
                        first_name=admin_first_name,
                        last_name=admin_last_name,
                        phone_number=admin_phone,
                        organization=organization,
                        role='ORG_ADMIN',
                        is_staff=True
                    )

        return organization


class PlatformUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_code = serializers.CharField(source='organization.code', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'role', 'organization', 'organization_name',
            'organization_code', 'phone_number', 'is_active',
            'is_staff', 'is_superuser', 'is_2fa_enabled', 'date_joined'
        ]
        read_only_fields = ('id', 'date_joined')


class PlatformAuditLogSerializer(serializers.Serializer):
    id = serializers.CharField()
    actor_email = serializers.CharField()
    action = serializers.CharField()
    resource_type = serializers.CharField()
    resource_id = serializers.CharField()
    description = serializers.CharField()
    ip_address = serializers.CharField(allow_blank=True, required=False)
    timestamp = serializers.CharField()
