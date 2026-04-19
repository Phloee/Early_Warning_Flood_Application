from rest_framework import serializers
from .models import CCTVCamera


class CCTVCameraSerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source='area.name', read_only=True, default=None)
    detection_display = serializers.CharField(source='get_detection_result_display', read_only=True)

    class Meta:
        model = CCTVCamera
        fields = [
            'id', 'name', 'area_name', 'location_description',
            'thumbnail_url', 'is_active',
            'detection_result', 'detection_display',
            'confidence_score', 'last_detected_at',
        ]
