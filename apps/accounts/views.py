"""
Accounts views for authentication, token refresh, and user management.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from common.permissions import IsOrganizationAdmin
from .models import User
from .serializers import UserSerializer, CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'success': True,
            'user': serializer.data
        })


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsOrganizationAdmin]
    filterset_fields = ['role', 'is_active', 'organization']
    search_fields = ['email', 'username', 'first_name', 'last_name']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return User.objects.none()
        if user.is_superuser:
            return User.objects.all()
        if getattr(user, 'organization', None):
            return User.objects.filter(organization=user.organization)
        return User.objects.none()
