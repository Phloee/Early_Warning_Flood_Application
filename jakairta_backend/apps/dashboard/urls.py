from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('login/', views.dashboard_login, name='dashboard_login'),
    path('logout/', views.dashboard_logout, name='dashboard_logout'),
    path('alert/<int:area_id>/', views.send_alert, name='dashboard_send_alert'),
    path('predict/', views.predict_flood, name='dashboard_predict'),
    path('analyze/<int:camera_id>/', views.analyze_camera, name='dashboard_analyze'),
    path('analyze_sim/<int:sim_id>/', views.analyze_sim, name='dashboard_analyze_sim'),
    path('stream_sim/<int:sim_id>/', views.stream_sim_video, name='dashboard_stream_sim'),
    path('latest_analysis/<int:area_id>/', views.get_latest_analysis, name='dashboard_latest_analysis'),
    path('broadcast_alert/', views.broadcast_alert, name='dashboard_broadcast_alert'),
    path('api/status/', views.api_status, name='dashboard_api_status'),
    path('api/area-status-stream/', views.area_status_stream, name='dashboard_area_status_stream'),
    path('api/notifications/', views.flood_notifications_api, name='dashboard_notifications_api'),
    path('api/notifications/read/', views.mark_notifications_read, name='dashboard_notifications_read'),

    # CRUD — Kamera CCTV
    
    # CRUD — Wilayah
    path('area/add/', views.area_add, name='dashboard_area_add'),
    path('area/<int:area_id>/edit/', views.area_edit, name='dashboard_area_edit'),
    path('area/<int:area_id>/delete/', views.area_delete, name='dashboard_area_delete'),
    path('camera/add/', views.camera_add, name='dashboard_camera_add'),
    path('camera/<int:camera_id>/edit/', views.camera_edit, name='dashboard_camera_edit'),
    path('camera/<int:camera_id>/delete/', views.camera_delete, name='dashboard_camera_delete'),

    # CRUD — Video Simulasi
    path('sim/add/', views.sim_add, name='dashboard_sim_add'),
    path('sim/<int:sim_id>/edit/', views.sim_edit, name='dashboard_sim_edit'),
    path('sim/<int:sim_id>/delete/', views.sim_delete, name='dashboard_sim_delete'),
]
