from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, BuildingViewSet, FloorViewSet

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'buildings', BuildingViewSet, basename='building')
router.register(r'floors', FloorViewSet, basename='floor')

urlpatterns = [
    path('', include(router.urls)),
]
