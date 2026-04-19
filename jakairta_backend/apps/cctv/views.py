from rest_framework import generics
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from .models import CCTVCamera
from .serializers import CCTVCameraSerializer


@extend_schema(tags=['CCTV'])
class CCTVListView(generics.ListAPIView):
    """Daftar semua kamera CCTV yang aktif"""
    serializer_class = CCTVCameraSerializer
    permission_classes = [AllowAny]
    queryset = CCTVCamera.objects.filter(is_active=True).select_related('area')


@extend_schema(tags=['CCTV'])
class CCTVDetailView(generics.RetrieveAPIView):
    """Detail dan status deteksi kamera CCTV"""
    serializer_class = CCTVCameraSerializer
    permission_classes = [AllowAny]
    queryset = CCTVCamera.objects.filter(is_active=True).select_related('area')
