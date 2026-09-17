"""
Standardized JSON error envelope for Django REST Framework.
"""
from datetime import datetime, timezone
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first to get standard response
    response = exception_handler(exc, context)
    request = context.get('request')
    correlation_id = getattr(request, 'correlation_id', None)

    current_timestamp = datetime.now(timezone.utc).isoformat()

    if response is not None:
        code = "API_ERROR"
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            code = "VALIDATION_ERROR"
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "AUTHENTICATION_FAILED"
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            code = "PERMISSION_DENIED"
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            code = "NOT_FOUND"
        elif response.status_code == status.HTTP_409_CONFLICT:
            code = "CONCURRENCY_CONFLICT"

        # Format details
        details = response.data
        message = "An error occurred during request processing."
        if isinstance(details, dict):
            if 'detail' in details:
                message = str(details['detail'])
            elif len(details) > 0:
                first_key = next(iter(details))
                first_val = details[first_key]
                if isinstance(first_val, list) and len(first_val) > 0:
                    message = f"{first_key}: {first_val[0]}"
                else:
                    message = f"{first_key}: {first_val}"

        custom_data = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
            "correlation_id": correlation_id,
            "timestamp": current_timestamp,
        }
        response.data = custom_data
    else:
        # Unhandled 500 server error
        custom_data = {
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc) if getattr(request, 'user', None) and request.user.is_staff else "Internal server error.",
                "details": None,
            },
            "correlation_id": correlation_id,
            "timestamp": current_timestamp,
        }
        response = Response(custom_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
