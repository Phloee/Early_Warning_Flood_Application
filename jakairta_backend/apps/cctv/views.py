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
        raw_detection_result = request.data.get('detection_result')
        confidence = request.data.get('confidence_score', 0.0)
        snapshot_url = request.data.get('snapshot_url')

        if not camera_id or not raw_detection_result:
            return Response({'error': 'camera_id dan detection_result harus diisi'}, status=status.HTTP_400_BAD_REQUEST)

        camera_status_map = {
            'flood': 'flood',
            'banjir': 'flood',
            'mulai_banjir': 'mulai_banjir',
            'banjir_ringan': 'mulai_banjir',
            'hanya_genangan': 'mulai_banjir',
            'no_flood': 'no_flood',
            'aman': 'no_flood',
            'uncertain': 'uncertain',
            'offline': 'offline',
        }
        log_status_map = {
            'flood': 'banjir',
            'banjir': 'banjir',
            'mulai_banjir': 'banjir_ringan',
            'banjir_ringan': 'banjir_ringan',
            'hanya_genangan': 'hanya_genangan',
            'no_flood': 'aman',
            'aman': 'aman',
            'uncertain': 'aman',
            'offline': 'aman',
        }
        normalized = str(raw_detection_result).lower().strip()
        detection_result = camera_status_map.get(normalized)
        status_banjir = log_status_map.get(normalized)
        if not detection_result or not status_banjir:
            return Response({'error': f'detection_result tidak valid: {raw_detection_result}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            camera = CCTVCamera.objects.get(pk=camera_id)
            camera.detection_result = detection_result
            camera.confidence_score = confidence
            if snapshot_url:
                camera.thumbnail_url = snapshot_url
            camera.last_detected_at = timezone.now()
            camera.save()

            # Create Analysis Log for dashboard and history
            is_flood = detection_result == 'flood'
            from .models import FloodAnalysisLog
            FloodAnalysisLog.objects.create(
                area=camera.area,
                camera=camera,
                source_type='cctv',
                source_name=camera.name,
                status_banjir=status_banjir,
                is_flood=is_flood,
                has_water=is_flood or detection_result == 'mulai_banjir',
                confidence_score=confidence * 100 if confidence <= 1.0 else confidence,
                water_level_text='Tinggi' if detection_result == 'flood' else ('Sedang' if detection_result == 'mulai_banjir' else 'Aman'),
                recommendation='Pantau terus kondisi.' if not is_flood else 'Waspada banjir!'
            )

            if camera.area:
                try:
                    from apps.dashboard.views import update_wilayah_status
                    confidence_pct = confidence * 100 if confidence <= 1.0 else confidence
                    confidence_level = 'high' if confidence_pct >= 75 else ('medium' if confidence_pct >= 45 else 'low')
                    update_wilayah_status(
                        camera.area,
                        flood_detected=detection_result in ['flood', 'mulai_banjir'],
                        confidence=confidence_level,
                        water_ratio=float(request.data.get('water_area_ratio') or (25 if detection_result == 'flood' else 5 if detection_result == 'mulai_banjir' else 0)),
                    )
                except Exception:
                    pass
            
            return Response({'status': 'success', 'message': f'Status Kamera {camera.name} diperbarui ke {detection_result}'})
        except CCTVCamera.DoesNotExist:
            return Response({'error': 'Kamera tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)
