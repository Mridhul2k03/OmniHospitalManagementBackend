"""
Dual-Mode Authentication (HttpOnly Cookies + Bearer Token).
Supports secure HttpOnly cookies (access_token, refresh_token) for browser frontend,
with seamless fallback to Authorization: Bearer <token>.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieOrBearerJWTAuthentication(JWTAuthentication):
    """
    Checks HTTP Authorization header first; if absent, inspects HttpOnly cookie 'access_token'.
    """
    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get("access_token")

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
