from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # API Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # App APIs
    path('api/auth/', include('apps.users.urls')),
    path('api/areas/', include('apps.areas.urls')),
    path('api/weather/', include('apps.weather.urls')),
    path('api/cctv/', include('apps.cctv.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
]
