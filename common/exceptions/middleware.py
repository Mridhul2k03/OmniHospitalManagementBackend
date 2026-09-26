"""
Middleware for correlation IDs and distributed request tracing.
Implements RequestIDMiddleware from Multi-Tenant SaaS Architecture Blueprint.
"""
import uuid
from common.context import set_current_request_id


class CorrelationIdMiddleware:
    """
    Extracts or injects X-Request-ID and X-Correlation-ID headers,
    and binds the request ID to the thread-safe context for logging and audits.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = (
            request.headers.get('X-Request-ID') or
            request.headers.get('X-Correlation-ID') or
            str(uuid.uuid4())
        )
        request.correlation_id = request_id
        request.request_id = request_id
        set_current_request_id(request_id)

        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        response['X-Correlation-ID'] = request_id
        return response


# Blueprint compliance alias
RequestIDMiddleware = CorrelationIdMiddleware
