from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.html import format_html, mark_safe
from django.contrib import messages
from django.utils import timezone
from .models import Area, SavedArea
from apps.weather.models import WeatherForecast
from apps.cctv.models import CCTVCamera, VideoSimulasi

class CCTVCameraInline(admin.TabularInline):
    model = CCTVCamera
    extra = 0
    fields = ('name', 'stream_url', 'thumbnail_url', 'is_active')

class VideoSimulasiInline(admin.TabularInline):
    model = VideoSimulasi
    extra = 0
    fields = ('title', 'video_file', 'is_active')

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'get_weather_status', 'get_cctv_status', 'status']
    list_filter = ['status', 'district', 'is_active']
    search_fields = ['name', 'district']
    ordering = ['district', 'name']
    actions = ['trigger_flood_alert']
    inlines = [CCTVCameraInline, VideoSimulasiInline]

    def get_weather_status(self, obj):
        # Cari prediksi cuaca ARIMA terbaru untuk area ini (atau general) yang hujan lebat
        forecast = WeatherForecast.objects.filter(area=obj, forecast_time__gte=timezone.now()).order_by('forecast_time').first()
        if not forecast:
            forecast = WeatherForecast.objects.filter(area__isnull=True, forecast_time__gte=timezone.now()).order_by('forecast_time').first()
            
        if forecast and forecast.rainfall and forecast.rainfall > 10.0:
            return format_html('<span style="color: red; font-weight: bold;">🌧️ HUJAN LEBAT ({} mm)</span>', forecast.rainfall)
        return mark_safe('<span style="color: green;">☀️ AMAN</span>')
    get_weather_status.short_description = "Syarat 1 (Cuaca)"

    def get_cctv_status(self, obj):
        # Cari apakah ada CCTV di area ini yang mendeteksi banjir
        cameras = CCTVCamera.objects.filter(area=obj, is_active=True)
        if not cameras.exists():
            return mark_safe('<span style="color: gray;">Tidak ada CCTV</span>')
            
        if cameras.filter(detection_result=CCTVCamera.DetectionResult.FLOOD).exists():
            return mark_safe('<span style="color: red; font-weight: bold;">🌊 BANJIR TERDETEKSI</span>')
        return mark_safe('<span style="color: green;">Aman</span>')
    get_cctv_status.short_description = "Syarat 2 (CCTV)"

    @admin.action(description="Kirim Peringatan Banjir Darurat (Manual Validator)")
    def trigger_flood_alert(self, request, queryset):
        # Jika user sudah menekan tombol "Confirm Send" di halaman intermediate
        if request.POST.get('post') == 'yes':
            # Kirim notifikasi ke user (Database & Firebase Push)
            from apps.notifications.models import Notification
            from django.contrib.auth import get_user_model
            from pyfcm import FCMNotification
            from django.conf import settings
            import logging
            
            logger = logging.getLogger(__name__)
            User = get_user_model()
            users = User.objects.all() # In real app, filter by SavedArea
            
            # Setup FCM Service (Firebase)
            push_service = None
            if settings.FCM_SERVER_KEY:
                push_service = FCMNotification(api_key=settings.FCM_SERVER_KEY)
            
            for area in queryset:
                for u in users:
                    # 1. Simpan ke Database
                    Notification.objects.create(
                        user=u,
                        title=f"AWAS BANJIR: {area.name}",
                        body=f"Peringatan Darurat Banjir untuk wilayah {area.name}. Harap waspada dan ikuti instruksi evakuasi.",
                        notif_type=Notification.NotifType.FLOOD_ALERT,
                        area=area
                    )
                    
                    # 2. Kirim "Pop-Up" (Push Notification) ke HP Frontend (Dart/Flutter)
                    if push_service and u.fcm_token:
                        try:
                            result = push_service.notify_single_device(
                                registration_id=u.fcm_token,
                                message_title=f"🚨 AWAS BANJIR: {area.name}",
                                message_body=f"Segera evakuasi dari wilayah {area.name}! Air terus naik.",
                                data_message={"area_id": area.id, "type": "flood_alert"}
                            )
                            logger.info(f"FCM Push to {u.email}: {result}")
                        except Exception as e:
                            logger.error(f"Gagal mengirim FCM ke {u.email}: {e}")
            
            self.message_user(request, f"Peringatan darurat & Push Notification berhasil dikirim untuk {queryset.count()} area.", level=messages.SUCCESS)
            return HttpResponseRedirect(request.get_full_path())
        
        # Evaluasi syarat untuk ditampilkan di halaman konfirmasi
        context = self.admin_site.each_context(request)
        
        areas_data = []
        for area in queryset:
            forecast = WeatherForecast.objects.filter(area=area, forecast_time__gte=timezone.now()).order_by('forecast_time').first()
            if not forecast:
                forecast = WeatherForecast.objects.filter(area__isnull=True, forecast_time__gte=timezone.now()).order_by('forecast_time').first()
            
            weather_met = forecast and forecast.rainfall and forecast.rainfall > 10.0
            cctv_met = CCTVCamera.objects.filter(area=area, is_active=True, detection_result=CCTVCamera.DetectionResult.FLOOD).exists()
            
            areas_data.append({
                'area': area,
                'weather_met': weather_met,
                'cctv_met': cctv_met,
                'ready': weather_met and cctv_met
            })
            
        context['areas_data'] = areas_data
        context['queryset'] = queryset
        
        return render(request, 'admin/areas/area/trigger_alert_confirmation.html', context)


@admin.register(SavedArea)
class SavedAreaAdmin(admin.ModelAdmin):
    list_display = ['user', 'area', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'area__name']
