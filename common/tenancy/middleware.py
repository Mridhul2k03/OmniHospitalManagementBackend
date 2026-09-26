"""
Middleware to establish tenant scope from the authenticated request.
Implements Recipe C (TenantContextMiddleware) from the Multi-Tenant SaaS Architecture Blueprint.
"""
import uuid
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from common.context import set_current_tenant, clear_current_tenant


class TenantContextMiddleware(MiddlewareMixin):
    """
    Resolves active tenant from X-Tenant-ID header or authenticated user's organization.
    Enforces strict cross-tenant isolation for regular users and allows SuperAdmin
    tenant inspection / switching. Sets thread-safe context for automatic ORM isolation.
    """
    EXEMPT_PREFIXES = (
        "/api/v1/auth/",
        "/api/v1/health/",
        "/api/v1/public/",
    )

    def process_request(self, request):
        clear_current_tenant()
        request.tenant = None
        request.organization = None

        # 1. Skip non-authenticated public paths
        if any(request.path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return None

        # 2. Extract User if authenticated
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        from apps.organizations.models import Organization

        # 3. Read requested tenant header
        raw_tenant = request.headers.get("X-Tenant-ID", "").strip()
        requested_tenant_id = None if raw_tenant in ("", "null", "undefined") else raw_tenant

        is_platform_admin = getattr(user, 'is_superuser', False) or getattr(user, 'role', '') == 'SUPER_ADMIN'

        if requested_tenant_id:
            try:
                tenant_uuid = uuid.UUID(requested_tenant_id)
                lookup = {"id": tenant_uuid}
            except (ValueError, AttributeError):
                slug = requested_tenant_id.lower()
                lookup = {"code": slug}

            # SuperAdmin bypass / cross-tenant inspection
            if is_platform_admin:
                tenant = Organization.objects.filter(**lookup, is_active=True).first()
                if not tenant:
                    tenant = Organization.objects.filter(**lookup).first()
                if not tenant:
                    return JsonResponse({"error": "Organization not found."}, status=404)
                request.tenant = tenant
                request.organization = tenant
                set_current_tenant(tenant)
                return None

            # Verify regular user organization
            user_org = getattr(user, 'organization', None)
            if user_org:
                is_match = False
                if "id" in lookup and user_org.id == lookup["id"]:
                    is_match = True
                elif "code" in lookup and user_org.code.lower() == lookup["code"]:
                    is_match = True

                if not is_match:
                    return JsonResponse(
                        {"error": "Forbidden: Cross-tenant access not permitted."},
                        status=403,
                    )
                request.tenant = user_org
                request.organization = user_org
                set_current_tenant(user_org)
            else:
                return JsonResponse(
                    {"error": "Forbidden: User has no active organization."},
                    status=403,
                )
        else:
            # Default active organization
            user_org = getattr(user, 'organization', None)
            if user_org:
                request.tenant = user_org
                request.organization = user_org
                set_current_tenant(user_org)
            elif is_platform_admin:
                first_org = Organization.objects.filter(is_active=True).first()
                if first_org:
                    request.tenant = first_org
                    request.organization = first_org
                    set_current_tenant(first_org)

        return None

    def process_response(self, request, response):
        clear_current_tenant()
        return response

    def process_exception(self, request, exception):
        clear_current_tenant()
        return None


# Backward compatibility alias
TenantMiddleware = TenantContextMiddleware
