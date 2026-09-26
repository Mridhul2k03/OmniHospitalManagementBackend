from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    CurrentUserView,
    RegisterView,
    UserViewSet,
    LogoutView,
    SwitchTenantView,
    HealthCheckView,
    TenantViewSet,
    ChangePasswordView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'tenants', TenantViewSet, basename='tenant')

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegisterView.as_view(), name='register'),
    path('register-institution/', RegisterView.as_view(), name='register_institution'),
    path('logout/', LogoutView.as_view(), name='token_logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('switch-tenant/', SwitchTenantView.as_view(), name='switch_tenant'),
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('ready/', HealthCheckView.as_view(), name='readiness_check'),
    path('', include(router.urls)),
]
