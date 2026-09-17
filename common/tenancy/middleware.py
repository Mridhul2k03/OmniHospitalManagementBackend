"""
Middleware to establish tenant scope from the authenticated request.
"""
from django.utils.deprecation import MiddlewareMixin


class TenantMiddleware(MiddlewareMixin):
    """
    Attaches the active tenant organization to request.organization.
    Never trusts client-supplied tenant ID for authenticated staff.
    """
    def process_request(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            request.organization = getattr(user, 'organization', None)
        else:
            request.organization = None
