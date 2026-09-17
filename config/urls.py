"""
URL Configuration for Hospitality Management Operating System (HMOS).
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Documentation via OpenAPI 3.0 / Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Domain Routes
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/organizations/', include('apps.organizations.urls')),
    path('api/v1/corporate/', include('apps.corporate.urls')),
    path('api/v1/', include('apps.properties.urls')),
    path('api/v1/rooms/', include('apps.rooms.urls')),
    path('api/v1/availability/', include('apps.availability.urls')),
    path('api/v1/guests/', include('apps.guests.urls')),
    path('api/v1/reservations/', include('apps.reservations.urls')),
    path('api/v1/billing/', include('apps.billing.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/frontoffice/', include('apps.frontoffice.urls')),
]
