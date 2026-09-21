from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReservationViewSet
from .wizard_views import CheckInWizardView

router = DefaultRouter()
router.register(r'', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('wizard-submit/', CheckInWizardView.as_view(), name='checkin-wizard'),
    path('', include(router.urls)),
]
