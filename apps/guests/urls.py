from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GuestProfileViewSet

router = DefaultRouter()
router.register(r'', GuestProfileViewSet, basename='guest-profile')

urlpatterns = [
    path('', include(router.urls)),
]
