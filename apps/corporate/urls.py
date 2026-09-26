from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegionViewSet, PropertyGroupViewSet, ExecutiveAssignmentViewSet,
    CorporateKPIView, PropertyComparisonView, RevenueMixView,
    OccupancyTrendView, ExportBoardPackView,
    ShareholderProfileView, ShareholderAssetsView,
    ShareholderDividendViewSet, ShareholderDividendVoucherView,
    ShareholderReportViewSet, ShareholderFinancialDownloadView,
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
    path('occupancy-trend/', OccupancyTrendView.as_view(), name='corporate-occupancy-trend'),
    path('revenue-mix/', RevenueMixView.as_view(), name='corporate-revenue-mix'),
    path('export-board-pack/', ExportBoardPackView.as_view(), name='corporate-export-board-pack'),
]

# Executive endpoints mounted under /api/v1/executive/
executive_urlpatterns = [
    path('kpis/', CorporateKPIView.as_view(), name='executive-kpis'),
    path('property-comparison/', PropertyComparisonView.as_view(), name='executive-property-comparison'),
    path('occupancy-trend/', OccupancyTrendView.as_view(), name='executive-occupancy-trend'),
    path('revenue-mix/', RevenueMixView.as_view(), name='executive-revenue-mix'),
    path('export-board-pack/', ExportBoardPackView.as_view(), name='executive-export-board-pack'),
]

# Shareholder portal URLs are mounted separately under /api/v1/shareholder/
shareholder_urlpatterns = [
    path('profile/', ShareholderProfileView.as_view(), name='shareholder-profile'),
    path('assets/', ShareholderAssetsView.as_view(), name='shareholder-assets'),
    path('dividends/<str:pk>/voucher-pdf/', ShareholderDividendVoucherView.as_view(), name='shareholder-dividend-voucher'),
    path('financials/', ShareholderReportViewSet.as_view({'get': 'list'}), name='shareholder-financials'),
    path('financials/<str:pk>/download/', ShareholderFinancialDownloadView.as_view(), name='shareholder-financial-download'),
    path('reports/<str:pk>/download/', ShareholderFinancialDownloadView.as_view(), name='shareholder-report-download'),
    path('', include(shareholder_router.urls)),
]
