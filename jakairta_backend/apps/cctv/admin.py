from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count, Q
from .models import CCTVCamera, VideoSimulasi, FloodAnalysisLog


@admin.register(CCTVCamera)
class CCTVCameraAdmin(admin.ModelAdmin):
    list_display = ['name', 'area', 'detection_result', 'confidence_score', 'is_active', 'flood_prob_badge', 'last_detected_at']
    list_filter = ['detection_result', 'is_active', 'area']
    search_fields = ['name', 'area__name']
    list_editable = ['is_active']
    readonly_fields = ['last_detected_at', 'confidence_score', 'detection_result', 'flood_probability_info']

    fieldsets = (
        ('Informasi Kamera', {
            'fields': ('name', 'area', 'location_description', 'stream_url', 'thumbnail_url', 'is_active')
        }),
        ('Status Deteksi AI (Auto)', {
            'fields': ('detection_result', 'confidence_score', 'last_detected_at', 'flood_probability_info'),
            'description': 'Data ini diisi otomatis oleh sistem AI YOLOv8.'
        }),
    )

    def flood_prob_badge(self, obj):
        prob = FloodAnalysisLog.get_location_flood_probability(obj.area, hours=24)
        color = '#e74c3c' if prob >= 70 else '#f39c12' if prob >= 30 else '#27ae60'
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold;">'
            '{}% banjir (24j)</span>', color, prob
        )
    flood_prob_badge.short_description = 'Prob. Banjir'

    def flood_probability_info(self, obj):
        prob_6h = FloodAnalysisLog.get_location_flood_probability(obj.area, hours=6)
        prob_24h = FloodAnalysisLog.get_location_flood_probability(obj.area, hours=24)
        threshold = FloodAnalysisLog.get_adaptive_threshold(obj.area)
        return format_html(
            '<div style="font-size:13px;line-height:1.8">'
            '🕐 <b>6 jam terakhir:</b> {}% kemungkinan banjir<br>'
            '📅 <b>24 jam terakhir:</b> {}% kemungkinan banjir<br>'
            '🎯 <b>Threshold AI aktif:</b> {:.0f}% confidence (adaptive)<br>'
            '</div>',
            prob_6h, prob_24h, threshold * 100
        )
    flood_probability_info.short_description = 'Statistik AI (Adaptive Learning)'


@admin.register(VideoSimulasi)
class VideoSimulasiAdmin(admin.ModelAdmin):
    list_display = ['title', 'area', 'is_active', 'created_at']
    list_filter = ['is_active', 'area']
    search_fields = ['title', 'area__name']
    list_editable = ['is_active']


@admin.register(FloodAnalysisLog)
class FloodAnalysisLogAdmin(admin.ModelAdmin):
    list_display = [
        'analyzed_at', 'source_name', 'area', 'source_type',
        'status_badge', 'water_ratio_bar', 'rain_intensity',
        'confidence_score', 'total_objects_detected'
    ]
    list_filter = ['status_banjir', 'source_type', 'risk_level', 'is_flood', 'area', 'analyzed_at']
    search_fields = ['source_name', 'area__name', 'recommendation']
    readonly_fields = [
        'area', 'camera', 'source_type', 'source_name', 'status_banjir',
        'is_flood', 'has_water', 'water_area_ratio', 'water_level_text',
        'rain_intensity', 'risk_level', 'recommendation',
        'total_objects_detected', 'confidence_score', 'model_used',
        'frame_size', 'analyzed_at'
    ]
    date_hierarchy = 'analyzed_at'
    ordering = ['-analyzed_at']

    # Hanya Read (tidak ada add/delete dari admin untuk menjaga integritas log)
    def has_add_permission(self, request):
        return False

    fieldsets = (
        ('Sumber Analisis', {
            'fields': ('source_name', 'source_type', 'area', 'camera', 'analyzed_at')
        }),
        ('Hasil Deteksi AI', {
            'fields': ('status_banjir', 'is_flood', 'has_water', 'water_area_ratio', 'water_level_text')
        }),
        ('Analisis Cuaca & Risiko', {
            'fields': ('rain_intensity', 'risk_level', 'recommendation')
        }),
        ('Metadata Model AI', {
            'fields': ('model_used', 'frame_size', 'total_objects_detected', 'confidence_score'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'banjir': ('#e74c3c', '🌊 BANJIR'),
            'banjir_ringan': ('#e67e22', '⚠️ BANJIR RINGAN'),
            'hanya_genangan': ('#f39c12', '💧 GENANGAN'),
            'aman': ('#27ae60', '✅ AMAN'),
        }
        color, label = colors.get(obj.status_banjir, ('#95a5a6', obj.status_banjir))
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;'
            'font-size:11px;font-weight:bold;">{}</span>', color, label
        )
    status_badge.short_description = 'Status Banjir'
    status_badge.admin_order_field = 'status_banjir'

    def water_ratio_bar(self, obj):
        ratio = obj.water_area_ratio
        color = '#e74c3c' if ratio > 25 else '#f39c12' if ratio > 10 else '#27ae60'
        return format_html(
            '<div style="background:#eee;border-radius:4px;width:100px;height:12px;overflow:hidden;">'
            '<div style="background:{};width:{}%;height:100%;"></div></div>'
            '<small style="color:{};">{:.1f}%</small>',
            color, min(ratio, 100), color, ratio
        )
    water_ratio_bar.short_description = 'Area Genangan'

    def changelist_view(self, request, extra_context=None):
        """Tambahkan statistik ringkasan di atas daftar log."""
        extra_context = extra_context or {}
        qs = self.get_queryset(request)
        total = qs.count()
        floods = qs.filter(is_flood=True).count()
        avg_ratio = qs.aggregate(a=Avg('water_area_ratio'))['a'] or 0
        extra_context['summary_html'] = format_html(
            '<div style="background:#1a1a2e;color:white;padding:12px 16px;border-radius:8px;'
            'margin-bottom:12px;font-size:13px;display:flex;gap:24px;">'
            '<span>📊 <b>Total Log:</b> {}</span>'
            '<span>🌊 <b>Deteksi Banjir:</b> {} ({:.1f}%)</span>'
            '<span>💧 <b>Rata-rata Genangan:</b> {:.1f}%</span>'
            '</div>',
            total, floods, (floods / total * 100) if total else 0, avg_ratio
        )
        return super().changelist_view(request, extra_context=extra_context)
