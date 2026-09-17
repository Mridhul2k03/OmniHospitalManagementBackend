from django.urls import path
from .views import AvailabilitySearchView

urlpatterns = [
    path('search/', AvailabilitySearchView.as_view(), name='availability-search'),
]
