from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    UpdateProfileSerializer,
    CustomTokenObtainPairSerializer,
)

User = get_user_model()


@extend_schema(tags=['Auth'])
class RegisterView(generics.CreateAPIView):
    """Daftar akun baru"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = RefreshToken.for_user(user)
        return Response({
            'message': 'Akun berhasil dibuat',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(token),
                'access': str(token.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Auth'])
class LoginView(TokenObtainPairView):
    """Login dan dapatkan JWT token"""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


@extend_schema(tags=['Auth'])
class LogoutView(generics.GenericAPIView):
    """Logout dan blacklist refresh token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout berhasil'})
        except Exception:
            return Response({'error': 'Token tidak valid'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Auth'])
class ProfileView(generics.RetrieveUpdateAPIView):
    """Lihat dan update profil pengguna"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateProfileSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user
