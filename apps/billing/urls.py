from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FolioViewSet, ChargeEventViewSet, GLExportView

router = DefaultRouter()
router.register(r'folios', FolioViewSet, basename='folio')
router.register(r'charge-events', ChargeEventViewSet, basename='charge-event')

folio_direct_router = DefaultRouter()
folio_direct_router.register(r'', FolioViewSet, basename='folio-direct')

urlpatterns = [
    path('gl-export/', GLExportView.as_view({'get': 'list'}), name='billing-gl-export'),
    path('', include(router.urls)),
]

folio_urlpatterns = [
    path('', include(folio_direct_router.urls)),
]
