"""
ILA SaaS Platform SuperAdmin Permissions.
Guarantees access strictly to active ILA Company Platform SuperUsers (is_superuser=True).
Hotel client administrators (ORG_ADMIN, etc.) are strictly forbidden.
"""
from rest_framework.permissions import BasePermission


class IsILAPlatformSuperAdmin(BasePermission):
    """
    Strict permission class: Allows access ONLY to active ILA Company SuperUsers
    (request.user.is_superuser=True).
    Hotel-level tenant administrators (ORG_ADMIN, PROPERTY_MANAGER, etc.) are strictly denied (403 Forbidden).
    """
    message = "Forbidden: Access restricted strictly to ILA SaaS Platform SuperAdmins."

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not (user and user.is_authenticated and user.is_active):
            return False
        # Strictly requires ILA Company Root SuperUser
        return bool(user.is_superuser)


# Backward compatibility alias
IsPlatformSuperAdmin = IsILAPlatformSuperAdmin
