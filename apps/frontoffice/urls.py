from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FrontOfficeViewSet, StayLogViewSet

router = DefaultRouter()
router.register(r'stays', StayLogViewSet, basename='stay-log')
router.register(r'', FrontOfficeViewSet, basename='front-office')

urlpatterns = [
    path('', include(router.urls)),
]
