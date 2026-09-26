from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoyaltyViewSet

router = DefaultRouter()
router.register(r'', LoyaltyViewSet, basename='loyalty')

urlpatterns = [
    path('', include(router.urls)),
]
