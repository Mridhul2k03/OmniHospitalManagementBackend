"""
URL routing for the Platform SuperAdmin Subsystem (/api/v1/platform/*).
Implements Section 6 of Multi-Tenant SaaS Architecture Blueprint.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlatformStatsView,
    PlatformTenantViewSet,
    PlatformUserViewSet,
    PlatformAuditLogViewSet,
    PlatformSystemHealthView,
)

router = DefaultRouter()
router.register(r'tenants', PlatformTenantViewSet, basename='platform-tenants')
router.register(r'users', PlatformUserViewSet, basename='platform-users')

urlpatterns = [
    path('stats/', PlatformStatsView.as_view(), name='platform-stats'),
    path('audit-logs/', PlatformAuditLogViewSet.as_view(), name='platform-audit-logs'),
    path('health/', PlatformSystemHealthView.as_view(), name='platform-health'),
    path('system/health/', PlatformSystemHealthView.as_view(), name='platform-system-health'),
    path('', include(router.urls)),
]
