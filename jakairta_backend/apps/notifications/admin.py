from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['sent_at_display', 'notif_type_badge', 'title', 'area', 'user', 'is_read_badge']
    list_filter = ['notif_type', 'is_read', 'sent_at', 'area']
    search_fields = ['user__email', 'title', 'body']
    ordering = ['-sent_at']
    readonly_fields = ['user', 'title', 'body', 'notif_type', 'area', 'is_read', 'sent_at']

    # Tidak boleh tambah manual — hanya dari sistem AI
    def has_add_permission(self, request):
        return False

    def sent_at_display(self, obj):
        return obj.sent_at.strftime('%d/%m/%Y %H:%M') if obj.sent_at else '-'
    sent_at_display.short_description = 'Waktu'
    sent_at_display.admin_order_field = 'sent_at'

    def notif_type_badge(self, obj):
        colors = {
            'flood_alert':    ('#e74c3c', '🌊 BANJIR'),
            'weather_alert':  ('#f39c12', '🌧 CUACA'),
            'status_update':  ('#3478f6', '📡 STATUS'),
            'info':           ('#27ae60', 'ℹ️ INFO'),
        }
        color, label = colors.get(obj.notif_type, ('#95a5a6', obj.notif_type))
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;'
            'font-size:11px;font-weight:bold;">{}</span>', color, label
        )
    notif_type_badge.short_description = 'Tipe'

    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color:#27ae60;font-weight:700;">✓ Dibaca</span>')
        return format_html('<span style="color:#e74c3c;font-weight:700;">● Belum Dibaca</span>')
    is_read_badge.short_description = 'Status Baca'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from django.utils import timezone
        from datetime import timedelta
        qs = self.get_queryset(request)
        total = qs.count()
        unread = qs.filter(is_read=False).count()
        flood_alerts = qs.filter(notif_type='flood_alert').count()
        recent_flood = qs.filter(
            notif_type='flood_alert',
            sent_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        extra_context['summary_html'] = format_html(
            '<div style="background:#1a1a2e;color:white;padding:12px 16px;border-radius:8px;'
            'margin-bottom:12px;font-size:13px;display:flex;gap:24px;flex-wrap:wrap;">'
            '<span>📊 <b>Total Notif:</b> {}</span>'
            '<span style="color:#FCA5A5;">🔴 <b>Belum Dibaca:</b> {}</span>'
            '<span style="color:#FCD34D;">🌊 <b>Flood Alerts:</b> {}</span>'
            '<span style="color:#86EFAC;">⏰ <b>1 Jam Terakhir:</b> {} banjir</span>'
            '</div>',
            total, unread, flood_alerts, recent_flood
        )
        return super().changelist_view(request, extra_context=extra_context)

