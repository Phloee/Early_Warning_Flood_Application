from django.contrib import admin
from .models import CCTVCamera


@admin.register(CCTVCamera)
class CCTVCameraAdmin(admin.ModelAdmin):
    list_display = ['name', 'area', 'detection_result', 'confidence_score', 'is_active', 'last_detected_at']
    list_filter = ['detection_result', 'is_active']
    search_fields = ['name', 'area__name']
    list_editable = ['is_active']
