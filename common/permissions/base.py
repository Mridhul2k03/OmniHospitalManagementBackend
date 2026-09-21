"""
Enterprise role-based & tenant-scoped permission classes.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperAdmin(BasePermission):
    """Allows access to superusers or users with role SUPER_ADMIN."""
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.is_superuser or getattr(request.user, 'role', '') == 'SUPER_ADMIN')
        )


class IsOrganizationAdmin(BasePermission):
    """Allows access to superusers or organization administrators."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        return getattr(request.user, 'role', '') in ('SUPER_ADMIN', 'ORG_ADMIN')


class IsShareholderReadOnly(BasePermission):
    """
    Ensures shareholders have a strictly READ-ONLY perimeter.
    Any attempt by a shareholder to mutate data (POST, PUT, PATCH, DELETE) is rejected.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if getattr(request.user, 'role', '') == 'SHAREHOLDER':
            return request.method in SAFE_METHODS
        return True


class IsPropertyStaffOrAdmin(BasePermission):
    """Allows access to property staff members, corporate executives, or organization admins."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(request.user, 'role', '')
        if role == 'SHAREHOLDER' and request.method in SAFE_METHODS:
            return True
        allowed_roles = (
            'ORG_ADMIN', 'PROPERTY_MANAGER', 'FRONT_DESK',
            'HOUSEKEEPING', 'MAINTENANCE', 'ACCOUNTANT',
            'PRESIDENT', 'VICE_PRESIDENT', 'CEO', 'OPERATIONS_DIRECTOR',
            'RESTAURANT_POS', 'CHEF_KITCHEN', 'SECURITY_STAFF',
            'TRANSPORT_DISPATCHER', 'DRIVER', 'HR',
        )
        return role in allowed_roles


class IsDiningStaff(BasePermission):
    """Allows access to restaurant/POS, kitchen, and management roles."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(request.user, 'role', '')
        allowed_roles = (
            'ORG_ADMIN', 'PROPERTY_MANAGER', 'RESTAURANT_POS',
            'CHEF_KITCHEN', 'FRONT_DESK',
            'PRESIDENT', 'VICE_PRESIDENT', 'CEO', 'OPERATIONS_DIRECTOR',
        )
        return role in allowed_roles


class IsHousekeepingStaff(BasePermission):
    """Allows access to housekeeping staff and management roles."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(request.user, 'role', '')
        allowed_roles = (
            'ORG_ADMIN', 'PROPERTY_MANAGER', 'HOUSEKEEPING', 'FRONT_DESK',
            'PRESIDENT', 'VICE_PRESIDENT', 'CEO', 'OPERATIONS_DIRECTOR',
        )
        return role in allowed_roles


class IsMaintenanceStaff(BasePermission):
    """Allows access to maintenance/engineering staff and management roles."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(request.user, 'role', '')
        allowed_roles = (
            'ORG_ADMIN', 'PROPERTY_MANAGER', 'MAINTENANCE', 'FRONT_DESK',
            'PRESIDENT', 'VICE_PRESIDENT', 'CEO', 'OPERATIONS_DIRECTOR',
        )
        return role in allowed_roles


class IsSecurityStaff(BasePermission):
    """Allows access to security/gate staff and management roles."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(request.user, 'role', '')
        allowed_roles = (
            'ORG_ADMIN', 'PROPERTY_MANAGER', 'SECURITY_STAFF', 'FRONT_DESK',
            'PRESIDENT', 'VICE_PRESIDENT', 'CEO', 'OPERATIONS_DIRECTOR',
        )
        return role in allowed_roles


class IsTransportStaff(BasePermission):
    """Allows access to transport dispatchers, drivers, and management roles."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(request.user, 'role', '')
        allowed_roles = (
            'ORG_ADMIN', 'PROPERTY_MANAGER', 'TRANSPORT_DISPATCHER',
            'DRIVER', 'FRONT_DESK',
            'PRESIDENT', 'VICE_PRESIDENT', 'CEO', 'OPERATIONS_DIRECTOR',
        )
        return role in allowed_roles


class IsSpaStaff(BasePermission):
    """Allows access to spa/wellness staff and management roles."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(request.user, 'role', '')
        allowed_roles = (
            'ORG_ADMIN', 'PROPERTY_MANAGER', 'FRONT_DESK',
            'PRESIDENT', 'VICE_PRESIDENT', 'CEO', 'OPERATIONS_DIRECTOR',
        )
        return role in allowed_roles
