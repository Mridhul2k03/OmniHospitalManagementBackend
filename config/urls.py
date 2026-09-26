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

from apps.corporate.urls import executive_urlpatterns, shareholder_urlpatterns
from apps.accounts.views import HealthCheckView, TenantViewSet
from apps.billing.urls import folio_urlpatterns
from apps.billing.views import GLExportView
from apps.operations.urls import (
    dining_urlpatterns,
    kot_urlpatterns,
    housekeeping_urlpatterns,
    maintenance_urlpatterns,
    transport_urlpatterns,
    spa_urlpatterns,
    security_urlpatterns,
    inventory_urlpatterns,
    events_urlpatterns,
    cloakroom_urlpatterns,
    channels_urlpatterns,
    hr_urlpatterns,
)
from rest_framework.routers import DefaultRouter

tenant_router = DefaultRouter()
tenant_router.register(r'', TenantViewSet, basename='api-tenant')

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Documentation via OpenAPI 3.0 / Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Health Probes & Multi-Tenancy Gateway
    path('api/v1/health/', HealthCheckView.as_view(), name='root-health-check'),
    path('api/v1/ready/', HealthCheckView.as_view(), name='root-readiness-check'),
    path('api/v1/tenants/', include(tenant_router.urls)),
    path('api/v1/platform/', include('apps.platform_admin.urls')),

    # Domain Routes
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/organizations/', include('apps.organizations.urls')),
    path('api/v1/corporate/', include('apps.corporate.urls')),
    path('api/v1/executive/', include(executive_urlpatterns)),
    path('api/v1/shareholder/', include(shareholder_urlpatterns)),
    path('api/v1/', include('apps.properties.urls')),
    path('api/v1/rooms/', include('apps.rooms.urls')),
    path('api/v1/availability/', include('apps.availability.urls')),
    path('api/v1/guests/', include('apps.guests.urls')),
    path('api/v1/reservations/', include('apps.reservations.urls')),
    path('api/v1/billing/', include('apps.billing.urls')),
    path('api/v1/folios/', include(folio_urlpatterns)),
    path('api/v1/finance/gl-export/', GLExportView.as_view({'get': 'list'}), name='finance-gl-export'),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/frontoffice/', include('apps.frontoffice.urls')),

    # Dynamic Pricing & Guest Loyalty
    path('api/v1/pricing/', include('apps.pricing.urls')),
    path('api/v1/loyalty/', include('apps.loyalty.urls')),

    # Operations & Facilities Modules
    path('api/v1/dining/', include(dining_urlpatterns)),
    path('api/v1/kot/', include(kot_urlpatterns)),
    path('api/v1/housekeeping/', include(housekeeping_urlpatterns)),
    path('api/v1/maintenance/', include(maintenance_urlpatterns)),
    path('api/v1/transport/', include(transport_urlpatterns)),
    path('api/v1/spa/', include(spa_urlpatterns)),
    path('api/v1/security/', include(security_urlpatterns)),
    path('api/v1/inventory/', include(inventory_urlpatterns)),
    path('api/v1/events/', include(events_urlpatterns)),
    path('api/v1/cloakroom/', include(cloakroom_urlpatterns)),
    path('api/v1/channels/', include(channels_urlpatterns)),
    path('api/v1/hr/', include(hr_urlpatterns)),
]
