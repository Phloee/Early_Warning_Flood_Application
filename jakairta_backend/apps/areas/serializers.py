from rest_framework import serializers
from .models import Area, SavedArea


class AreaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Area
        fields = [
            'id', 'name', 'district', 'sub_district',
            'latitude', 'longitude',
            'status', 'status_display',
            'water_level_cm', 'water_level_change',
            'status_genangan', 'area_tergenang', 'ai_confidence_level', 'last_ai_detected_at',
            'description', 'updated_at',
        ]


class AreaListSerializer(serializers.ModelSerializer):
    """Serializer ringkas untuk list view"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Area
        fields = ['id', 'name', 'district', 'status', 'status_display', 'water_level_cm', 'water_level_change', 'status_genangan', 'area_tergenang', 'ai_confidence_level', 'last_ai_detected_at', 'latitude', 'longitude', 'updated_at']


class SavedAreaSerializer(serializers.ModelSerializer):
    area = AreaListSerializer(read_only=True)
    area_id = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.all(), source='area', write_only=True
    )

    class Meta:
        model = SavedArea
        fields = ['id', 'area', 'area_id', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
