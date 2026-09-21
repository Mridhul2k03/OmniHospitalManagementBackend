from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegionViewSet, PropertyGroupViewSet, ExecutiveAssignmentViewSet,
    CorporateKPIView, PropertyComparisonView, RevenueMixView,
    ShareholderProfileView, ShareholderDividendViewSet, ShareholderReportViewSet,
)

router = DefaultRouter()
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'property-groups', PropertyGroupViewSet, basename='property-group')
router.register(r'executive-assignments', ExecutiveAssignmentViewSet, basename='executive-assignment')

shareholder_router = DefaultRouter()
shareholder_router.register(r'dividends', ShareholderDividendViewSet, basename='shareholder-dividend')
shareholder_router.register(r'reports', ShareholderReportViewSet, basename='shareholder-report')

urlpatterns = [
    path('', include(router.urls)),
    path('kpis/', CorporateKPIView.as_view(), name='corporate-kpis'),
    path('property-comparison/', PropertyComparisonView.as_view(), name='corporate-property-comparison'),
    path('revenue-mix/', RevenueMixView.as_view(), name='corporate-revenue-mix'),
]

# Executive endpoints mounted under /api/v1/executive/
executive_urlpatterns = [
    path('kpis/', CorporateKPIView.as_view(), name='executive-kpis'),
    path('property-comparison/', PropertyComparisonView.as_view(), name='executive-property-comparison'),
    path('revenue-mix/', RevenueMixView.as_view(), name='executive-revenue-mix'),
]

# Shareholder portal URLs are mounted separately under /api/v1/shareholder/
shareholder_urlpatterns = [
    path('', include(shareholder_router.urls)),
    path('profile/', ShareholderProfileView.as_view(), name='shareholder-profile'),
    path('financials/', ShareholderReportViewSet.as_view({'get': 'list'}), name='shareholder-financials'),
]
