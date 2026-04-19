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
