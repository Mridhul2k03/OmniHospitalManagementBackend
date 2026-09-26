from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DynamicPricingViewSet

router = DefaultRouter()
router.register(r'rules', DynamicPricingViewSet, basename='pricing-rules')
router.register(r'', DynamicPricingViewSet, basename='pricing')

urlpatterns = [
    path('', include(router.urls)),
]
