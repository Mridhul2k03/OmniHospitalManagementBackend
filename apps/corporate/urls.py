from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegionViewSet, PropertyGroupViewSet, ExecutiveAssignmentViewSet

router = DefaultRouter()
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'property-groups', PropertyGroupViewSet, basename='property-group')
router.register(r'executive-assignments', ExecutiveAssignmentViewSet, basename='executive-assignment')

urlpatterns = [
    path('', include(router.urls)),
]
