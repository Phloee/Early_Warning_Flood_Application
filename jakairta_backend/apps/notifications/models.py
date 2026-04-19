from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Riwayat notifikasi yang dikirim ke pengguna"""

    class NotifType(models.TextChoices):
        FLOOD_ALERT = 'flood_alert', 'Peringatan Banjir'
        WEATHER_ALERT = 'weather_alert', 'Peringatan Cuaca'
        STATUS_UPDATE = 'status_update', 'Update Status'
        INFO = 'info', 'Informasi'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    notif_type = models.CharField(
        max_length=30,
        choices=NotifType.choices,
        default=NotifType.INFO,
    )
    area = models.ForeignKey(
        'areas.Area',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications',
    )
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notifikasi'
        verbose_name_plural = 'Notifikasi'
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.user.email} – {self.title}'
