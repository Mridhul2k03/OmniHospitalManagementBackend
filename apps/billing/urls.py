from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FolioViewSet, ChargeEventViewSet

router = DefaultRouter()
router.register(r'folios', FolioViewSet, basename='folio')
router.register(r'charge-events', ChargeEventViewSet, basename='charge-event')

urlpatterns = [
    path('', include(router.urls)),
]
