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


from .models import VideoSimulasi
from rest_framework import serializers

class VideoSimulasiSerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source='area.name', read_only=True, default=None)

    class Meta:
        model = VideoSimulasi
        fields = ['id', 'title', 'area_name', 'video_file', 'created_at']

@extend_schema(tags=['CCTV'])
class VideoSimulasiListView(generics.ListAPIView):
    """Daftar video simulasi aktif"""
    serializer_class = VideoSimulasiSerializer
    permission_classes = [AllowAny]
    queryset = VideoSimulasi.objects.filter(is_active=True).select_related('area')


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

@extend_schema(tags=['CCTV Webhook'])
class Yolov8WebhookView(APIView):
    """Webhook untuk menerima hasil deteksi banjir dari script YOLOv8"""
    permission_classes = [AllowAny] # Idealnya pakai API Key khusus, tapi di-allow dulu untuk mempermudah.

    def post(self, request, *args, **kwargs):
        camera_id = request.data.get('camera_id')
        detection_result = request.data.get('detection_result')
        confidence = request.data.get('confidence_score', 0.0)
        snapshot_url = request.data.get('snapshot_url')

        if not camera_id or not detection_result:
            return Response({'error': 'camera_id dan detection_result harus diisi'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            camera = CCTVCamera.objects.get(pk=camera_id)
            camera.detection_result = detection_result
            camera.confidence_score = confidence
            if snapshot_url:
                camera.thumbnail_url = snapshot_url
            camera.last_detected_at = timezone.now()
            camera.save()
            
            return Response({'status': 'success', 'message': f'Status Kamera {camera.name} diperbarui ke {detection_result}'})
        except CCTVCamera.DoesNotExist:
            return Response({'error': 'Kamera tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)
