from django.db import models
from django.conf import settings


class FloodStatus(models.TextChoices):
    AMAN = 'aman', 'Aman'
    POTENSIAL = 'potensial', 'Potensial'
    BANJIR = 'banjir', 'Banjir'


class Area(models.Model):
    """Wilayah di Jakarta yang dipantau"""
    name = models.CharField(max_length=200, help_text='Nama lokasi (contoh: Kampung Melayu)')
    district = models.CharField(max_length=100, help_text='Kota/Kabupaten (contoh: Jakarta Timur)')
    sub_district = models.CharField(max_length=100, blank=True, help_text='Kecamatan')
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    status = models.CharField(
        max_length=20,
        choices=FloodStatus.choices,
        default=FloodStatus.AMAN,
    )
    water_level_cm = models.FloatField(default=0.0, help_text='Ketinggian air dalam cm')
    water_level_change = models.FloatField(default=0.0, help_text='Perubahan ketinggian air cm/jam')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'areas'
        verbose_name = 'Wilayah'
        verbose_name_plural = 'Wilayah'
        ordering = ['district', 'name']

    def __str__(self):
        return f'{self.name} – {self.district}'

    def classify_status(self):
        """Klasifikasi otomatis berdasarkan ketinggian air"""
        if self.water_level_cm > 150:
            return FloodStatus.BANJIR
        elif self.water_level_cm > 50:
            return FloodStatus.POTENSIAL
        return FloodStatus.AMAN


class SavedArea(models.Model):
    """Wilayah yang disimpan oleh pengguna"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_areas',
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='saved_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_areas'
        unique_together = ['user', 'area']
        verbose_name = 'Area Tersimpan'
        verbose_name_plural = 'Area Tersimpan'

    def __str__(self):
        return f'{self.user.email} → {self.area.name}'
