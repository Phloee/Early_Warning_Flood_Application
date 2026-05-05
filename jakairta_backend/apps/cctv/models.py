from django.db import models
from apps.areas.models import Area


class CCTVCamera(models.Model):
    """Kamera CCTV yang dipantau"""

    class DetectionResult(models.TextChoices):
        NO_FLOOD = 'no_flood', 'Tidak Banjir'
        FLOOD = 'flood', 'Banjir Terdeteksi'
        UNCERTAIN = 'uncertain', 'Tidak Pasti'
        OFFLINE = 'offline', 'Kamera Offline'

    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='cameras',
        null=True, blank=True,
    )
    name = models.CharField(max_length=200)
    location_description = models.CharField(max_length=255, blank=True)
    stream_url = models.URLField(blank=True, help_text='URL stream CCTV (RTSP/HTTP)')
    thumbnail_url = models.URLField(blank=True, help_text='URL thumbnail/snapshot kamera')
    is_active = models.BooleanField(default=True)

    # Hasil deteksi YOLOv8
    detection_result = models.CharField(
        max_length=20,
        choices=DetectionResult.choices,
        default=DetectionResult.OFFLINE,
    )
    confidence_score = models.FloatField(default=0.0, help_text='Confidence score YOLOv8 (0-1)')
    last_detected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cctv_cameras'
        verbose_name = 'Kamera CCTV'
        verbose_name_plural = 'Kamera CCTV'
        ordering = ['area__name', 'name']

    def __str__(self):
        area_name = self.area.name if self.area else 'Unknown'
        return f'{self.name} ({area_name})'


class VideoSimulasi(models.Model):
    """Video yang diupload untuk simulasi deteksi banjir"""
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='simulations',
        null=True, blank=True,
    )
    title = models.CharField(max_length=200, help_text='Judul video simulasi')
    video_file = models.FileField(upload_to='simulations/', help_text='Upload file video (.mp4)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'video_simulasi'
        verbose_name = 'Video Simulasi'
        verbose_name_plural = 'Video Simulasi'

    def __str__(self):
        return self.title


class FloodAnalysisLog(models.Model):
    """
    Log setiap hasil analisis AI YOLOv8.
    Database ini digunakan sebagai 'memori' sistem agar analisis
    berikutnya bisa mempertimbangkan riwayat deteksi di lokasi yang sama.
    """

    class SourceType(models.TextChoices):
        CCTV = 'cctv', 'CCTV Live'
        SIMULATION = 'simulation', 'Video Simulasi'

    class FloodStatus(models.TextChoices):
        BANJIR = 'banjir', 'BANJIR'
        BANJIR_RINGAN = 'banjir_ringan', 'BANJIR RINGAN'
        HANYA_GENANGAN = 'hanya_genangan', 'HANYA GENANGAN'
        AMAN = 'aman', 'AMAN (TIDAK BANJIR)'

    # Sumber analisis
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='analysis_logs')
    camera = models.ForeignKey(CCTVCamera, on_delete=models.SET_NULL, null=True, blank=True, related_name='analysis_logs')
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.CCTV)
    source_name = models.CharField(max_length=200, blank=True, help_text='Nama kamera / judul video')

    # Hasil analisis AI
    status_banjir = models.CharField(max_length=30, choices=FloodStatus.choices, default=FloodStatus.AMAN)
    is_flood = models.BooleanField(default=False)
    has_water = models.BooleanField(default=False)
    water_area_ratio = models.FloatField(default=0.0, help_text='Persentase area genangan (0-100%)')
    water_level_text = models.CharField(max_length=100, blank=True)
    rain_intensity = models.CharField(max_length=100, blank=True)
    risk_level = models.CharField(max_length=20, blank=True)  # safe, caution, warning, critical
    recommendation = models.TextField(blank=True)

    # Metadata model AI
    total_objects_detected = models.IntegerField(default=0)
    confidence_score = models.FloatField(default=0.0, help_text='Confidence score rata-rata (0-100)')
    model_used = models.CharField(max_length=100, default='best.pt')
    frame_size = models.CharField(max_length=30, blank=True)

    # Timestamp
    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'flood_analysis_logs'
        verbose_name = 'Log Analisis AI'
        verbose_name_plural = 'Log Analisis AI'
        ordering = ['-analyzed_at']

    def __str__(self):
        ts = self.analyzed_at.strftime('%d/%m/%Y %H:%M') if self.analyzed_at else '-'
        return f'[{self.get_status_banjir_display()}] {self.source_name} — {ts}'

    @classmethod
    def get_location_flood_probability(cls, area, hours=24):
        """
        Hitung probabilitas banjir di suatu area berdasarkan riwayat N jam terakhir.
        Digunakan untuk meningkatkan akurasi: jika riwayat sering banjir,
        threshold deteksi berikutnya diturunkan otomatis.
        """
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(hours=hours)
        logs = cls.objects.filter(area=area, analyzed_at__gte=cutoff)
        total = logs.count()
        if total == 0:
            return 0.0
        flood_count = logs.filter(is_flood=True).count()
        return round((flood_count / total) * 100, 1)

    @classmethod
    def get_adaptive_threshold(cls, area, base_threshold=0.50):
        """
        Turunkan threshold AI secara otomatis jika riwayat menunjukkan
        lokasi ini sering banjir (adaptive learning dari database).
        """
        prob = cls.get_location_flood_probability(area, hours=6)
        if prob >= 70:
            return max(0.25, base_threshold - 0.20)  # Lebih sensitif
        elif prob >= 40:
            return max(0.35, base_threshold - 0.10)  # Agak sensitif
        return base_threshold  # Normal
