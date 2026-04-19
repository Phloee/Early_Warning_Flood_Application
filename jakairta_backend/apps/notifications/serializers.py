from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    notif_type_display = serializers.CharField(source='get_notif_type_display', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True, default=None)

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'body', 'notif_type', 'notif_type_display',
            'area_name', 'is_read', 'sent_at',
        ]
        read_only_fields = ['id', 'title', 'body', 'notif_type', 'area_name', 'sent_at']


class FCMTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField(max_length=500)
