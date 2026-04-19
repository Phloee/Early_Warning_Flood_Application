from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notif_type', 'is_read', 'sent_at']
    list_filter = ['notif_type', 'is_read', 'sent_at']
    search_fields = ['user__email', 'title']
    ordering = ['-sent_at']
