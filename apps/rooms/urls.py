from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomAmenityViewSet,
    RoomTypeViewSet,
    RoomViewSet,
    RatePlanViewSet,
    RoomRateViewSet
)

router = DefaultRouter()
router.register(r'amenities', RoomAmenityViewSet, basename='room-amenity')
router.register(r'types', RoomTypeViewSet, basename='room-type')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'rate-plans', RatePlanViewSet, basename='rate-plan')
router.register(r'rates', RoomRateViewSet, basename='room-rate')

urlpatterns = [
    path('', include(router.urls)),
]
