from django.contrib import admin
from .models import Area, SavedArea


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'status', 'water_level_cm', 'is_active', 'updated_at']
    list_filter = ['status', 'district', 'is_active']
    search_fields = ['name', 'district']
    ordering = ['district', 'name']
    list_editable = ['status', 'water_level_cm']


@admin.register(SavedArea)
class SavedAreaAdmin(admin.ModelAdmin):
    list_display = ['user', 'area', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'area__name']
